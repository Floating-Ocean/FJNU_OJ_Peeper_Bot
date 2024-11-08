import asyncio
import os
import re
import sys
import threading
import traceback
from asyncio import AbstractEventLoop

import botpy
import nest_asyncio
import urllib3
from apscheduler.schedulers.blocking import BlockingScheduler
from botpy import logging, BotAPI, Client
from botpy.ext.cog_yaml import read
from botpy.message import Message, GroupMessage

from utils.cf import __cf_help_content__
from utils.command import command, _commands
from utils.hitokoto import __hitokoto_help_content__
from utils.interact import RobotMessage, match_key_words
from utils.peeper import send_user_info, \
    daily_update_job, noon_report_job
from utils.pick_one import __pick_one_help_content__, load_pick_one_config
from utils.rand import __rand_help_content__
from utils.tools import report_exception, check_is_int
from utils.uptime import fetch_status

nest_asyncio.apply()
urllib3.disable_warnings()

_config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))
_log = logging.get_logger()

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
    await message.reply(_fixed_reply.get(message.pure_content[0][1:], ""), modal_words=False)


@command(need_check_exclude=True)
async def user(message: RobotMessage):
    content = message.pure_content
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
    await message.reply("好的捏，正在原地去世" if message.pure_content[0] == '/去死' else "好的捏，正在重启bot")
    _log.info(f"Restarting bot...")
    os.execl(sys.executable, sys.executable, *sys.argv)


async def call_handle_message(message: RobotMessage):
    try:
        content = message.pure_content

        if len(content) == 0:
            return await message.reply(f"{match_key_words('')}")

        func = content[0].lower()
        for cmd in _commands.keys():
            starts_with = cmd[-1] == '*' and func.startswith(cmd[:-1])
            if starts_with or cmd == func:
                original_command, execute_level, is_command, need_check_exclude = _commands[cmd]

                if execute_level > 0:
                    print(f'{message.author_id} attempted {original_command.__name__}.')
                    if execute_level > message.user_permission_level:
                        raise PermissionError("权限不足，操作被拒绝")

                if need_check_exclude:
                    if (message.group_message is not None and
                            message.group_message.group_openid in _config['exclude_group_id']):
                        return await message.reply('榜单功能被禁用，请联系bot管理员')
                try:
                    if starts_with:
                        name = cmd[:-1]
                        replaced = func.replace(name, '')
                        message.pure_content = [name] + ([replaced] if replaced else []) + message.pure_content[1:]
                    await original_command(message)
                except Exception as e:
                    await report_exception(message, f'Command-{original_command.__name__}', traceback.format_exc(),
                                           repr(e))
                return

        if '/' in func:
            await message.reply(f"其他指令还在开发中")
        else:
            await message.reply(f"{match_key_words(func)}")

    except Exception as e:
        await report_exception(message, 'Robot-Interact', traceback.format_exc(), repr(e))


class MyClient(Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_at_message_create(self, message: Message):
        _log.info(
            f"{self.robot.name} receive public message {message.content} {message.attachments} from {message.channel_id}")
        packed_message = RobotMessage(self.api)
        packed_message.setup_guild_message(message)
        await call_handle_message(packed_message)

    async def on_message_create(self, message: Message):
        _log.info(
            f"{self.robot.name} receive global message {message.content} {message.attachments} from {message.channel_id}")
        content = message.content

        packed_message = RobotMessage(self.api)
        packed_message.setup_guild_message(message)

        if not re.search(r'<@!\d+>', content):
            await call_handle_message(packed_message)

    async def on_group_at_message_create(self, message: GroupMessage):
        _log.info(
            f"{self.robot.name} receive group message {message.content} {message.attachments} from {message.group_openid}")
        packed_message = RobotMessage(self.api)
        packed_message.setup_group_message(message)
        await call_handle_message(packed_message)


if __name__ == "__main__":
    # 通过kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_messages=True, public_guild_messages=True, guild_messages=True)
    client = MyClient(intents=intents, timeout=20)

    # 更新每日排行榜
    daily_thread = threading.Thread(target=daily_sched_thread, args=[asyncio.get_event_loop()])
    daily_thread.start()

    # 午间推送机制
    noon_thread = threading.Thread(target=noon_sched_thread, args=[asyncio.get_event_loop(), client.api])
    noon_thread.start()

    # 加载 pick_one 和 uptime
    load_pick_one_config()
    fetch_status("fjnuacm.top")

    client.run(appid=_config["appid"], secret=_config["secret"])
