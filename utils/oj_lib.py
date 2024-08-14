import datetime
import json
import os
import time
from asyncio import AbstractEventLoop

from botpy import logging, BotAPI
from botpy.ext.cog_yaml import read

from utils.cf import __cf_version__
from utils.interact import RobotMessage, __interact_version__
from utils.tools import run_shell, run_async, report_exception, escape_mail_url, _config
from utils.pick_one import __pick_one_version__

_lib_path = _config["lib_path"] + "\\Peeper-Board-Generator"
_output_path = _config["output_path"]
_log = logging.get_logger()


def classify_verdicts(content: str) -> str:
    match = {
        "ac": ["accepted", "accept", "ac"],
        "wa": ["wronganswer", "rejected", "reject", "wa", "rj"],
        "tle": ["timeexceeded", "timelimitexceeded", "timeexceed", "timelimitexceed", "tle", "te"],
        "mle": ["memoryexceeded", "memorylimitexceeded", "memoryexceed", "memorylimitexceed", "mle", "me"],
        "ole": ["outputexceeded", "outputlimitexceeded", "outputexceed", "outputlimitexceed", "ole", "oe"],
        "re": ["runtimeerror", "re"],
        "ce": ["compileerror", "ce"],
        "se": ["systemerror", "se"],
        "fe": ["formaterror", "se"],
    }

    for verdict, alias in match.items():
        if content in alias:
            return verdict.upper()

    return ""


async def execute_lib_method(prop: str, message: RobotMessage | None, no_id: bool) -> str | None:
    traceback = ""
    for _t in range(2):  # 尝试2次
        id_prop = "" if no_id else "--id hydro "
        result = run_shell(f"cd {_lib_path} & python main.py {id_prop}{prop}")
        traceback = open(f"{_lib_path}\\last_traceback.log", "r").read()

        if traceback == "ok":
            return result

    if message is not None:
        await report_exception(message, 'Peeper-Board-Generator', traceback)

    return None


async def call_lib_method(message: RobotMessage, prop: str, no_id: bool = False) -> str | None:
    return await execute_lib_method(prop, message, no_id)


async def call_lib_method_directly(prop: str) -> str | None:
    return await execute_lib_method(prop, None, False)


def daily_update_job(loop: AbstractEventLoop):
    run_async(loop, call_lib_method_directly(f"--full --output {_output_path}/full.png"))


def noon_report_job(loop: AbstractEventLoop, api: BotAPI):
    run_async(loop, call_noon_report(api))


async def call_noon_report(api: BotAPI):
    today = datetime.datetime.now().strftime("%Y/%m/%d")
    oneday = datetime.timedelta(days=1)
    yesterday = (datetime.datetime.now() - oneday).strftime("%Y/%m/%d")

    # 调用jar
    run = await call_lib_method_directly(f"--full --output {_output_path}/full.png")
    if run is None:
        await api.post_message(channel_id=_config['push_channel'], content="推送昨日卷王天梯榜失败")
    else:
        await api.post_message(channel_id=_config['push_channel'], content=f"{yesterday} 卷王天梯榜",
                               file_image=f"{_output_path}/full.png")

    # 调用jar
    run = await call_lib_method_directly(f"--now --output {_output_path}/now.png")
    if run is None:
        await api.post_message(channel_id=_config['push_channel'], content="推送今日题数失败")
    else:
        await api.post_message(channel_id=_config['push_channel'], content=f"{today} 半天做题总榜",
                               file_image=f"{_output_path}/now.png")


async def send_user_info_name(message: RobotMessage, content: str):
    await message.reply(f"正在查询用户名为 {content} 的用户数据，请稍等")

    # 调用jar
    run = await call_lib_method(message, f"--query_name {content} --output {_output_path}/user.txt")
    if run is None:
        return

    result = open(f"{_output_path}/user.txt", encoding="utf-8").read()
    result = escape_mail_url(result)
    await message.reply(f"[Name {content}]\n\n{result}")


async def send_user_info_uid(message: RobotMessage, content: str):
    await message.reply(f"正在查询 uid 为 {content} 的用户数据，请稍等")

    # 调用jar
    run = await call_lib_method(message, f"--query_uid {content} --output {_output_path}/user.txt")
    if run is None:
        return

    result = open(f"{_output_path}/user.txt", encoding="utf-8").read()
    result = escape_mail_url(result)
    await message.reply(f"[Uid {content}]\n\n{result}")


async def send_verdict_count(message: RobotMessage, content: str):
    verdict = classify_verdicts(content.lower().replace(" ", ""))
    if verdict == "":
        await message.reply(f"请在 /评测榜单 后面添加正确的参数，如 ac, Accepted, TimeExceeded, WrongAnswer")
        return

    await message.reply(f"正在查询今日 {verdict} 榜单，请稍等")

    # 调用jar
    run = await call_lib_method(message, f"--now --verdict {verdict} --output {_output_path}/verdict_{verdict}.png")
    if run is None:
        return

    await message.reply(f"今日 {verdict} 榜单", f"{_output_path}/verdict_{verdict}.png")


async def send_today_count(message: RobotMessage):
    await message.reply(f"正在查询今日题数，请稍等")

    # 调用jar
    run = await call_lib_method(message, f"--now --output {_output_path}/now.png")
    if run is None:
        return

    await message.reply("今日题数", f"{_output_path}/now.png")


async def send_yesterday_count(message: RobotMessage):
    await message.reply(f"正在查询总榜，请稍等")

    # 调用jar
    run = await call_lib_method(message, f"--full --output {_output_path}/full.png")
    if run is None:
        return

    await message.reply("昨日卷王天梯榜", f"{_output_path}/full.png")


async def send_version_info(message: RobotMessage):
    await message.reply(f"正在查询各模块版本，请稍等")
    # 调用jar
    run = await call_lib_method(message, f"--version --output {_output_path}/version.txt", no_id=True)
    if run is None:
        return

    result = open(f"{_output_path}/version.txt", encoding="utf-8").read()
    await message.reply(f"[API Version]\n\n"
                        f"Robot-Interact {__interact_version__}\n"
                        f"{result}\n"
                        f"Pick-One {__pick_one_version__}\n"
                        f"Codeforces {__cf_version__}")
