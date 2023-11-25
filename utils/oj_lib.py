import subprocess
import json
import time
import asyncio
import datetime

from botpy import logging
from utils.interact import *

_log = logging.get_logger()
_path = "/home/floatingcean/fjnuacm_rank"


def classify_verdicts(content):
    verdict = ""
    if content == "accepted" or content == "accept":
        verdict = "ac"
    if content == "wronganswer" or content == "rejected" or content == "reject":
        verdict = "wa"
    elif content == "compileerror":
        verdict = "ce"
    elif content == "runtimeerror":
        verdict = "re"
    elif content == "timeexceeded" or content == "timelimitexceeded" or content == "timeexceed" or content == "timelimitexceed":
        verdict = "tle"
    elif content == "memoryexceeded" or content == "memorylimitexceeded" or content == "memoryexceed" or content == "memorylimitexceed":
        verdict = "mle"
    elif content == "ac":
        verdict = "ac"
    elif content == "wa":
        verdict = "wa"
    elif content == "ce":
        verdict = "ce"
    elif content == "re":
        verdict = "re"
    elif content == "tle" or content == "te":
        verdict = "tle"
    elif content == "mle" or content == "me":
        verdict = "mle"
    return verdict


def run_shell(shell):
    cmd = subprocess.Popen(shell, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                           universal_newlines=True, shell=True, bufsize=1)
    result = ""

    # 实时输出
    while True:
        line = cmd.stdout.readline().strip()
        result = result + line

        if line != "":
            _log.info(line)

        if subprocess.Popen.poll(cmd) == 0:  # 判断子进程是否结束
            break

    return result  # 返回结果不包含换行符


async def execute_lib_method(prop, me=None, message=None):
    for _t in range(1, 11):
        run = run_shell(
            f"sudo java -DproxyHost=127.0.0.1 -DproxyPort=7890 -Djava.net.useSystemProxies=true -jar "
            f"{_path}/lib/module_peeper_fjnuoj.jar {prop}")

        result_file = open(f"{_path}/lib/bug/out.txt")
        result = result_file.read()
        if result == "ok":
            return run

    if me != None and message != None:
        await reply(me, message, f"Query failed after 10 retries.")   
        error = result[:500] + "\n...\n" + result[-1500:] if len(result) > 2000 else result
        await reply(me, message, f"{error}")
    _log.info(result)
    return None


async def call_lib_method(me, message, prop):
    return await execute_lib_method(prop, me, message)


async def call_lib_method_directly(prop):
    return await execute_lib_method(prop)
    

def run_async_using_loop(loop, func):
    task = loop.create_task(func)
    loop.run_until_complete(task)
    run = task.result()
    loop.close()
    return run


def daily_update_job(loop):
    run_async_using_loop(loop, call_lib_method_directly("/update"))
    

def noon_report_job(loop, me):
    run_async_using_loop(loop, call_noon_report(me))


async def call_noon_report(me):
    today = datetime.datetime.now().strftime("%Y/%m/%d")
    oneday = datetime.timedelta(days=1)
    yesterday = (datetime.datetime.now() - oneday).strftime("%Y/%m/%d")
    
    # 调用jar
    run = await call_lib_method_directly(f"/full {_path}/out/img_full.png {_path}/out/text_full.txt")
    if run is None:
        await reply_directly(me, "633509366", "推送昨日卷王天梯榜失败")
    else:
        await reply_directly(me, "633509366", f"{yesterday} 卷王天梯榜", f"{_path}/out/img_full.png")

    # 调用jar
    run = await call_lib_method_directly(f"/now full {_path}/out/img_today.png {_path}/out/text_today.txt")
    if run is None:
        await reply_directly(me, "633509366", "推送今日题数失败")
    else:
        await reply_directly(me, "633509366", f"{today} 半天做题总榜", f"{_path}/out/img_today.png")


