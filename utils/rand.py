import random
import re
import traceback

import requests

from robot import command
from utils.interact import RobotMessage
from utils.tools import _log, check_is_int, report_exception

__rand_version__ = "v1.0.1"

__rand_help_content__ = """/rand [num/int] [min] [max]: 在 [min, max] 中选择一个随机数，值域 [-1e9, 1e9].
/rand seq [max]: 获取一个 1, 2, ..., max 的随机排列，值域 [1, 500]."""


def get_rand_num(range_min: int, range_max: int) -> int:
    url = (f"https://www.random.org/integers/?num=1&"
           f"min={range_min}&max={range_max}&col=1&base=10&format=plain&rnd=new")
    response = requests.get(url)

    if response.status_code != 200:
        _log.info(f"failed to get random number, code {response.status_code}.")
        return random.randint(range_min, range_max)

    data = response.text
    return int(data)


def get_rand_seq(range_max: int) -> str:
    url = (f"https://www.random.org/integer-sets/?sets=1&"
           f"num={range_max}&min=1&max={range_max}&seqnos=off&commas=on&order=index&"
           f"format=plain&rnd=new")
    response = requests.get(url)

    if response.status_code != 200:
        _log.info(f"failed to get random sequence, code {response.status_code}.")
        return ", ".join([str(x) for x in random.sample(range(1, range_max + 1), range_max)])

    data = response.text
    return data


@command(aliases=["选择", "rand", "shuffle", "打乱"])
async def reply_rand_request(message: RobotMessage):
    try:
        content = re.sub(r'<@!\d+>', '', message.content).strip().split()
        if len(content) < 2 and not content[0].startswith("/选择"):
            await message.reply(f"[Random]\n\n{__rand_help_content__}", modal_words=False)
            return

        if content[0] == "/shuffle" or content[0] == "/打乱":
            if len(content) != 2:
                await message.reply(f"请输入正确的指令格式，比如说\"/{content[0]} 这是一句话\"")
            content_len = len(content[1])
            rnd_perm = get_rand_seq(content_len).split(", ")
            rnd_content = "".join([content[1][int(x) - 1] for x in rnd_perm])
            await message.reply(f"[Random Shuffle]\n\n{rnd_content}", modal_words=False)
            return

        func = content[0][3::].strip() if len(content) == 1 else content[1]

        if content[0].startswith("/选择"):
            if len(func) == 0:
                await message.reply("请指定要选择范围，用 \"还是\" 或逗号分隔")
                return
            select_from = re.split("还是|,|，", func)
            select_len = len(select_from)
            selected_idx = get_rand_num(0, select_len - 1)
            await message.reply(f"我觉得 \"{select_from[selected_idx]}\" 更好")

        elif func == "num" or func == "int":
            if (len(content) != 4 or
                    (not check_is_int(content[2])) or (not check_is_int(content[3]))):
                await message.reply("请输入正确的指令格式，比如说\"/rand num 1 100\"")
                return

            if max(len(content[2]), len(content[3])) <= 10:
                range_min, range_max = int(content[2]), int(content[3])
                if max(abs(range_min), abs(range_max)) <= 1_000_000_000:
                    if range_min > range_max:
                        range_min, range_max = range_max, range_min
                    result = get_rand_num(range_min, range_max)
                    split_str = "\n\n" if result >= 10_000 else " "
                    await message.reply(f"[Rand Number]{split_str}{result}", modal_words=False)
                    return

            await message.reply("参数过大，请输入 [-1e9, 1e9] 内的数字")

        elif func == "seq":
            if len(content) != 3 or not check_is_int(content[2]):
                await message.reply("请输入正确的指令格式，比如说\"/rand seq 10\"")
                return

            if len(content[2]) <= 4:
                range_max = int(content[2])
                if 1 <= range_max <= 500:
                    result = get_rand_seq(range_max).replace("\n", "")
                    await message.reply(f"[Rand Sequence]\n\n[{result}]", modal_words=False)
                    return

            await message.reply("参数错误，请输入 [1, 500] 内的数字")

        else:
            await message.reply(f"[Random]\n\n{__rand_help_content__}", modal_words=False)

    except Exception as e:
        await report_exception(message, 'Random', traceback.format_exc(), repr(e))
