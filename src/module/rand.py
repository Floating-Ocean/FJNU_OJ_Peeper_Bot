import random
import re
import traceback

from src.core.command import command
from src.core.constants import Constants
from src.core.tools import check_is_int, fetch_url_json, fetch_url_text
from src.module.atc import reply_atc_request
from src.module.cf import reply_cf_request
from src.module.color_rand import reply_color_rand
from src.module.message import report_exception, RobotMessage

__rand_version__ = "v2.1.2"


def register_module():
    pass


def get_rand_num(range_min: int, range_max: int) -> int:
    url = (f"https://www.random.org/integers/?num=1&"
           f"min={range_min}&max={range_max}&col=1&base=10&format=plain&rnd=new")
    data = fetch_url_text(url, throw=False, method='get')

    if isinstance(data, int):
        Constants.log.info(f"failed to get random number, code {data}.")
        return random.randint(range_min, range_max)

    return int(data)


def get_rand_seq(range_max: int) -> str:
    url = (f"https://www.random.org/integer-sets/?sets=1&"
           f"num={range_max}&min=1&max={range_max}&seqnos=off&commas=on&order=index&"
           f"format=plain&rnd=new")
    data = fetch_url_text(url, throw=False, method='get')

    if isinstance(data, int):
        Constants.log.info(f"failed to get random sequence, code {data}.")
        return ", ".join([str(x) for x in random.sample(range(1, range_max + 1), range_max)])

    return data


@command(tokens=["选择", "rand", "shuffle", "打乱"])
async def reply_rand_request(message: RobotMessage):
    try:
        content = message.tokens
        if len(content) < 2 and not content[0].startswith("/选择"):
            return await message.reply(f'[Random]\n\n{Constants.help_contents["random"]}', modal_words=False)

        if content[0] == "/shuffle" or content[0] == "/打乱":
            if len(content) != 2:
                await message.reply(f"请输入正确的指令格式，比如说\"/{content[0]} 这是一句话\"")
            content_len = len(content[1])
            rnd_perm = get_rand_seq(content_len).split(", ")
            rnd_content = "".join([content[1][int(x) - 1] for x in rnd_perm])
            return await message.reply(f"[Random Shuffle]\n\n{rnd_content}", modal_words=False)

        func = content[0][3::].strip() if len(content) == 1 else content[1]

        if content[0].startswith("/选择"):
            if len(func) == 0:
                return await message.reply("请指定要选择范围，用 \"还是\" 或逗号分隔")

            select_from = re.split("还是|,|，", func)
            select_len = len(select_from)
            selected_idx = get_rand_num(0, select_len - 1)
            await message.reply(f"我觉得第{selected_idx}个更好")

        elif func == "num" or func == "int":
            if (len(content) != 4 or
                    (not check_is_int(content[2])) or (not check_is_int(content[3]))):
                return await message.reply("请输入正确的指令格式，比如说\"/rand num 1 100\"")

            if max(len(content[2]), len(content[3])) <= 10:
                range_min, range_max = int(content[2]), int(content[3])
                if max(abs(range_min), abs(range_max)) <= 1_000_000_000:
                    if range_min > range_max:
                        range_min, range_max = range_max, range_min
                    result = get_rand_num(range_min, range_max)
                    split_str = "\n\n" if result >= 10_000 else " "
                    return await message.reply(f"[Rand Number]{split_str}{result}", modal_words=False)

            await message.reply("参数过大，请输入 [-1e9, 1e9] 内的整数")

        elif func == "seq":
            if len(content) != 3 or not check_is_int(content[2]):
                return await message.reply("请输入正确的指令格式，比如说\"/rand seq 10\"")

            if len(content[2]) <= 4:
                range_max = int(content[2])
                if 1 <= range_max <= 500:
                    result = get_rand_seq(range_max).replace("\n", "")
                    return await message.reply(f"[Rand Sequence]\n\n[{result}]", modal_words=False)

            await message.reply("参数错误，请输入 [1, 500] 内的数字")

        elif func == "word" or func == "hitokoto" or func == "sentence":
            await reply_hitokoto(message)

        elif func == "color":
            await reply_color_rand(message)

        elif func == "cf":
            await reply_cf_request(message)

        elif func == "atc":
            await reply_atc_request(message)

        else:
            await message.reply(f'[Random]\n\n{Constants.help_contents["random"]}', modal_words=False)

    except Exception as e:
        await report_exception(message, 'Random', traceback.format_exc(), repr(e))


@command(tokens=["hitokoto", "来句", "来一句", "来句话", "来一句话"])
async def reply_hitokoto(message: RobotMessage):
    json = fetch_url_json("https://v1.hitokoto.cn/")
    content = json['hitokoto']
    where = json['from']
    author = json['from_who'] if json['from_who'] else ""
    await message.reply(f"[Hitokoto]\n{content}\nBy {author}「{where}」", modal_words=False)
