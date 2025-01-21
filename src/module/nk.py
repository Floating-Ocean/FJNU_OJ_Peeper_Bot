import re
import traceback

from src.core.command import command
from src.core.constants import Constants
from src.module.message import report_exception, RobotMessage

__nk_version__ = "v1.0.0"

from src.platform.cp.nowcoder import NowCoder


def register_module():
    pass


async def send_contest(message: RobotMessage):
    await message.reply(f"正在查询近期 NowCoder 比赛，请稍等")

    info = NowCoder.get_recent_contests()

    content = (f"[NowCoder] 近期比赛\n\n"
               f"{info}")

    await message.reply(content, modal_words=False)


@command(tokens=['nk', 'nc', 'nowcoder'])
async def reply_nk_request(message: RobotMessage):
    try:
        content = re.sub(r'<@!\d+>', '', message.content).strip().split()
        if len(content) < 2:
            await message.reply(f'[NowCoder]\n\n{Constants.help_contents["nowcoder"]}', modal_words=False)
            return

        func = content[1]

        if func == "contest" or func == "contests":
            await send_contest(message)

        else:
            await message.reply(f'[NowCoder]\n\n{Constants.help_contents["nowcoder"]}', modal_words=False)

    except Exception as e:
        await report_exception(message, 'NowCoder', traceback.format_exc(), repr(e))
