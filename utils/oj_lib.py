import datetime
import json
import os
from asyncio import AbstractEventLoop

from botpy import logging, BotAPI
from botpy.ext.cog_yaml import read

from utils.interact import RobotMessage
from utils.tools import run_shell, run_async, report_exception

_config = read(os.path.join(os.path.join(os.path.dirname(__file__), ".."), "config.yaml"))
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

    return content.upper()


async def execute_lib_method(prop: str, message: RobotMessage | None) -> str | None:
    traceback = ""
    for _t in range(3):  # 尝试3次，
        result = run_shell(f"python {_lib_path}\\main.py {prop}")
        traceback = open(f"{_lib_path}\\last_traceback.log", "r").read()

        if traceback == "ok":
            return result

    if message is not None:
        await report_exception(message, 'Peeper-Board-Generator', traceback)

    return None


async def call_lib_method(message: RobotMessage, prop: str) -> str | None:
    return await execute_lib_method(prop, message)


async def call_lib_method_directly(prop: str) -> str | None:
    return await execute_lib_method(prop, None)


def daily_update_job(loop: AbstractEventLoop):
    run_async(loop, call_lib_method_directly(f"--full --output {_output_path}/full.png"))


def noon_report_job(loop: AbstractEventLoop, api: BotAPI):
    run_async(call_noon_report(loop, api))


async def call_noon_report(api: BotAPI):
    today = datetime.datetime.now().strftime("%Y/%m/%d")
    oneday = datetime.timedelta(days=1)
    yesterday = (datetime.datetime.now() - oneday).strftime("%Y/%m/%d")

    # 调用jar
    run = await call_lib_method_directly(f"--full --output {_output_path}/full.png")
    if run is None:
        await api.post_message(channel_id="633509366", content="推送昨日卷王天梯榜失败")
    else:
        await api.post_message(channel_id="633509366", content=f"{yesterday} 卷王天梯榜", file_image=f"{_output_path}/full.png")

    # 调用jar
    run = await call_lib_method_directly(f"--now --output {_output_path}/now.png")
    if run is None:
        await api.post_message(channel_id="633509366", content="推送今日题数失败")
    else:
        await api.post_message(channel_id="633509366", content=f"{today} 半天做题总榜", file_image=f"{_output_path}/now.png")


# todo: 等待api添加功能
async def send_user_info_name(message: RobotMessage, content: str):
    await message.reply(f"正在查询用户名为 {content} 的用户数据，请稍等")

    # 调用jar
    run = await call_lib_method(message, f"--user name {content} --output {_output_path}/user_name.txt")
    if run is None:
        return

    result = open(f"{_output_path}/text_user_name.txt").read()
    _log.info(result)
    if result != "mismatch":
        user = json.loads(result)
        await message.reply(f"[Fuzzy Match]\n最佳匹配：{user['name']}\nUID: {user['id']}")

        await send_user_info_uid(message, user['id'], True)
    else:
        await message.reply(f"[Fuzzy Mismatch]\n模糊匹配失败，相似度太低")


async def send_user_info_uid(message: RobotMessage, content: str, is_started_query: bool = False):
    if not is_started_query:
        await message.reply(f"正在查询 uid 为 {content} 的用户数据，请稍等")

    # 调用jar
    run = await call_lib_method(message, f"--user id {content} --output {_output_path}/user.txt")
    if run is None:
        return

    result = open(f"{_output_path}/text_user.txt").read()
    await message.reply(f"uid {content}\n\n{result}")


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
    # 调用jar
    run = await call_lib_method(message, f"--version --output {_output_path}/version.txt")
    if run is None:
        return

    result = open(f"{_output_path}/version.txt").read()
    await message.reply(f"{result}")
