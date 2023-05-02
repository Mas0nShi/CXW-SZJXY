import json
import re
import time
import random
import string
from urllib3 import encode_multipart_formdata
from cxw.lib.network import customRequest, delayRequest
from cxw.lib.network import Response
from urllib.parse import urlparse, urlunparse
from urllib.parse import parse_qs
from cxw.lib.config import ACCOUNT_ID, SESSION_ID, DEVICE_ID, USER_ID
from cxw.lib.cls import AnswerInfo, QA
from cxw.lib.cache import db
from cxw.modules.scan import scan_action_entry
from cxw.modules.location import get_channel_id
from bs4 import BeautifulSoup


def _init_task_list(channel_id):
    """
    获取文章列表
    :param channel_id: 频道id（地区id）
    :return: 文章列表
    """
    url = scan_action_entry(channel_id)
    assert url, 'Get page url failed'
    req: Response = customRequest.get(url)
    assert req.status_code == 200, 'Get channel list failed'
    j = req.text
    assert j, 'Get channel list failed'
    soup = BeautifulSoup(j, 'html.parser')
    #  <script id="__NEXT_DATA__" type="application/json">
    lists = soup.find_all('script', id="__NEXT_DATA__")
    assert len(lists) > 0, 'Get channel list failed'

    for item in lists:
        if item['type'] == 'application/json':
            j = json.loads(item.string)
            assert j, 'Get channel list failed'

            groups = j.get('props', {}).get('pageProps', {}).get('article', {}).get('subject_groups', {})
            assert len(groups) > 0, 'Get channel list failed'
            for group in groups:
                group_articles = group['group_articles']
                assert len(group_articles) > 0, 'Get channel list failed'
                for article in group_articles:
                    url = article['url']
                    list_title = article['list_title']
                    yield url, list_title


def _serialize_task_list(channel_id):
    """
    序列化文章列表
    :param channel_id: 频道id（地区id）
    :return: 序列化后的文章列表
    """
    task_list = _init_task_list(channel_id)
    ser_dicts = {}
    for url, list_title in task_list:
        ser_dicts[list_title] = url
    return ser_dicts


def _need_to_answer(content):
    """
    判断文章是否有答题板块
    :param content: 文章内容
    :return: bool
    """
    return '答题' in content and 'answer' in content


def _get_article_detail(url):
    """
    获取文章内容
    :param url: 文章链接
    :return: 文章内容
    """
    _id = re.match(r'.*\?id=(\d+)', url).group(1)
    req = delayRequest.get('/api/article/detail', params={
        'top_id': '',
        'id': _id,
        'from_channel': '',
        'refer_from': ''
    })
    assert req.status_code == 200, 'Get article detail failed'
    j = req.json()
    assert j['code'] == 0, 'Get article detail failed'
    content = j['data']['article']['content']
    assert content, 'Get article detail failed'
    return content


def _public_front_action(url):
    """
    TODO: 未知作用
    :param url:
    :return:
    """
    p = urlparse(url)
    assert p, 'Get url failed'
    req = customRequest.get(
        urlunparse((p.scheme, p.netloc, '/activity/api.php', '', '', '')),
        params={'m': 'public', 'subm': 'front'})
    assert req.status_code == 200, 'Get public info failed'
    j = req.json()
    assert j['code'] == 3001 and j['status'] == True, 'Get public info failed'


def valid(title: str, url: str) -> AnswerInfo:
    """
    判断是否在答题有效时间内
    :return: class AnswerInit
    """
    p = urlparse(url)
    assert p, 'Get url failed'
    q = parse_qs(urlparse(p.fragment).query)
    params = {
        'm': 'front', 'subm': 'answer', 'action': 'init',
        'q': q['q'][0],
        'account_id': ACCOUNT_ID, 'sessionid': SESSION_ID,
        'need_register': 2
    }
    req = customRequest.get(
        urlunparse((p.scheme, p.netloc, '/activity/api.php', '', '', '')), params=params)
    assert req.status_code == 200, 'Get answer info failed'
    j = req.json()
    assert j['code'] == 3001, 'Get answer info failed'

    return AnswerInfo(title, url, j['data'])


def get_task_lists() -> [AnswerInfo]:
    """
    获取有效的文章列表
    :return:
    """
    tasks = _serialize_task_list(get_channel_id())
    for title, url in tasks.items():
        if db.get(title):  # 尝试从缓存数据库中查询记录，如果存在直接跳过
            continue
        content = _get_article_detail(url)

        # 文章是否有答题板块, 如果没有直接记录到缓存数据库中
        if not _need_to_answer(content):
            db.set(title, url, expired=False)  # 没有答题板块
            continue
        # 是否在答题有效时间内且未答过题
        soup = BeautifulSoup(content, 'html.parser')
        a = soup.find('a', string=re.compile('答题'))
        assert a, 'Get answer url failed'
        url = a['href']
        ai = valid(title, url)
        if ai.is_valid:
            yield ai  # 有效的文章返回
        else:
            db.set(title, url,
                   expired=True, answertitle=ai.answertitle,
                   start=ai.start_time, end=ai.end_time,
                   userstatus=ai.userstatus, answer_id=ai.answer_id,
                   score=ai.score, accuracy=ai.accuracy
                   )  # 防止异常遗漏，记录到缓存数据库中