async def send_user_info_name(me, message, content):
    await reply(me, message, f"正在查询用户名为 {content} 的用户数据，请稍等")

    # 调用jar
    run = await call_lib_method(me, message, f"/user name {content} {_path}/out/text_user_name.txt")
    if run is None:
        return

    result = open(f"{_path}/out/text_user_name.txt").read()
    _log.info(result)
    if result != "mismatch":
        user = json.loads(result)
        await reply(me, message, f"[Fuzzy Match]\n最佳匹配：{user['name']}\nUID: {user['id']}")

        await send_user_info_uid(me, message, user['id'], True)
    else:
        await reply(me, message, f"[Fuzzy Mismatch]\n模糊匹配失败，相似度太低")


async def send_user_info_uid(me, message, content, is_started_query=False):
    if not is_started_query:
        await reply(me, message, f"正在查询 uid 为 {content} 的用户数据，请稍等")

    # 调用jar
    run = await call_lib_method(me, message, f"/user id {content} {_path}/out/text_user.txt")
    if run is None:
        return

    result = open(f"{_path}/out/text_user.txt").read()
    await reply(me, message, f"uid {content}\n\n{result}")


async def send_verdict_count(me, message, content, as_img):
    verdict = classify_verdicts(content.lower().replace(" ", ""))
    if verdict == "":
        await reply(me, message, f"请在 /评测榜单 后面添加正确的参数，如 ac, Accepted, TimeExceeded, "
                                         f"WrongAnswer")
        return

    await reply(me, message, f"正在查询今日 {verdict} 榜单，请稍等")

    # 调用jar
    run = await call_lib_method(me, message, f"/verdict {verdict} {_path}/out/img_verdict.png {_path}/out/text_verdict.txt")
    if run is None:
        return

    if as_img:
        await reply(me, message, f"今日 {verdict} 榜单", f"{_path}/out/img_verdict.png")
    else:
        result = open(f"{_path}/out/text_verdict.txt").read()
        await reply(me, message, f"今日 {verdict} 榜单\n\n{result}")


async def send_today_count(me, message, full, as_img):
    await reply(me, message, f"正在查询今日题数，请稍等")

    # 调用jar
    run = await call_lib_method(me, message, f"/now {full} {_path}/out/img_today.png {_path}/out/text_today.txt")
    if run is None:
        return

    if as_img:
        await reply(me, message, "今日题数", f"{_path}/out/img_today.png")
    else:
        result = open(f"{_path}/out/text_today.txt").read()
        await reply(me, message, f"今日题数\n\n{result}")


async def send_yesterday_count(me, message, as_img):
    await reply(me, message, f"正在查询总榜，请稍等")

    # 调用jar
    run = await call_lib_method(me, message, f"/full {_path}/out/img_full.png {_path}/out/text_full.txt")
    if run is None:
        return

    if as_img:
        await reply(me, message, "昨日卷王天梯榜", f"{_path}/out/img_full.png")
    else:
        result = open(f"{_path}/out/text_full.txt").read()
        await reply(me, message, f"昨日卷王天梯榜\n\n{result}")


async def send_version_info(me, message):
    # 调用jar
    run = await call_lib_method(me, message, 
                                f"/version {_path}/out/text_version.txt")
    if run is None:
        return

    result = open(f"{_path}/out/text_version.txt").read()
    await reply(me, message, f"{result}")


async def send_is_alive(me, message):
    # 调用jar
    run = await call_lib_method(me, message, 
                                f"/alive {_path}/out/text_alive.txt")
    if run is None:
        return

    result = open(f"{_path}/out/text_alive.txt").read()
    await reply(me, message, f"[UptimeRobot Api] {result}")


async def send_necessity_info(me, message):
    # 调用jar
    necessity = await call_lib_method(me, message, "/necessity")
    if necessity is None:
        return

    result = "不需要重新刷新每日榜单" if necessity.strip() == "useless" else "哦？需要重新刷新每日榜单"
    await reply(me, message, f"{result}")