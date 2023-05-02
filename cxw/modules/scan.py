from cxw.lib.network import delayRequest
from cxw.lib.network import Response


def scan_action_entry(channel_id, list_count=0):
    req: Response = delayRequest.get('/api/article/channel_list',
                                     params={'channel_id': channel_id, "list_count": list_count, "query_city_type": 0, "recommend_switch": 0})
    assert req.status_code == 200, 'Get channel list failed'
    j = req.json()
    assert j['code'] == 0, 'Get channel list failed'
    articles = j['data'].get('article_list', [])
    assert len(articles) > 0, 'Get channel list failed'
    for article in articles:
        if article['doc_title'] == '时政进校园':
            return article['url']
    # recursive
    return scan_action_entry(channel_id, list_count + len(articles))

if __name__ == '__main__':
    from cxw.modules.location import get_channel_id
    u = scan_action_entry(get_channel_id())
    print(u)
