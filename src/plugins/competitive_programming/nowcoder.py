import re
import traceback

from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters import Message
from nonebot.params import CommandArg,Command
from nonebot.log import logger
from nonebot.exception import MatcherException

from nonebot_plugin_saa import MessageFactory,AggregatedMessageFactory,Image


from src.core.constants import Constants
from src.core.tools import check_is_int
from src.platform.cp.nowcoder import NowCoder
from src.core.tools import reply_help

__nk_version__ = "v1.1.0"


supported_commands = ['info','user','contests']

def register_module():
    pass

regular_handler = on_command(('nk','help'),rule=to_me(),
                             aliases = {('nk', command) for command in supported_commands},
                             priority=Constants.PLATFORM_PRIOR,block=True)

alias_handler = on_command(('nc','help'),rule=to_me(),
                             aliases = {('nc', command) for command in supported_commands},
                             priority=Constants.PLATFORM_PRIOR,block=True)

fullname_handler = on_command(('nowcoder','help'),rule=to_me(),
                              aliases = {('nowcoder', command) for command in supported_commands},
                              priority=Constants.PLATFORM_PRIOR,block=True)

help_trigger = on_command('nowcoder',rule=to_me(),aliases={'nk','nc'},priority=Constants.HELP_PRIOR,block=True)

@help_trigger.handle()
async def handle_help():
    await reply_help("Nowcoder")

async def send_user_info(handle: str):
    await MessageFactory(f"正在查询 {handle} 的 NowCoder 平台信息，请稍等").send()

    info, avatar = NowCoder.get_user_info(handle)

    if avatar is None:
        content = (f"[NowCoder] {handle}\n\n"
                   f"{info}")
    else:
        last_contest = NowCoder.get_user_last_contest(handle)
        content = (f"[NowCoder] {handle}\n\n"
                   f"{info}\n\n"
                   f"{last_contest}")

    messages = []
    if avatar is not None:
        messages.append(MessageFactory(Image(avatar)))
    messages.append(MessageFactory(content))
    await AggregatedMessageFactory(messages).finish()


async def send_contest():
    await MessageFactory(f"正在查询近期 NowCoder 比赛，请稍等").send()

    info = NowCoder.get_recent_contests()

    content = (f"[NowCoder] 近期比赛\n\n"
               f"{info}")

    await AggregatedMessageFactory(MessageFactory(content)).finish()


@regular_handler.handle()
@alias_handler.handle()
@fullname_handler.handle()
async def handle_regular(command:tuple[str,str]=Command(),message:Message = CommandArg()):
    try:
        func = command[1]
        args = message.extract_plain_text().split()
        if func == "info" or func == "user":
            if len(args) != 1:
                await MessageFactory("请输入正确的指令格式，如\"/nk info 815516497\"").finish()
            uid = args[0]
            if not check_is_int(uid):
                await MessageFactory("暂不支持使用昵称检索用户，请使用uid").finish()

            await send_user_info(uid)

        elif func == "contest" or func == "contests":
            await send_contest()
        else:
            reply_help("Nowcoder","",False)
    except MatcherException:
        raise
    except Exception as e:
        logger.exception(e.__str__)
        await reply_help("Nowcoder","出现未知异常。请联系管理员。",False)
