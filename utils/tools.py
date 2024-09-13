import os
import re
import ssl
import subprocess
import time
from asyncio import AbstractEventLoop

import requests
from botpy import logging
from botpy.ext.cog_yaml import read
from requests.adapters import HTTPAdapter

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
        _log.info(line)
        info += line

        if line == "" or subprocess.Popen.poll(cmd) == 0:  # 判断子进程是否结束
            break

    return info


def run_async(loop: AbstractEventLoop, func: any):
    task = loop.create_task(func)
    loop.run_until_complete(task)
    loop.close()
    return task.result()


async def report_exception(message: RobotMessage, name: str, trace: str, info: str):
    _log.error(trace)
    await message.reply(f"[Operation failed] in module {name}.\n\n{info}", modal_words=False)


def fetch_json(url: str, payload: dict = None) -> dict:
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.77 Safari/537.36",
        'Connection': 'close'
    }
    response = requests.post(url, headers=headers, json=payload)

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


def check_is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


async def save_img(url: str, file_path: str) -> bool:
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.77 Safari/537.36"
    }
    if not url.startswith('https://'):
        url = f'https://{url}'

    sess = requests.session()
    sess.mount("https://", SSLAdapter())   # 将上面定义的SSLAdapter 应用起来

    response = sess.get(url, headers=headers, verify=False)  # 阻止ssl验证

    if response.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(response.content)
            f.close()
        return True

    return False


class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        """
        tls1.3 不再支持RSA KEY exchange，py3.10 增加TLS的默认安全设置。可能导致握手失败。
        使用 `ssl_context.set_ciphers('DEFAULT')` DEFAULT 老的加密设置。
        """
        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers('DEFAULT')
        ssl_context.check_hostname = False  # 避免在请求时 verify=False 设置时报错， 如果设置需要校验证书可去掉该行。
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2  # 最小版本设置成1.2 可去掉低版本的警告
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_2  # 最大版本设置成1.2
        kwargs["ssl_context"] = ssl_context
        return super().init_poolmanager(*args, **kwargs)
