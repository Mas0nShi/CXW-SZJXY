import time
import random
from cxw.modules.task import get_task_lists, answer_info, submit_answers, answer_result, AnswerInfo
from cxw.lib.config import LARK
from cxw.modules.lark import bot
import tqdm

def tasks():
    task_list = list(get_task_lists())
    print(f'共有{len(task_list)}个任务')

    if len(task_list) == 0:
        print('直接退出')
        return
    print('开始答题')
    print(f'{"标题":<30} {"答对数量":<10} {"准确率":<10}\n')

    for item in tqdm.tqdm(task_list):
        item: AnswerInfo

        ai_lists = list(answer_info(item))
        if len(ai_lists) == 0:
            continue
        if LARK:  # 飞书机器人
            msg = [bot.tag_text(item.title + '\n\n')]
            msg.extend([bot.tag_text(q.visual + '\n\n') for q in ai_lists])
            msg.append(bot.tag_a('点击查看', item.url))
            bot.send_rich_text('时政进校园 答题', msg)

        right, result_id = submit_answers(item, ai_lists)
        result = answer_result(item, result_id)
        print(f'{result.title:<30} {result.score:<10} {result.accuracy:<10}')
        # sleep 3-10s
        time.sleep(random.randint(3, 10))

    print('答题结束')


if __name__ == '__main__':
    tasks()
