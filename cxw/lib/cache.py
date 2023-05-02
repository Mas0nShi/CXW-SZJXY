# save title and compare with title in cache
# Prevent duplication
# use sqlite3
import functools
import pathlib
import sqlite3
import time
from typing import Callable
from cxw.lib.cls import AnswerInfo


class Cache:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS cache (title text, url text, answertitle text, expired bool, start datetime, end datetime, userstatus int, answer_id int, score int, accuracy int)')
        self.conn.commit()

    def set(self, title: str, url: str,  # 标题和链接
            answertitle: str = '',  # 答案
            expired: bool = False,  # 是否过期
            start: int = 0,  # 开始时间 10位时间戳
            end: int = 0,  # 结束时间 10位时间戳
            userstatus: int = 0,  # 用户状态
            answer_id: int = 0,  # 答题id
            score: int = 0,  # 得分
            accuracy: int = 0  # 准确率
            ):
        # 时间戳 to datetime
        start = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))
        end = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end))
        # title text, url text, answertitle text, expired bool, start datetime, end datetime, userstatus int, answer_id int, score int, accuracy int
        self.cursor.execute('INSERT INTO cache VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                            (title, url, answertitle, expired, start, end, userstatus, answer_id, score, accuracy))
        self.conn.commit()

    def get(self, title):
        """
        get url by title
        :param title: str
        :return: str
        """
        self.cursor.execute('SELECT url FROM cache WHERE title=?', (title,))
        return self.cursor.fetchone()

    def close(self):
        """
        close connection
        :return:
        """
        self.conn.close()

    def __del__(self):
        self.conn.close()

    def record(self, func: Callable):
        """
        完成任务后记录到数据库
        :param func: Callable -> AnswerInit
        :return:
        """

        @functools.wraps(func)
        def wrapper(title, url, *args, **kwargs):
            ai: AnswerInfo = func(title, url, *args, **kwargs)
            self.set(ai.title, ai.url,
                     expired=True, answertitle=ai.answertitle,
                     start=ai.start_time, end=ai.end_time,
                     userstatus=ai.userstatus, answer_id=ai.answer_id,
                     score=ai.score, accuracy=ai.accuracy
                     )
            return ai

        return wrapper


current_dir = pathlib.Path(__file__).parent.parent.absolute()

db = Cache(current_dir / 'cache.db')

if __name__ == '__main__':
    db.set('test', 'test')
    print(db.get('test'))
