import asyncio
import os
import queue
import re
import sys
import threading
from asyncio import AbstractEventLoop
from typing import Union, List

import botpy
from apscheduler.schedulers.blocking import BlockingScheduler
from botpy import BotAPI, Client, Intents
from botpy.message import Message, GroupMessage, C2CMessage

from src.core.command import command
from src.core.constants import Constants
from src.core.interact import RobotMessage, call_handle_message
from src.core.tools import run_async
from src.module.peeper import daily_update_job, noon_report_job

_query_queue = queue.Queue()

daily_sched = BlockingScheduler()
noon_sched = BlockingScheduler()


def daily_sched_thread(loop: AbstractEventLoop):
    daily_sched.add_job(daily_update_job, "cron", hour=0, minute=0, args=[loop])
    daily_sched.start()


def noon_sched_thread(loop: AbstractEventLoop, api: BotAPI):
    noon_sched.add_job(noon_report_job, "cron", hour=13, minute=0, args=[loop, api])
    noon_sched.start()


@command(tokens=["去死", "重启", "restart", "reboot"], permission_level=2)
async def reply_restart_bot(message: RobotMessage):
    await message.reply("好的捏，捏？欸我怎么似了" if message.tokens[0] == '/去死' else "好的捏，正在重启bot")
    Constants.log.info(f"Restarting bot...")
    os.execl(sys.executable, sys.executable, *sys.argv)


async def queue_up_handler():
    while True:
        while _query_queue.qsize() == 0:  # 忙等待
            pass
        await call_handle_message(_query_queue.get())


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
        Constants.log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_at_message_create(self, message: Message):
        Constants.log.info(
            f"{self.robot.name} receive public message {message.content} {message.attachments} "
            f"from {message.channel_id}")
        packed_message = RobotMessage(self.api)
        packed_message.setup_guild_message(self._main_event_loop, message)
        await join_in_message(packed_message)

    async def on_message_create(self, message: Message):
        Constants.log.info(
            f"{self.robot.name} receive global message {message.content} {message.attachments} "
            f"from {message.channel_id}")
        content = message.content

        packed_message = RobotMessage(self.api)
        packed_message.setup_guild_message(self._main_event_loop, message, is_public=True)

        if not re.search(r'<@!\d+>', content):
            await join_in_message(packed_message)

    async def on_group_at_message_create(self, message: GroupMessage):
        Constants.log.info(
            f"{self.robot.name} receive group message {message.content} {message.attachments} "
            f"from {message.group_openid}")
        packed_message = RobotMessage(self.api)
        packed_message.setup_group_message(self._main_event_loop, message)
        await join_in_message(packed_message)

    async def on_c2c_message_create(self, message: C2CMessage):
        Constants.log.info(
            f"{self.robot.name} receive private message {message.content} {message.attachments} "
            f"from {message.author.user_openid}")
        packed_message = RobotMessage(self.api)
        packed_message.setup_c2c_message(self._main_event_loop, message)
        await join_in_message(packed_message)


def start_client(loop: AbstractEventLoop):
    # 对目前已支持的所有事件进行监听
    intents = botpy.Intents.default()
    client = MyClient(loop, intents=intents, timeout=60)

    # 午间推送机制
    noon_thread = threading.Thread(target=noon_sched_thread, args=[asyncio.get_event_loop(), client.api])
    noon_thread.start()

    client.run(appid=Constants.config["appid"], secret=Constants.config["secret"])


def run_queue():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    run_async(loop, queue_up_handler())


def run_msg():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    run_async(loop, start_client(loop))


def open_robot_session():
    # 更新每日排行榜
    daily_thread = threading.Thread(target=daily_sched_thread, args=[asyncio.get_event_loop()])
    daily_thread.start()

    # 任务线程
    task_thread = threading.Thread(target=run_queue, args=[])
    task_thread.start()

    # 消息线程
    msg_thread = threading.Thread(target=run_msg, args=[])
    msg_thread.start()
    msg_thread.join()
