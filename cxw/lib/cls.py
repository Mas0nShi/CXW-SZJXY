import time
from enum import IntEnum


class UserStatus(IntEnum):
    NEED_CREDIT = 1
    ANSWERED = 2


class OptionType(IntEnum):
    RADIO = 1
    MULTI = 2
    INPUT = 3


class AnswerInfo:
    title: str
    url: str
    userstatus: int
    answer_id: int
    start_time: int
    end_time: int
    limit_num: int
    answertitle: str
    # after submit
    score: int = 0
    accuracy: int = 0

    # problem_num: int
    # problem_score: int

    def __init__(self, title, url, info):
        self.title = title
        self.url = url
        self.userstatus = info['userstatus']
        self.answer_id = info['answer_id']
        self.start_time = info['start_time']
        self.end_time = info['end_time']
        self.limit_num = info['limit_num']
        self.answertitle = info['answertitle']
        # self.problem_num = info['problem_num']
        # self.problem_score = info['problem_score']

    @property
    def is_valid(self):
        """
        1. 是否在答题有效时间内
        2. 是否已经答过题 或者 积分不足
        :return:
        """
        now = int(time.time())
        return self.start_time < now < self.end_time and self.userstatus not in [1, 2]


class QA:
    id: int
    title: str
    _options: list
    problems_type: int
    win_content: str
    win_id: str
    acc: int

    def __init__(self, itm):
        self.id = itm['id']
        self.title = itm['title']
        self._options = itm['option_content']
        self.problems_type = OptionType(itm['problems_type'])
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
        options = '\n'.join([f'{o["id"]}. {o["option_content"]}' for o in self._options])
        if self.win_id.count(',') == 0:
            return f'{self.title}\n{options}\n\n正确答案：{self.win_id}. {self.win_content}'
        #
        answers = zip([win_id.strip() for win_id in self.win_id.split(',')], self.win_content.split(','))
        return f'{self.title}\n{options}\n\n正确答案：{", ".join([f"{a[0]}. {a[1]}" for a in answers])}'

    @property
    def option(self):
        # match need python 3.10+
        if self.problems_type == OptionType.RADIO:
            return {'id': self.id, 'option': [self.win_id]}
        if self.problems_type == OptionType.MULTI:
            return {'id': self.id, 'option': [win_id.strip() for win_id in self.win_id.split(',')]}
        if self.problems_type == OptionType.INPUT:
            raise NotImplementedError('input type not supported')


if __name__ == '__main__':
    from pprint import pprint

    info = {
        "userstatus": 0,
        "answer_id": 1,
        "start_time": 1628332800,
        "end_time": 1628419199,
        "limit_num": 1,
        "answertitle": "时政进校园答题",
        "problem_num": 1,
        "problem_score": 1
    }
    itm = {
        "id": 1,
        "title": "问题1",
        "option_content": [
            {
                "id": "A",
                "option_content": "选项1"
            },
            {
                "id": "B",
                "option_content": "选项2"
            },
            {
                "id": "C",
                "option_content": "选项3"
            },
            {
                "id": "D",
                "option_content": "选项4"
            }
        ],
        "problems_type": 1,
        "win_content": "选项1",
        "win_id": "A",
        "acc": 1
    }
    ai = AnswerInfo('title', 'url', info)
    pprint(ai.__dict__)
    qa = QA(itm)
    pprint(qa.__dict__)
    print(qa.visual)
