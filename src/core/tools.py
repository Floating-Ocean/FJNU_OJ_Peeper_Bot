import asyncio
import datetime
import hashlib
import os
import random
import re
import ssl
import string
import subprocess
import time
from asyncio import AbstractEventLoop

import requests
from PIL import Image
from lxml import etree
from lxml.etree import Element
from requests.adapters import HTTPAdapter

from src.core.constants import Constants


def run_shell(shell: str) -> str:
    Constants.log.info(shell)
    cmd = subprocess.Popen(shell, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                           universal_newlines=True, shell=True, bufsize=1)
    info = ""
    # 实时输出
    while True:
        line = cmd.stderr.readline().strip()
        Constants.log.info(line)
        info += line

        if line == "" or subprocess.Popen.poll(cmd) == 0:  # 判断子进程是否结束
            break

    return info


def run_async(loop: AbstractEventLoop, func: any):
    asyncio.set_event_loop(loop)
    task = loop.create_task(func)
    loop.run_until_complete(task)
    return task.result()


def fetch_html(url: str, payload: dict = None) -> Element:
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.77 Safari/537.36",
        'Connection': 'close'
    }
    response = requests.get(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise ConnectionError(f"Filed to connect {url}, code {response.status_code}.")

    return etree.HTML(response.text)


def fetch_json(url: str, payload: dict = None, throw: bool = True) -> dict | None:
    try:
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/91.0.4472.77 Safari/537.36",
            'Connection': 'close'
        }
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200 and throw:
            raise ConnectionError(f"Filed to connect {url}, code {response.status_code}.")

        return response.json()
    except Exception as e:
        if throw:
            raise e
        return None


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
    return time.strftime('%y/%m/%d %H:%M:%S', time.localtime(timestamp))


def format_seconds(seconds: int) -> str:
    units_in_seconds = [
        ['天', 365 * 24 * 3600, 24 * 3600],
        ['小时', 24 * 3600, 3600],
        ['分钟', 3600, 60],
        ['秒', 60, 1]
    ]
    return ''.join([f" {seconds % u_mod // u_div} {name}"
                    for name, u_mod, u_div in units_in_seconds if seconds % u_mod // u_div > 0]).strip()


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
    sess.mount("https://", SSLAdapter())  # 将上面定义的SSLAdapter 应用起来

    response = sess.get(url, headers=headers, verify=False)  # 阻止ssl验证

    if response.status_code == 200:
        parent_path = os.path.dirname(file_path)
        if not os.path.exists(parent_path):
            os.makedirs(parent_path)

        with open(file_path, "wb") as f:
            f.write(response.content)
            f.close()

        return True

    return False


def png2jpg(path: str) -> str:
    img = Image.open(path)
    new_path = os.path.splitext(path)[0] + '.jpg'
    img.convert('RGB').save(new_path)
    return new_path


def get_md5(path: str) -> str:
    md5 = hashlib.md5()
    file = open(path, 'rb')
    md5.update(file.read())
    file.close()
    return md5.hexdigest()


def rand_str_len32() -> str:
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(32)])


def get_today_start_timestamp() -> int:
    today = datetime.datetime.now().date()
    today_start = datetime.datetime.combine(today, datetime.time.min)
    timestamp = int(today_start.timestamp())
    return timestamp


def get_week_start_timestamp() -> int:
    today = datetime.datetime.now()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    week_start = datetime.datetime.combine(start_of_week.date(), datetime.time.min)
    timestamp = int(week_start.timestamp())
    return timestamp


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
