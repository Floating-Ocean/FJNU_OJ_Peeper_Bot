import re
import traceback

from src.core.command import command
from src.core.constants import Constants
from src.modules.message import report_exception, RobotMessage
from src.platforms.atcoder import AtCoder

__atc_version__ = "v1.1.0"


def register_module():
    pass


async def send_user_info(message: RobotMessage, handle: str):
    await message.reply(f"正在查询 {handle} 的 AtCoder 平台信息，请稍等")

    info, avatar = AtCoder.get_user_info(handle)

    if avatar is None:
        content = (f"[AtCoder] {handle}\n\n"
                   f"{info}")
    else:
        last_contest = AtCoder.get_user_last_contest(handle)
        content = (f"[AtCoder] {handle}\n\n"
                   f"{info}\n\n"
                   f"{last_contest}")

    await message.reply(content, img_url=avatar, modal_words=False)


async def send_contest(message: RobotMessage):
    await message.reply(f"正在查询近期 AtCoder 比赛，请稍等")

    info = AtCoder.get_recent_contests()

    content = (f"[AtCoder] 近期比赛\n\n"
               f"{info}")

    await message.reply(content, modal_words=False)


@command(tokens=['atc', 'atcoder'])
async def reply_cf_request(message: RobotMessage):
    try:
        content = re.sub(r'<@!\d+>', '', message.content).strip().split()
        if len(content) < 2:
            await message.reply(f"[AtCoder]\n\n{Constants.atc_help_content}", modal_words=False)
            return

        func = content[1]

        if func == "info" or func == "user":
            if len(content) != 3:
                await message.reply("请输入正确的指令格式，如\"/atc info jiangly\"")
                return

            await send_user_info(message, content[2])

        elif func == "contest" or func == "contests":
            await send_contest(message)

        else:
            await message.reply(f"[AtCoder]\n\n{Constants.atc_help_content}", modal_words=False)

    except Exception as e:
        await report_exception(message, 'AtCoder', traceback.format_exc(), repr(e))
