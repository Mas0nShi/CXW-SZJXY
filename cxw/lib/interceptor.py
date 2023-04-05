import functools
import time
from hashlib import sha256
from requests import Session
from uuid import uuid4
from typing import Callable
from cxw.lib.config import USER_AGENT, SESSION_ID, SIGNATURE_SALT, PROTOCOL, HOST
from urllib.parse import urlunparse


class DailyInterceptor:

    #################
    @staticmethod
    def signature(uri, session_id, request_id, timestamp):
        ctx = sha256()
        msg = f'{uri}&&{session_id}&&{request_id}&&{timestamp}&&{SIGNATURE_SALT}'.encode('utf-8')
        ctx.update(msg)
        return ctx.hexdigest()

    @staticmethod
    def intercept(func: Callable):
        @functools.wraps(func)
        def wrapper(session: Session, uri: str, *args, **kwargs):
            session.headers['User-Agent'] = USER_AGENT
            session.headers['X-SESSION-ID'] = SESSION_ID
            session.headers['X-REQUEST-ID'] = str(uuid4())
            session.headers['X-TIMESTAMP'] = str(int(time.time() * 1000))
            session.headers['X-SIGNATURE'] = DailyInterceptor.signature(
                uri,
                session.headers['X-SESSION-ID'],
                session.headers['X-REQUEST-ID'],
                session.headers['X-TIMESTAMP']
            )
            return func(session, uri, *args, **kwargs)
        return wrapper


if __name__ == '__main__':

    @DailyInterceptor.intercept
    def test_request(session: Session, uri: str):
        uri = urlunparse((PROTOCOL, HOST, uri, '', '', ''))
        print(uri)
        print(session.headers)

    sess = Session()
    test_request(sess, '/api/v1/xxx')
