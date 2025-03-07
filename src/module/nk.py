import re
import traceback

from src.core.command import command
from src.core.constants import Constants
from src.core.output_cached import get_cached_prefix
from src.core.tools import check_is_int, png2jpg
from src.module.message import RobotMessage, report_exception

__nk_version__ = "v1.2.1"

from src.platform.cp.nowcoder import NowCoder


def register_module():
    pass


async def send_user_id_card(message: RobotMessage, handle: str):
    await message.reply(f"正在查询 {handle} 的 NowCoder 基础信息，请稍等")

    id_card = NowCoder.get_user_id_card(handle)

    if isinstance(id_card, str):
        content = (f"[NowCoder ID] {handle}"
                   f"{id_card}")
        await message.reply(content, modal_words=False)
    else:
        cached_prefix = get_cached_prefix('Platform-ID')
        id_card.write_file(f"{cached_prefix}.png")
        await message.reply(f"[NowCoder] {handle}", png2jpg(f"{cached_prefix}.png"), modal_words=False)


async def send_user_info(message: RobotMessage, handle: str):
    await message.reply(f"正在查询 {handle} 的 NowCoder 平台信息，请稍等")

    info, avatar = NowCoder.get_user_info(handle)

    if avatar is None:
        content = (f"[NowCoder] {handle}\n\n"
                   f"{info}")
    else:
        last_contest = NowCoder.get_user_last_contest(handle)
        content = (f"[NowCoder] {handle}\n\n"
                   f"{info}\n\n"
                   f"{last_contest}")

    await message.reply(content, img_url=avatar, modal_words=False)


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

        if func == "identity" or func == "id" or func == "card":
            if len(content) != 3:
                await message.reply(f"请输入正确的指令格式，如\"/nk {func} 329687984\"")
                return

            if not check_is_int(content[2]):
                await message.reply("暂不支持使用昵称检索用户，请使用uid")
                return

            await send_user_id_card(message, content[2])

        elif func == "info" or func == "user":
            if len(content) != 3:
                await message.reply(f"请输入正确的指令格式，如\"/nk {func} 329687984\"")
                return

            if not check_is_int(content[2]):
                await message.reply("暂不支持使用昵称检索用户，请使用uid")
                return

            await send_user_info(message, content[2])

        elif func == "contest" or func == "contests":
            await send_contest(message)

        else:
            await message.reply(f'[NowCoder]\n\n{Constants.help_contents["nowcoder"]}', modal_words=False)

    except Exception as e:
        await report_exception(message, 'NowCoder', traceback.format_exc(), e)
