import os
import time
import re

import botpy
from botpy.ext.cog_yaml import read
from botpy.message import Message, DirectMessage

from utils.oj_lib import *
from utils.cf import reply_cf_request

import threading
from datetime import date
from apscheduler.schedulers.blocking import BlockingScheduler 

import asyncio

test_config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))

_log = logging.get_logger()

daily_sched = BlockingScheduler()
noon_sched = BlockingScheduler()


help_content = """[Functions]

[Main]
/今日题数 [full/留空]: 查询今天从凌晨到现在的做题数情况，第二参数若为 full，那么将会返回完整榜单，否则只返回前 5.
/评测榜单 [verdict]: 查询分类型榜单，其中指定评测结果为第二参数 verdict，需要保证参数中无空格，如 wa, TimeExceeded.
/昨日总榜: 查询昨日的完整榜单.

[sub]
/user id [uid]: 查询 uid 对应用户的信息.
/user name [name]: 查询名为 name 对应用户的信息，支持模糊匹配.
/alive: 检查 OJ, Codeforces, AtCoder 的可连通性.
/api: 获取当前 module-api 的构建信息.
/check: 查询昨日榜单是否生成过.

[robot]
/活着吗: 顾名思义，只要活着回你一句话，不然就不理你.
/似了吗: 如果机器人活着，它将在你回复这句话之后一分钟内无响应.

[3-party]
/capoo: 获取一个 capoo 表情包.
/cf info [handle]: 获取用户名为 handle 的 Codeforces 基础用户信息.
/cf prob tags: 列出 Codeforces 上的所有题目标签.
/cf prob [tag/all] [int/range/留空]: 从 Codeforces 上随机选择一道题，并给出题目的信息。若第二参数不为 all，那么将搜索范围缩小到标签为 tag。若第三参数不为空，那么将搜索范围缩小到难度为给定值 int 或给定范围 range (格式为 l-r)."""


def daily_sched_thread(loop):
    daily_sched.add_job(daily_update_job, "cron", hour=0,minute=0, args=[loop])
    daily_sched.start()


def noon_sched_thread(loop, client):
    noon_sched.add_job(noon_report_job, "cron", hour=13,minute=0, args=[loop, client])
    noon_sched.start()


async def call_handle_message(self, message, is_public):
    content = re.sub(r'<@!\d+>', '', message.content).strip()

    if content == "/help":
        await reply(self, message, help_content)

    elif content == "/api":
        await send_version_info(self, message)

    elif content == "/alive":
        await send_is_alive(self, message)

    elif content == "/check":
        await send_necessity_info(self, message)

    elif content == "/capoo":
        await reply_capoo(self, message)

    else:
        contents = content.split()

        if contents[0] == "/今日题数":
            if len(contents) == 3:
                await send_today_count(self, message, contents[1], contents[2] != "plain")
            else:
                await send_today_count(self, message, "tp5" if (len(contents) < 2 or contents[1] == "plain") else contents[1], not(len(contents) == 2 and contents[1] == "plain"))

        elif contents[0] == "/昨日总榜":
            await send_yesterday_count(self, message, not(len(contents) == 2 and contents[1] == "plain"))

        elif contents[0] == "/评测榜单":
            await send_verdict_count(self, message, contents[1] if len(contents) >= 2 else "", not((len(contents) == 2 and contents[1] == "plain") or (len(contents) == 3 and contents[2] == "plain")))

        elif contents[0] == "/user":
            if len(contents) < 3:
                await reply(self, message, f"请输入三个参数，如 /user id 1")
            elif len(contents) > 3:
                await reply(self, message, f"请输入三个参数，第三个参数不要加上空格")
            else:
                if contents[1] == "id":
                    await send_user_info_uid(self, message, contents[2])
                elif contents[1] == "name":
                    await send_user_info_name(self, message, contents[2])
                else:
                    await reply(self, message, f"请输入正确的参数，如/user id, /user name")
            
        elif contents[0] == "/cf":
            await reply_cf_request(self, message)

        elif is_public:
            if content == "/活着吗":
                await reply(self, message, f"你猜")

            elif content == "/似了吗":
                await reply(self, message, f"你猜我接下来一分钟是生是似")
                time.sleep(60)

            elif "/" in content:
                await reply(self, message, f"其他指令还在开发中qaq")

            else:
                await reply(self, message, f"{match_key_words(content)}")


class MyClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_at_message_create(self, message: Message):
        _log.info(f"{self.robot.name}receive public message {message.content}")
        content = re.sub(r'<@!\d+>', '', message.content).strip()

        if message.channel_id != "633467826":
            _log.info("在频道id {} 中出现了一条消息".format(message.channel_id))
            await reply(self, message, f"请到 \"Bot 互动\" 子频道和Bot进行互动")
            return

        await call_handle_message(self, message, True)
        
    async def on_message_create(self, message: Message):
        #_log.info(f"{self.robot.name}receive global message {message.content}")
        content = message.content

        if message.channel_id != "633467826":
            #_log.info("在频道id {} 中出现了一条消息".format(message.channel_id))
            # await reply(self, message, f"请到 \"Bot 互动\" 子频道和Bot进行互动")
            return

        if not re.search(r'<@!\d+>', content):
            await call_handle_message(self, message, False)
            

if __name__ == "__main__":
    # 通过预设置的类型，设置需要监听的事件通道
    # intents = botpy.Intents.none()
    # intents.public_guild_messages=True

    # 通过kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_guild_messages=True, guild_messages=True)
    client = MyClient(intents=intents)

    daily_thread = threading.Thread(target=daily_sched_thread, args=[asyncio.get_event_loop()])
    daily_thread.start()
    noon_thread = threading.Thread(target=noon_sched_thread, args=[asyncio.get_event_loop(), client])
    noon_thread.start()

    client.run(appid=test_config["appid"], token=test_config["token"])
