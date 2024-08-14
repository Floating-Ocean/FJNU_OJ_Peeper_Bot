import asyncio
import os
import re
import sys
import threading
import traceback
from asyncio import AbstractEventLoop

import botpy
import nest_asyncio
from apscheduler.schedulers.blocking import BlockingScheduler
from botpy import logging, BotAPI, Client
from botpy.ext.cog_yaml import read
from botpy.message import Message, GroupMessage

from utils.cf import reply_cf_request
from utils.interact import RobotMessage, match_key_words
from utils.oj_lib import send_today_count, send_yesterday_count, send_verdict_count, send_user_info_uid, \
    send_user_info_name, send_version_info, daily_update_job, noon_report_job
from utils.pick_one import reply_pick_one
from utils.tools import report_exception
from utils.uptime import send_is_alive

nest_asyncio.apply()

_config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))
_log = logging.get_logger()

daily_sched = BlockingScheduler()
noon_sched = BlockingScheduler()

help_content = """[Functions]

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

[3-party]
/来只 [what]: 获取一个随机表情包，目前只有 capoo.
/cf info [handle]: 获取用户名为 handle 的 Codeforces 基础用户信息.
/cf pick [标签|all] (难度) (New): 从 Codeforces 上随机选题. 标签中间不能有空格，支持模糊匹配. 难度为整数或一个区间，格式为xxx-xxx. 末尾加上 New 参数则会忽视 P1000A 以前的题.
/cf contest: 列出最近的 Codeforces 比赛.
/cf tags: 列出 Codeforces 上的所有题目标签."""


def daily_sched_thread(loop: AbstractEventLoop):
    daily_sched.add_job(daily_update_job, "cron", hour=0, minute=0, args=[loop])
    daily_sched.start()


def noon_sched_thread(loop: AbstractEventLoop, api: BotAPI):
    noon_sched.add_job(noon_report_job, "cron", hour=13, minute=0, args=[loop, api])
    noon_sched.start()


async def call_handle_message(message: RobotMessage, is_public: bool):
    try:
        content = re.sub(r'<@!\d+>', '', message.content).strip().split()

        if len(content) == 0:
            await message.reply(f"{match_key_words('')}")
            return

        func = content[0]

        if func == "/help":
            await message.reply(help_content)

        elif func == "/今日题数" or func == "/today":
            await send_today_count(message)

        elif func == "/昨日总榜" or func == "/yesterday" or func == "/full":
            await send_yesterday_count(message)

        elif func == "/评测榜单" or func == "/verdict":
            await send_verdict_count(message, content[1] if len(content) == 2 else "")

        elif func == "/user":
            if len(content) < 3:
                await message.reply(f"请输入三个参数，如 /user id 1")
            elif len(content) > 3:
                await message.reply(f"请输入三个参数，第三个参数不要加上空格")
            else:
                if content[1] == "id":
                    await send_user_info_uid(message, content[2])
                elif content[1] == "name":
                    await send_user_info_name(message, content[2])
                else:
                    await message.reply(f"请输入正确的参数，如/user id, /user name")

        elif func == "/alive":
            await send_is_alive(message)

        elif func == "/api":
            await send_version_info(message)

        elif func.startswith("/来只"):
            what = func[3::] if func != "/来只" else ""  # 支持不加空格的形式
            if len(content) >= 2:
                what = content[1]
            await reply_pick_one(message, what)

        elif func == "/capoo" or func == "/咖波":
            await reply_pick_one(message, "capoo")

        elif func == "/cf":
            await reply_cf_request(message)

        elif is_public:
            if func == "/活着吗":
                await message.reply(f"你猜")

            elif func == "/ping":
                await message.reply(f"pong")

            elif func == "/去死" or func == "/重启" or func == "/restart" or func == "/reboot":
                _log.info(f"{message.get_author()} attempted to restart bot.")
                if message.get_author() in _config['admin_qq_id']:
                    await message.reply(f"好的捏，正在重启bot")
                    _log.info(f"Restarting bot...")
                    os.execl(sys.executable, sys.executable, *sys.argv)
                else:
                    raise PermissionError("阿米诺斯" if func == "/去死" else "非bot管理员，操作被拒绝")

            elif "/" in func:
                await message.reply(f"其他指令还在开发中qaq")

            else:
                await message.reply(f"{match_key_words(func)}")

    except Exception as e:
        await report_exception(message, 'Robot-Interact', traceback.format_exc())


class MyClient(Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_at_message_create(self, message: Message):
        _log.info(f"{self.robot.name} receive public message {message.content}")
        packed_message = RobotMessage(self.api)
        packed_message.setup_guild_message(message)
        await call_handle_message(packed_message, True)

    async def on_message_create(self, message: Message):
        _log.info(f"{self.robot.name} receive global message {message.content}")
        content = message.content

        packed_message = RobotMessage(self.api)
        packed_message.setup_guild_message(message)

        if not re.search(r'<@!\d+>', content):
            await call_handle_message(packed_message, False)

    async def on_group_at_message_create(self, message: GroupMessage):
        _log.info(f"{self.robot.name} receive group message {message.content}")
        packed_message = RobotMessage(self.api)
        packed_message.setup_group_message(message)
        await call_handle_message(packed_message, True)


if __name__ == "__main__":
    # 通过kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_messages=True, public_guild_messages=True, guild_messages=True)
    client = MyClient(intents=intents)

    # 更新每日排行榜
    daily_thread = threading.Thread(target=daily_sched_thread, args=[asyncio.get_event_loop()])
    daily_thread.start()

    # 午间推送机制
    noon_thread = threading.Thread(target=noon_sched_thread, args=[asyncio.get_event_loop(), client.api])
    noon_thread.start()

    client.run(appid=_config["appid"], secret=_config["secret"])
