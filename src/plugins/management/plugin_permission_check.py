from nonebot import get_driver , logger
from nonebot.matcher import Matcher
from nonebot.message import run_preprocessor
from nonebot.exception import IgnoredException
from nonebot_plugin_session import EventSession

from .plugin_permission_set import cubp

superusers = get_driver().config.superusers


@run_preprocessor
async def pass_run(
    matcher: Matcher,
    session: EventSession,
):
    user_id = str(session.id1)
    if session.level >= 2:
        mode = await passgroup_rule(user_id, session.id2, matcher)
        if mode == "white": return
        if session.level == 3:
             #子ID也支持但是可能会有冲突
            mode = await passgroup_rule(user_id, session.id3, matcher)
            if mode == "white": return
    await pass_rule(user_id, matcher)
           
    pass


async def pass_rule(user_id: str, matcher: Matcher):

    modulename = matcher.plugin.name
    if modulename.startswith("nonebot_plugin_"):
        modulename = modulename.replace("nonebot_plugin_", "")
    msg = f"Plugin {modulename} is triggered by {user_id}, checking permission!"
    logger.opt(colors=True).debug(msg)
    check , mode = cubp.checkperm(modulename, user_id)
    if check:
        if user_id in superusers:
            return "white"
        msg = f"{user_id} is not allowed to run {modulename}.Ignoring."
        logger.opt(colors=True).warning(msg)
        raise IgnoredException(msg) from None
    return mode


async def passgroup_rule(user_id: str, group_id: str, matcher: Matcher):
    modulename = matcher.plugin.name
    if modulename.startswith("nonebot_plugin_"):
        modulename = modulename.replace("nonebot_plugin_", "")
    msg = f"Plugin {modulename} is triggered by group {group_id}, checking permission!"
    logger.opt(colors=True).debug(msg)
    check , mode = cubp.checkpermgroup(modulename, group_id)
    if check:
        if user_id in superusers:
            msg =f"Group {group_id} is not allowed to run {modulename}.But the user is a SUPERUSER.BYPASSING."
            logger.opt(colors=True).warning(msg)
            return "white"
        msg = f"Group {group_id} is not allowed to run {modulename}.Ignoring."
        logger.opt(colors=True).warning(msg)
        raise IgnoredException(msg) from None
    return mode