def _act_statistics(url):
    """
    TODO: 无实际作用，用于后台统计
    :param url:
    :return:
    """
    # https://fatzqg2w.act.tmuact.com/activity/api.php?m=public&subm=actstatistics&q=YunSLftQ2&account_id=63e315d451e9ec2780d8998e&session_id=642bc57daeb7b80001a0b63b&type=answer
    p = urlparse(url)
    assert p, 'Get url failed'
    q = parse_qs(urlparse(p.fragment).query)
    params = {
        'm': 'public', 'subm': 'actstatistics',
        'q': q['q'][0],
        'account_id': ACCOUNT_ID, 'session_id': SESSION_ID,
        'type': 'answer'
    }
    req = customRequest.get(
        urlunparse((p.scheme, p.netloc, '/activity/api.php', '', '', '')), params=params)
    assert req.status_code == 200, 'Get actstatistics failed'
    j = req.json()
    assert j['code'] == 3001, 'Get actstatistics failed'

def _ranking_list(url, answer_id):
    """
    TODO: 无实际用途
    :param url:
    :param answer_id:
    :return:
    """
    # https://fatzqg2w.act.tmuact.com/activity/api.php?m=front&subm=answer&action=rankinglist&page=1&answer_id=1995
    p = urlparse(url)
    assert p, 'Get url failed'
    req = customRequest.get(
        urlunparse((p.scheme, p.netloc, '/activity/api.php', '', '', '')), params={
            'm': 'front', 'subm': 'answer', 'action': 'rankinglist',
            'page': 1, 'answer_id': answer_id
        })
    assert req.status_code == 200, 'Get answers failed'
    j = req.json()
    assert j['code'] == 3001, 'Get answers failed'
    return j['data']['list']

def answer_info(ans: AnswerInfo):
    p = urlparse(ans.url)
    assert p, 'Get url failed'
    req = customRequest.get(
        urlunparse((p.scheme, p.netloc, '/activity/api.php', '', '', '')), params={
            'm': 'front', 'subm': 'answer', 'action': 'answerinfo',
            'answer_id': ans.answer_id, 'answer_start': 1
        })
    assert req.status_code == 200, 'Get answer info failed'
    j = req.json()
    assert j['code'] == 3001, 'Get answer info failed'
    qa_lists = j['data']['list']
    for qa in qa_lists:
        yield QA(qa)

def submit_answers(ans: AnswerInfo, qas: [QA]) -> (int, int):
    """
    提交答案
    :param ans: 答题信息
    :param qas: 答案列表
    :return: (正确数, 结果ID)
    """
    p = urlparse(ans.url)
    assert p, 'Get url failed'

    boundary = f'----WebKitFormBoundary{"".join(random.choices(string.ascii_letters + string.digits, k=16))}'

    data = encode_multipart_formdata({
        'option': json.dumps([{'id': q.id, 'option': [q.win_id]} for q in qas]),
        'zongshijian': random.randint(10, 30),
        'last': 1
    }, boundary=boundary)[0]

    req = customRequest.post(
        urlunparse((p.scheme, p.netloc, '/activity/api.php', '', '', '')), params={
            'm': 'front', 'subm': 'answer', 'action': 'answerdata2',
            'answer_id': ans.answer_id
        }, data=data, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    assert req.status_code == 200, 'Submit answers failed'
    j = req.json()
    assert j['code'] == 3001, 'Submit answers failed'
    return j['data']['right'], j['data']['id']

@db.record
def answer_result(ans: AnswerInfo, result_id) -> AnswerInfo:
    """
    获取答题结果
    :param ans: 信息
    :param result_id: 结果ID
    :return: (总分, 正确率)
    """
    p = urlparse(ans.url)
    assert p, 'Get url failed'
    req = customRequest.get(
        urlunparse((p.scheme, p.netloc, '/activity/api.php', '', '', '')), params={
            'm': 'front', 'subm': 'answer', 'action': 'answerresult',
            'answer_id': ans.answer_id, 'id': result_id
        })
    assert req.status_code == 200, 'Get answer result failed'
    j = req.json()
    assert j['code'] == 3001, 'Get answer result failed'
    ans.score = j['data']['zongfen']
    ans.accuracy = j['data']['accuracy']
    return ans


def checkdata() -> (int, int, int, int):
    """
    TODO: Experimental 试验性功能
    获取答题情况
    :return: (score, 总排名, 错误数, 正确数)
    """
    from hashlib import sha256
    timestamp = str(int(time.time() * 1000))
    signature = sha256(f"{DEVICE_ID}&&{timestamp}&&MJ<?TH4&9w^".encode()).hexdigest()
    req = customRequest.post('https://ser-html5.8531.cn/pro_personal/',
                             params={'m': 'api', 'subm': 'checksystem', 'action': 'getuserdata'},
                             data={
                                 'account_id': ACCOUNT_ID,
                                 'session_id': SESSION_ID,
                                 'device_id': DEVICE_ID,
                                 'timestamp': timestamp,
                                 'signature': signature,
                                 'user_id': USER_ID,
                                 'checkTimeId': '',
                                 'project_id': '155'
                             }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    assert req.status_code == 200, 'Get checkdata failed'
    j = req.json()
    assert j['code'] == '1000', 'Get checkdata failed'
    return j['data']['score'], j['data']['all_rank'], j['data']['error_num'], j['data']['right_num']


if __name__ == '__main__':
    score, all_rank, error_num, right_num = checkdata()
    print(f'当前积分: {score}, 总排名: {all_rank}, 错误数: {error_num}, 正确数: {right_num}')
    # items = get_task_lists()
    # item: AnswerInit = next(items)
    # print(item.url, item.answertitle, item.answer_id)
    # ai_lists = list(answer_info(item.url, item.answer_id))
    # for qa in ai_lists:
    #     print(qa.visual)
    #     print('-' * 20)
    #
    # right, res_id = submit_answers(item.url, item.answer_id, ai_lists)
    # print(right, res_id)
    # print(answer_result(item.answertitle, item.url, item.answer_id, res_id))
