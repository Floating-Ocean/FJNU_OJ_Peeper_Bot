﻿import asyncio
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

from utils.cf import reply_cf_request, __cf_help_content__
from utils.hitokoto import reply_hitokoto, __hitokoto_help_content__
from utils.interact import RobotMessage, match_key_words
from utils.peeper import send_now_board, send_yesterday_full_board, send_now_board_with_verdict, send_user_info, \
    send_version_info, daily_update_job, noon_report_job
from utils.pick_one import reply_pick_one, __pick_one_help_content__
from utils.rand import reply_rand_request, __rand_help_content__
from utils.tools import report_exception, check_is_int
from utils.uptime import send_is_alive

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


async def check_exclude(message: RobotMessage) -> bool:
    if message.group_message.group_openid in _config['exclude_group_id']:
        await message.reply('榜单功能被禁用，请联系bot管理员')
        return False
    return True


async def call_handle_message(message: RobotMessage, is_public: bool):
    try:
        content = re.sub(r'<@!\d+>', '', message.content).strip().split()

        if len(content) == 0:
            await message.reply(f"{match_key_words('')}")
            return

        func = content[0]

        if func == "/help":
            await message.reply(help_content, modal_words=False)

        elif func == "/今日题数" or func == "/today":
            if await check_exclude(message):
                await send_now_board(message, (content[1] == "single") if len(content) == 2 else False)

        elif func == "/昨日总榜" or func == "/yesterday" or func == "/full":
            if await check_exclude(message):
                await send_yesterday_full_board(message, (content[1] == "single") if len(content) == 2 else False)

        elif func == "/评测榜单" or func == "/verdict":
            if await check_exclude(message):
                await send_now_board_with_verdict(message, content[1] if len(content) == 2 else "",
                                                  (content[2] == "single") if len(content) == 3 else False)

        elif func == "/user":
            if await check_exclude(message):
                if len(content) < 3:
                    await message.reply("请输入三个参数，第三个参数前要加空格，比如说\"/user id 1\"，\"/user name Hydro\"")
                    return
                if len(content) > 3:
                    await message.reply("请输入三个参数，第三个参数不要加上空格")
                    return
                if content[1] == "id" and (len(content[2]) > 9 or not check_is_int(content[2])):
                    await message.reply("参数错误，id必须为整数")
                    return
                if content[1] == "id" or content[1] == "name":
                    await send_user_info(message, content[2], by_name=(content[1] == "name"))
                else:
                    await message.reply("请输入正确的参数，如\"/user id ...\", \"/user name ...\"")

        elif func == "/alive":
            await send_is_alive(message)

        elif func == "/api":
            await send_version_info(message)

        elif func.startswith("/来只"):
            what = func[3::].strip() if func != "/来只" else ""  # 支持不加空格的形式
            if len(content) >= 2:
                what = content[1]
            await reply_pick_one(message, what)

        elif func.startswith("/添加来只"):
            what = func[5::].strip() if func != "/添加来只" else ""  # 支持不加空格的形式
            if len(content) >= 2:
                what = content[1]
            await reply_pick_one(message, what, msg_type="add")

        elif func == "/审核来只" or func == "/同意来只" or func == "/accept" or func == "/audit":
            await reply_pick_one(message, msg_type="audit")

        elif func == "/随机来只" or func == "/随便来只":
            await reply_pick_one(message, "rand")

        elif func == "/capoo" or func == "/咖波":
            await reply_pick_one(message, "capoo")

        elif func == "/cf":
            await reply_cf_request(message)

        elif (func.startswith("/选择") or func == "/rand" or
              func == "/shuffle" or func == "/打乱"):
            await reply_rand_request(message)

        elif (func == "/hitokoto" or func == "/来句" or
              func == "/来一句" or func == "/来句话" or func == "/来一句话"):
            await reply_hitokoto(message)

        elif is_public:  # 是否被at
            if func == "/活着吗":
                await message.reply(f"你猜")

            elif func == "/ping":
                await message.reply(f"pong", modal_words=False)

            elif func == "/去死" or func == "/重启" or func == "/restart" or func == "/reboot":
                await reply_restart_bot(func, message)

            elif "/" in func:
                await message.reply(f"其他指令还在开发中")

            else:
                await message.reply(f"{match_key_words(func)}")

    except Exception as e:
        await report_exception(message, 'Robot-Interact', traceback.format_exc(), repr(e))


async def reply_restart_bot(func, message):
    _log.info(f"{message.author_id} attempted to restart bot.")
    if message.author_id in _config['admin_qq_id']:
        if func == "/去死":
            await message.reply(f"好的捏，正在原地去世")
        else:
            await message.reply(f"好的捏，正在重启bot")
        _log.info(f"Restarting bot...")
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        if func == "/去死":
            raise PermissionError("阿米诺斯")
        else:
            raise PermissionError("非bot管理员，操作被拒绝")


class MyClient(Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_at_message_create(self, message: Message):
        _log.info(
            f"{self.robot.name} receive public message {message.content} {message.attachments} from {message.channel_id}")
        packed_message = RobotMessage(self.api)
        packed_message.setup_guild_message(message)
        await call_handle_message(packed_message, True)

    async def on_message_create(self, message: Message):
        _log.info(
            f"{self.robot.name} receive global message {message.content} {message.attachments} from {message.channel_id}")
        content = message.content

        packed_message = RobotMessage(self.api)
        packed_message.setup_guild_message(message)

        if not re.search(r'<@!\d+>', content):
            await call_handle_message(packed_message, False)

    async def on_group_at_message_create(self, message: GroupMessage):
        _log.info(
            f"{self.robot.name} receive group message {message.content} {message.attachments} from {message.group_openid}")
        packed_message = RobotMessage(self.api)
        packed_message.setup_group_message(message)
        await call_handle_message(packed_message, True)


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

    client.run(appid=_config["appid"], secret=_config["secret"])
