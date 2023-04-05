# save title and compare with title in cache
# Prevent duplication
# use sqlite3
import functools
import pathlib
import sqlite3
from typing import Callable


class Cache:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS cache (title text, url text, score int, accuracy int)')
        self.conn.commit()

    def set(self, title, url, score=0, accuracy=0):
        self.cursor.execute('INSERT INTO cache VALUES (?, ?, ?, ?)', (title, url, score, accuracy))
        self.conn.commit()

    def get(self, title):
        self.cursor.execute('SELECT url FROM cache WHERE title=?', (title,))
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()

    def __del__(self):
        self.conn.close()

    def record(self, func: Callable):
        """
        完成任务后记录到数据库
        :param func: Callable -> (score, accuracy)
        :return:
        """
        @functools.wraps(func)
        def wrapper(title, url, *args, **kwargs):
            r = func(title, url, *args, **kwargs)
            self.set(title, url, *r)
            return r
        return wrapper


current_dir = pathlib.Path(__file__).parent.parent.absolute()

db = Cache(current_dir / 'cache.db')

if __name__ == '__main__':
    db.set('test', 'test')
    print(db.get('test'))
