
from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters import Message
from nonebot.params import CommandArg,Command
from nonebot.log import logger
from nonebot.exception import MatcherException

from nonebot_plugin_saa import MessageFactory,AggregatedMessageFactory,Image

from io import BytesIO

from src.core.constants import Constants
from src.core.tools import get_simple_qrcode, png2jpg
from src.platform.cp.atcoder import AtCoder
from src.core.tools import help

import re
import traceback


__atc_version__ = "v1.2.0"

supported_commands = ['pick']#'info','user', 'contests', 'pick']

async def send_user_info(handle: str):
    await MessageFactory(f"[Atcoder] 正在查询 {handle} 的 AtCoder 平台信息，请稍等...").send()

    info, avatar = AtCoder.get_user_info(handle)

    if avatar is None:
        content = (f"[AtCoder] {handle}\n\n"
                   f"{info}")
    else:
        last_contest = AtCoder.get_user_last_contest(handle)
        content = (f"[AtCoder] {handle}\n\n"
                   f"{info}\n\n"
                   f"{last_contest}")

    messages = []
    if avatar is not None:
        messages.append(MessageFactory(Image(avatar)))
    messages.append(MessageFactory(content))
    await AggregatedMessageFactory(messages).finish()


async def send_prob_filter_tag(contest_type: str, limit: str = None) -> bool:
    await MessageFactory("正在随机选题，请稍等").send()
    logger.debug(f"type:{contest_type},limit:{limit}")
    chosen_prob = AtCoder.get_prob_filtered(contest_type, limit)
    if isinstance(chosen_prob,int):
        await MessageFactory(f"clist返回：{chosen_prob}").send()
    if isinstance(chosen_prob, int) and chosen_prob < 0:
        return False

    if isinstance(chosen_prob, int):
        await MessageFactory("条件不合理或过于苛刻，无法找到满足条件的题目").finish()
        return True

    abbr = chosen_prob['url'].split('/')[-1].capitalize()
    link = chosen_prob['url'].replace('https://atcoder.jp', '')
    content = (f"[AtCoder] 随机选题\n\n"
               f"{abbr} {chosen_prob['name']}\n\n"
               f"链接: [atcoder] {link}")

    if 'rating' in chosen_prob:
        content += f"\n难度: *{chosen_prob['rating']}"

    qr_img = get_simple_qrcode(chosen_prob['url'])
    img_byte = BytesIO()
    qr_img.save(img_byte,format='PNG')
    await AggregatedMessageFactory([MessageFactory(content),MessageFactory(Image(img_byte))]).finish()

    return True


async def send_contest():
    await MessageFactory(f"正在查询近期 AtCoder 比赛，请稍等").send()

    info = AtCoder.get_recent_contests()

    content = (f"[AtCoder] 近期比赛\n\n"
               f"{info}")

    await AggregatedMessageFactory(MessageFactory(content)).finish()

regular_handler = on_command(('atc','help'),rule=to_me(),
                             aliases = {('atc', command) for command in supported_commands},
                             priority=Constants.PLATFORM_PRIOR,block=True)

fullname_handler = on_command(('atcoder','help'),rule=to_me(),
                              aliases = {('atcoder', command) for command in supported_commands},
                              priority=Constants.PLATFORM_PRIOR,block=True)

help_trigger = on_command('atc',rule=to_me(),aliases={'atcoder'},priority=Constants.HELP_PRIOR,block=True)

@help_trigger.handle()
async def handle_help():
    await help("Atcoder")

@regular_handler.handle()
@fullname_handler.handle()
async def handle_regular(command:tuple[str,str]=Command(),message:Message = CommandArg()):
    try:
        func = command[1]
        args = message.extract_plain_text().split()
        if func == "info" or func == "user":
            if len(args) != 1:
                await MessageFactory("请输入正确的指令格式，如\"/atc.info jiangly\"").finish()
                return
            handle = args[0]
            await send_user_info(handle)

        elif func == "pick":
            if not len(args) or not await send_prob_filter_tag(
                    contest_type=args[0],
                    limit=args[1] if len(args) >= 2 else None):
                func_prefix = f"/atc.pick"
                await MessageFactory("请输入正确的指令格式，题目标签不要带有空格，如:\n\n"
                                    f"{func_prefix} common\n"
                                    f"{func_prefix} abc\n"
                                    f"{func_prefix} sp 1200-1600\n"
                                    f"{func_prefix} all 1800").finish()

        elif func == "contest" or func == "contests":
            await send_contest()

        else:
            await help("Atcoder","",False)
    except MatcherException:
        raise
    except Exception as e:
        logger.exception(e.__str__)
        await help("Atcoder","出现未知异常。请联系管理员。",False)
