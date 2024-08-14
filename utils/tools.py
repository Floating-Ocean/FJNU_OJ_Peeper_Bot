import os
import re
import subprocess
import time
from asyncio import AbstractEventLoop
from typing import Any

import requests
from botpy import logging
from botpy.ext.cog_yaml import read

from utils.interact import RobotMessage

_log = logging.get_logger()
_config = read(os.path.join(os.path.join(os.path.dirname(__file__), ".."), "config.yaml"))


def run_shell(shell: str) -> str:
    _log.info(shell)
    cmd = subprocess.Popen(shell, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                           universal_newlines=True, shell=True, bufsize=1)
    info = ""
    # 实时输出
    while True:
        line = cmd.stderr.readline().strip()
        info = info + line

        _log.info(line)

        if line == "" or subprocess.Popen.poll(cmd) == 0:  # 判断子进程是否结束
            break

    return info


def run_async(loop: AbstractEventLoop, func: any):
    task = loop.create_task(func)
    loop.run_until_complete(task)
    loop.close()
    return task.result()


async def report_exception(message: RobotMessage, name: str, trace: str):
    _log.error(trace)
    trace = re.sub(r'[A-Za-z]:\\Users\\[^\\]+', r'%userProfile%', trace)
    trace = trace.replace(".", " . ")
    if len(trace) > 2000:
        trace = trace[:500] + "\n...\n" + trace[-1500:]
    await message.reply(f"[Operation failed] in module {name}.\n\n{trace}")


async def get_json(url: str) -> Any:
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.77 Safari/537.36",
        'Connection': 'close'
    }
    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise ConnectionError(f"Filed to connect {url}, code {response.status_code}.")


def format_timestamp_diff(diff: int) -> str:
    abs_diff = abs(diff)
    if abs_diff < 60:
        return "刚刚"

    if abs_diff < 3600:
        minutes = abs_diff // 60
        info = f"{minutes}分钟"
    elif abs_diff < 86400:
        hours = abs_diff // 3600
        info = f"{hours}小时"
    else:
        days = abs_diff // 86400
        if days >= 365:
            years = days // 365
            info = f"{years}年"
        elif days >= 30:
            months = days // 30
            info = f"{months}个月"
        elif days >= 7:
            weeks = days // 7
            info = f"{weeks}周"
        else:
            info = f"{days}天"

    return f"{info}{'后' if diff < 0 else '前'}"


def format_timestamp(timestamp: int) -> str:
    return time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(timestamp))


def escape_mail_url(content: str) -> str:
    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{1,})'
    return re.sub(email_pattern, lambda x: x.group().replace('.', ' . '), content)
