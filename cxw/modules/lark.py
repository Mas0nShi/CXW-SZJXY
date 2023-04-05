from requests import Session
import time
import hmac
import hashlib
import base64

from cxw.lib.config import LARK_SECRET, LARK_WEBHOOK


def _lark_sign():
    timestamp = str(int(time.time()))
    string_to_sign = '{}\n{}'.format(timestamp, LARK_SECRET)
    hmac_code = hmac.new(string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return sign, timestamp

class Lark:
    def __init__(self, webhook, secret):
        self.webhook = webhook
        self.secret = secret
        self.session = Session()

    def request(self, url, message):
        sign, timestamp = _lark_sign()
        message['timestamp'] = timestamp
        message['sign'] = sign

        resp = self.session.post(url, headers={
            'Content-Type': 'application/json',
        }, json=message)
        return resp.json()

    def send_message(self, msg):
        message = {
            "msg_type": "text",
            "content": {
                "text": msg
            }
        }
        j = self.request(self.webhook, message)
        if j['code'] != 0:
            raise Exception(j['msg'])

    # 富文本
    def send_rich_text(self, title, msgs: list = None):
        message = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": [
                            msgs
                        ]
                    }
                }
            }
        }
        j = self.request(self.webhook, message)
        if j['code'] != 0:
            raise Exception(j['msg'])

    @staticmethod
    def tag_a(text, href):
        return {
            "tag": "a",
            "text": text,
            "href": href
        }

    @staticmethod
    def tag_text(text):
        return {
            "tag": "text",
            "text": text
        }

    @staticmethod
    def tag_at(uid):
        return {
            "tag": "at",
            "user_id": uid
        }


bot = Lark(LARK_WEBHOOK, LARK_SECRET)

if __name__ == '__main__':
    # bot.send_message('test')
    bot.send_rich_text(title='时政进校园', msgs=[
        Lark.tag_text('这是一条测试消息！'),
        Lark.tag_a('这是一条链接', 'https://www.baidu.com'),
    ])
