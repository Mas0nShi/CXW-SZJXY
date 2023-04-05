from cxw.lib.network import delayRequest
from cxw.lib.config import LOCATION
from requests import Response


def get_channel_id():
    resp: Response = delayRequest.get('/api/area/list', params={'type': '1'})
    assert resp.status_code == 200, 'Get channel id failed'
    j = resp.json()
    assert j['code'] == 0, 'Get channel id failed'
    areas = j['data'].get('areas', [])
    assert len(areas) > 0, 'Get channel id failed'
    for province in areas:
        for city in province['children']:
            if city['name'] == LOCATION:
                return city.get('nav_parameter', None)


if __name__ == '__main__':
    channel = get_channel_id()
    print(channel)

