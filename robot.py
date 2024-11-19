import asyncio
import os
import queue
import re
import sys
import threading
import traceback
from asyncio import AbstractEventLoop
from typing import Union, List

import botpy
import nest_asyncio
import urllib3
from apscheduler.schedulers.blocking import BlockingScheduler
from botpy import logging, BotAPI, Client, Intents
from botpy.ext.cog_yaml import read
from botpy.message import Message, GroupMessage

from utils.cf import __cf_help_content__
from utils.command import command, __commands__
from utils.hitokoto import __hitokoto_help_content__
from utils.interact import RobotMessage, match_key_words, report_exception
from utils.peeper import send_user_info, \
    daily_update_job, noon_report_job
from utils.pick_one import __pick_one_help_content__, load_pick_one_config
from utils.rand import __rand_help_content__
from utils.tools import check_is_int, run_async

nest_asyncio.apply()
urllib3.disable_warnings()

_config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))
_log = logging.get_logger()
_query_queue = queue.Queue()

daily_sched = BlockingScheduler()
noon_sched = BlockingScheduler()

help_content = f"""[Functions]

[Main]
/今日题数: 查询今天从凌晨到现在的做题数情况.
/昨日总榜: 查询昨日的完整榜单.
/评测榜单 [verdict]: 查询分类型榜单，其中指定评测结果为第二参数 verdict，需要保证参数中无空格，如 wa, TimeExceeded.

[sub]
/user id [uid]: 查询 uid 对应用户的信息.
/user name [name]: 查询名为 name 对应用户的信息，支持模糊匹配.
/alive: 检查 OJ, Codeforces, AtCoder 的可连通性.
/api: 获取当前 module-api 的构建信息.

[robot]
/活着吗: 顾名思义，只要活着回你一句话，不然就不理你.

[pick-one]
{__pick_one_help_content__}

[codeforces]
{__cf_help_content__}

[random]
{__rand_help_content__}

[hitokoto]
{__hitokoto_help_content__}"""


def daily_sched_thread(loop: AbstractEventLoop):
    daily_sched.add_job(daily_update_job, "cron", hour=0, minute=0, args=[loop])
    daily_sched.start()


def noon_sched_thread(loop: AbstractEventLoop, api: BotAPI):
    noon_sched.add_job(noon_report_job, "cron", hour=13, minute=0, args=[loop, api])
    noon_sched.start()


_fixed_reply = {
    "ping": "pong",
    "活着吗": "你猜",
    "help": help_content
}


@command(aliases=_fixed_reply.keys())
async def reply_fixed(message: RobotMessage):
    await message.reply(_fixed_reply.get(message.tokens[0][1:], ""), modal_words=False)


@command(need_check_exclude=True)
async def user(message: RobotMessage):
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


@command(aliases=["去死", "重启", "restart", "reboot"], permission_level=2)
async def reply_restart_bot(message: RobotMessage):
    await message.reply("好的捏，正在原地去世" if message.tokens[0] == '/去死' else "好的捏，正在重启bot")
    _log.info(f"Restarting bot...")
    os.execl(sys.executable, sys.executable, *sys.argv)


async def queue_up_handler():
    while _query_queue.qsize() == 0:  # 忙等待
        pass
    await call_handle_message(_query_queue.get())
    await queue_up_handler()


async def call_handle_message(message: RobotMessage):
    try:
        content = message.tokens

        if len(content) == 0:
            return await message.reply(f"{match_key_words('')}")

        func = content[0].lower()
        for cmd in __commands__.keys():
            starts_with = cmd[-1] == '*' and func.startswith(cmd[:-1])
            if starts_with or cmd == func:
                original_command, execute_level, is_command, need_check_exclude = __commands__[cmd]

                if execute_level > 0:
                    _log.info(f'{message.author_id} attempted {original_command.__name__}.')
                    if execute_level > message.user_permission_level:
                        raise PermissionError("权限不足，操作被拒绝" if func != "/去死" else "阿米诺斯")

                if need_check_exclude:
                    if (message.group_message is not None and
                            message.group_message.group_openid in _config['exclude_group_id']):
                        return await message.reply('榜单功能被禁用，请联系bot管理员')
                try:
                    if starts_with:
                        name = cmd[:-1]
                        replaced = func.replace(name, '')
                        message.tokens = [name] + ([replaced] if replaced else []) + message.tokens[1:]
                    await original_command(message)
                except Exception as e:
                    await report_exception(message, f'Command<{original_command.__name__}>', traceback.format_exc(),
                                           repr(e))
                return

        if '/' in func:
            await message.reply(f"其他指令还在开发中")
        else:
            await message.reply(f"{match_key_words(func)}")

    except Exception as e:
        await report_exception(message, 'Robot-Interact', traceback.format_exc(), repr(e))


async def join_in_message(message: RobotMessage):
    if _query_queue.qsize() > 0:
        await message.reply(f"已加入处理队列，前方还有 {_query_queue.qsize()} 个请求")
    _query_queue.put(message)


class MyClient(Client):
    def __init__(self, main_event_loop: AbstractEventLoop, intents: Intents, timeout: int = 5, is_sandbox=False,
                 log_config: Union[str, dict] = None, log_format: str = None, log_level: int = None,
                 bot_log: Union[bool, None] = True, ext_handlers: Union[dict, List[dict], bool] = True):
        self._main_event_loop = main_event_loop
        super().__init__(intents, timeout, is_sandbox, log_config, log_format, log_level, bot_log, ext_handlers)

    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_at_message_create(self, message: Message):
        _log.info(
            f"{self.robot.name} receive public message {message.content} {message.attachments} "
            f"from {message.channel_id}")
        packed_message = RobotMessage(self.api)
        packed_message.setup_guild_message(self._main_event_loop, message)
        await join_in_message(packed_message)

    async def on_message_create(self, message: Message):
        _log.info(
            f"{self.robot.name} receive global message {message.content} {message.attachments} "
            f"from {message.channel_id}")
        content = message.content

        packed_message = RobotMessage(self.api)
        packed_message.setup_guild_message(self._main_event_loop, message)

        if not re.search(r'<@!\d+>', content):
            await join_in_message(packed_message)

    async def on_group_at_message_create(self, message: GroupMessage):
        _log.info(
            f"{self.robot.name} receive group message {message.content} {message.attachments} "
            f"from {message.group_openid}")
        packed_message = RobotMessage(self.api)
        packed_message.setup_group_message(self._main_event_loop, message)
        await join_in_message(packed_message)


def start_client(loop: AbstractEventLoop):
    # 通过kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_messages=True, public_guild_messages=True, guild_messages=True)
    client = MyClient(loop, intents=intents, timeout=20)

    # 午间推送机制
    noon_thread = threading.Thread(target=noon_sched_thread, args=[asyncio.get_event_loop(), client.api])
    noon_thread.start()

    client.run(appid=_config["appid"], secret=_config["secret"])


def run_queue():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    run_async(loop, queue_up_handler())


def run_msg():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    run_async(loop, start_client(loop))


if __name__ == "__main__":
    # 更新每日排行榜
    daily_thread = threading.Thread(target=daily_sched_thread, args=[asyncio.get_event_loop()])
    daily_thread.start()

    # 加载 pick_one
    load_pick_one_config()

    # 任务线程
    task_thread = threading.Thread(target=run_queue, args=[])
    task_thread.start()

    # 消息线程
    msg_thread = threading.Thread(target=run_msg, args=[])
    msg_thread.start()
    msg_thread.join()
