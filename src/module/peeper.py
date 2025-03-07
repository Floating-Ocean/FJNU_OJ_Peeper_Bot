﻿import datetime
import difflib
from asyncio import AbstractEventLoop

from botpy import BotAPI

from src.core.command import command
from src.core.constants import Constants
from src.core.exception import ModuleRuntimeError
from src.core.output_cached import get_cached_prefix
from src.core.tools import run_shell, run_async, escape_mail_url, png2jpg, check_is_int
from src.module.atc import __atc_version__
from src.module.cf import __cf_version__
from src.module.color_rand import __color_rand_version__
from src.module.message import RobotMessage, report_exception
from src.module.nk import __nk_version__
from src.module.pick_one import __pick_one_version__
from src.module.rand import __rand_version__

_lib_path = Constants.config["lib_path"] + "\\Peeper-Board-Generator"


def register_module():
    pass


def classify_verdicts(content: str) -> str:
    alias_to_full = {
        "ac": ["accepted", "ac"],
        "wa": ["wrong answer", "rejected", "wa", "rj"],
        "tle": ["time exceeded", "time limit exceeded", "tle", "te"],
        "mle": ["memory exceeded", "memory limit exceeded", "mle", "me"],
        "ole": ["output exceeded", "output limit exceeded", "ole", "oe"],
        "hc": ["hacked", "hc"],
        "re": ["runtime error", "re"],
        "ce": ["compile error", "ce"],
        "se": ["system error", "se"],
        "fe": ["format error", "se"],
    }
    full_to_alias = {val: key for key, alters in alias_to_full.items() for val in alters}
    # 模糊匹配
    matches = difflib.get_close_matches(content.lower(), full_to_alias.keys())
    if len(matches) == 0:
        return ""

    return full_to_alias[matches[0]].upper()


async def execute_lib_method(prop: str, message: RobotMessage | None, no_id: bool) -> str | None:
    traceback = ""
    for _t in range(2):  # 尝试2次
        id_prop = "" if no_id else "--id hydro "
        result = run_shell(f"cd {_lib_path} & python main.py {id_prop}{prop}")
        traceback = open(f"{_lib_path}\\last_traceback.log", "r", encoding='utf-8').read()

        if traceback == "ok":
            return result

    if message is not None:
        await report_exception(message, 'Peeper-Board-Generator', traceback,
                               ModuleRuntimeError(traceback.split('\n')[-2]))

    return None


async def call_lib_method(message: RobotMessage, prop: str, no_id: bool = False) -> str | None:
    return await execute_lib_method(prop, message, no_id)


async def call_lib_method_directly(prop: str) -> str | None:
    return await execute_lib_method(prop, None, False)


def daily_update_job(loop: AbstractEventLoop):
    cached_prefix = get_cached_prefix('Peeper-Board-Generator')
    run_async(loop, call_lib_method_directly(f"--full --output {cached_prefix}.png"))


def noon_report_job(loop: AbstractEventLoop, api: BotAPI):
    run_async(loop, call_noon_report(api))


async def call_noon_report(api: BotAPI):
    today = datetime.datetime.now().strftime("%Y/%m/%d")
    oneday = datetime.timedelta(days=1)
    yesterday = (datetime.datetime.now() - oneday).strftime("%Y/%m/%d")

    cached_prefix = get_cached_prefix('Peeper-Board-Generator')
    run = await call_lib_method_directly(f"--full --output {cached_prefix}.png")
    if run is None:
        await api.post_message(channel_id=Constants.config['push_channel'], content="推送昨日卷王天梯榜失败")
    else:
        await api.post_message(channel_id=Constants.config['push_channel'], content=f"{yesterday} 卷王天梯榜",
                               file_image=png2jpg(f"{cached_prefix}.png"))

    cached_prefix = get_cached_prefix('Peeper-Board-Generator')
    run = await call_lib_method_directly(f"--now --output {cached_prefix}.png")
    if run is None:
        await api.post_message(channel_id=Constants.config['push_channel'], content="推送今日题数失败")
    else:
        await api.post_message(channel_id=Constants.config['push_channel'], content=f"{today} 半天做题总榜",
                               file_image=png2jpg(f"{cached_prefix}.png"))


