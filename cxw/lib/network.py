from urllib.parse import urlunparse
from requests import Session, Response
from cxw.lib.config import PROTOCOL, HOST, CUSTOM_USER_AGENT
from cxw.lib.interceptor import DailyInterceptor

class CustomRequest(Session):
    def __init__(self):
        super().__init__()
        self.headers['User-Agent'] = CUSTOM_USER_AGENT
        self.headers['X-Requested-With'] = 'cn.com.zjol'

class DailyRequest(Session):
    def __init__(self):
        super().__init__()

    @DailyInterceptor.intercept
    def get(self, uri: str, params=None, **kwargs) -> Response:
        return super().get(urlunparse((PROTOCOL, HOST, uri, '', '', '')), params=params, **kwargs)

    @DailyInterceptor.intercept
    def post(self, uri: str, data=None, json=None, **kwargs) -> Response:
        return super().post(urlunparse((PROTOCOL, HOST, uri, '', '', '')), data=data, json=json, **kwargs)


# export
delayRequest = DailyRequest()
customRequest = CustomRequest()

if __name__ == '__main__':
    sess = DailyRequest()
    print(sess.get('/api/area/list', params={'type': '1'}).json())
