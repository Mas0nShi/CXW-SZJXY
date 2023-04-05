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
from cxw.lib.config import ACCOUNT_ID, SESSION_ID
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
            groups = j['props']['pageProps']['article']['subject_groups']
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
    # ?top_id=&id=1500227&from_channel=&refer_from=
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


# 是否在答题有效时间内
def vaild(url) -> (bool, int):
    """
    判断是否在答题有效时间内
    :return: (bool, answer_id)
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
    answer_id = j['data']['answer_id']
    start_time = j['data']['start_time']
    end_time = j['data']['end_time']
    userstatus = j['data']['userstatus']  # 1 = 积分答题积分不足, 2 = 已答过题
    limit_num = j['data']['limit_num']
    now = int(time.time())

    return (start_time < now < end_time) and userstatus not in [1, 2], answer_id


def get_task_lists() -> (str, str, int):
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
            db.set(title, url)
            continue
        # 是否在答题有效时间内且未答过题
        soup = BeautifulSoup(content, 'html.parser')
        a = soup.find('a', string=re.compile('答题'))
        assert a, 'Get answer url failed'
        url = a['href']
        vad, answer_id = vaild(url)
        if vad:
            yield title, url, answer_id  # 有效的文章返回
        else:
            db.set(title, url)  # 防止异常遗漏，记录到缓存数据库中


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

def answer_info(url, answer_id):
    p = urlparse(url)
    assert p, 'Get url failed'
    req = customRequest.get(
        urlunparse((p.scheme, p.netloc, '/activity/api.php', '', '', '')), params={
            'm': 'front', 'subm': 'answer', 'action': 'answerinfo',
            'answer_id': answer_id, 'answer_start': 1
        })
    assert req.status_code == 200, 'Get answer info failed'
    j = req.json()
    assert j['code'] == 3001, 'Get answer info failed'
    qa_lists = j['data']['list']
    for qa in qa_lists:
        yield QA(qa)


class QA:
    id: int
    title: str
    options: list
    problems_type: int
    win_content: str
    win_id: int
    acc: int

    def __init__(self, itm):
        self.id = itm['id']
        self.title = itm['title']
        self.options = itm['option_content']
        self.problems_type = itm['problems_type']
        self.win_content = itm['win_content']
        self.win_id = itm['win_id']
        self.acc = itm['acc']

    @property
    def visual(self):
        """
        preview:
            {question}
                A. {option}
                B. {option}
                C. {option}
                D. {option}
            正确答案：{win_id}. {win_content}
        :return: str
        """
        options = '\n'.join([f'{o["id"]}. {o["option_content"]}' for o in self.options])
        return f'{self.title}\n{options}\n正确答案：{self.win_id}. {self.win_content}'


def submit_answers(url, answer_id, qas: [QA]) -> (int, int):
    """
    提交答案
    :param url: 活动地址
    :param answer_id: 答题ID
    :param qas: 答案列表
    :return: (正确数, 结果ID)
    """
    p = urlparse(url)
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
            'answer_id': answer_id
        }, data=data, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    assert req.status_code == 200, 'Submit answers failed'
    j = req.json()
    assert j['code'] == 3001, 'Submit answers failed'
    return j['data']['right'], j['data']['id']

@db.record
def answer_result(title, url, answer_id, result_id) -> (int, int):
    """
    获取答题结果
    :param title: 活动标题
    :param url: 活动地址
    :param answer_id: 答题ID
    :param result_id: 结果ID
    :return: (总分, 正确率)
    """
    p = urlparse(url)
    assert p, 'Get url failed'
    req = customRequest.get(
        urlunparse((p.scheme, p.netloc, '/activity/api.php', '', '', '')), params={
            'm': 'front', 'subm': 'answer', 'action': 'answerresult',
            'answer_id': answer_id, 'id': result_id
        })
    assert req.status_code == 200, 'Get answer result failed'
    j = req.json()
    assert j['code'] == 3001, 'Get answer result failed'
    return j['data']['zongfen'], j['data']['accuracy']


if __name__ == '__main__':
    items = get_task_lists()
    t, u, a = next(items)
    print(u, t, a)
    ai_lists = list(answer_info(u, a))
    for qa in ai_lists:
        print(qa.visual)
        print('-' * 20)

    right, res_id = submit_answers(u, a, ai_lists)
    print(right, res_id)
    print(answer_result(t, u, a, res_id))