async def send_user_info(message: RobotMessage, content: str, by_name: bool = False):
    type_name = "用户名" if by_name else " uid "
    type_id = "name" if by_name else "uid"
    await message.reply(f"正在查询{type_name}为 {content} 的用户数据，请稍等")

    cached_prefix = get_cached_prefix('Peeper-Board-Generator')
    run = await call_lib_method(message, f"--query_{type_id} {content} --output {cached_prefix}.txt")
    if run is None:
        return

    result = open(f"{cached_prefix}.txt", encoding="utf-8").read()
    result = escape_mail_url(result)
    await message.reply(f"[{type_id.capitalize()} {content}]\n\n{result}", modal_words=False)


@command(tokens=['评测榜单', 'verdict'], need_check_exclude=True)
async def send_now_board_with_verdict(message: RobotMessage):
    content = message.tokens[1] if len(message.tokens) == 2 else ""
    single_col = (message.tokens[2] == "single") if len(
        message.tokens) == 3 else False
    verdict = classify_verdicts(content)
    if verdict == "":
        await message.reply(f"请在 /评测榜单 后面添加正确的参数，如 ac, Accepted, TimeExceeded, WrongAnswer")
        return

    await message.reply(f"正在查询今日 {verdict} 榜单，请稍等")

    single_arg = "" if single_col else " --separate_cols"
    cached_prefix = get_cached_prefix('Peeper-Board-Generator')
    run = await call_lib_method(message,
                                f"--now {single_arg} --verdict {verdict} --output {cached_prefix}.png")
    if run is None:
        return

    await message.reply(f"今日 {verdict} 榜单", png2jpg(f"{cached_prefix}.png"))


@command(tokens=['今日题数', 'today'], need_check_exclude=True)
async def send_today_board(message: RobotMessage):
    single_col = (message.tokens[1] == "single") \
        if len(message.tokens) == 2 else False
    await message.reply(f"正在查询今日题数，请稍等")

    single_arg = "" if single_col else " --separate_cols"
    cached_prefix = get_cached_prefix('Peeper-Board-Generator')
    run = await call_lib_method(message, f"--now {single_arg} --output {cached_prefix}.png")
    if run is None:
        return

    await message.reply("今日题数", png2jpg(f"{cached_prefix}.png"))


@command(tokens=['昨日总榜', 'yesterday', 'full'], need_check_exclude=True)
async def send_yesterday_board(message: RobotMessage):
    single_col = (message.tokens[1] == "single") \
        if len(message.tokens) == 2 else False
    await message.reply(f"正在查询昨日总榜，请稍等")

    single_arg = "" if single_col else " --separate_cols"
    cached_prefix = get_cached_prefix('Peeper-Board-Generator')
    run = await call_lib_method(message, f"--full {single_arg} --output {cached_prefix}.png")
    if run is None:
        return

    await message.reply("昨日卷王天梯榜", png2jpg(f"{cached_prefix}.png"))


@command(tokens=['api'])
async def send_version_info(message: RobotMessage):
    await message.reply(f"正在查询各模块版本，请稍等")

    cached_prefix = get_cached_prefix('Peeper-Board-Generator')
    run = await call_lib_method(message, f"--version --output {cached_prefix}.txt", no_id=True)
    if run is None:
        return

    result = open(f"{cached_prefix}.txt", encoding="utf-8").read()
    await message.reply(f"[API Version]\n\n"
                        f"Core {Constants.core_version}\n"
                        f"AtCoder {__atc_version__}\n"
                        f"Codeforces {__cf_version__}\n"
                        f"Color-Rand {__color_rand_version__}"
                        f"NowCoder {__nk_version__}\n"
                        f"{result}\n"
                        f"Pick-One {__pick_one_version__}\n"
                        f"Random {__rand_version__}", modal_words=False)


@command(tokens=['user'], need_check_exclude=True)
async def oj_user(message: RobotMessage):
    content = message.tokens
    if len(content) < 3:
        return await message.reply("请输入三个参数，第三个参数前要加空格，比如说\"/user id 1\"，\"/user name Hydro\"")
    if len(content) > 3:
        return await message.reply("请输入三个参数，第三个参数不要加上空格")
    if content[1] == "id" and (len(content[2]) > 9 or not check_is_int(content[2])):
        return await message.reply("参数错误，id必须为整数")
    if content[1] == "id" or content[1] == "name":
        await send_user_info(message, content[2], by_name=(content[1] == "name"))
    else:
        await message.reply("请输入正确的参数，如\"/user id ...\", \"/user name ...\"")
