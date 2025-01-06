import re
import traceback

from src.core.command import command
from src.core.constants import Constants
from src.core.tools import check_is_int
from src.modules.message import report_exception, RobotMessage
from src.platforms.codeforces import Codeforces

__cf_version__ = "v2.1.3"


def register_module():
    pass


async def send_user_info(message: RobotMessage, handle: str):
    await message.reply(f"正在查询 {handle} 的 Codeforces 平台信息，请稍等")

    info, avatar = Codeforces.get_user_info(handle)

    if info is None:
        content = (f"[Codeforces] {handle}\n\n"
                   f"用户不存在")
    else:
        last_contest = Codeforces.get_user_last_contest(handle)
        last_submit = Codeforces.get_user_last_submit(handle)
        total_sums, weekly_sums, daily_sums = Codeforces.get_user_submit_sums(handle)
        daily = "今日暂无过题" if daily_sums == 0 else f"今日通过 {daily_sums} 题"
        weekly = "" if weekly_sums == 0 else f"，本周共通过 {weekly_sums} 题"
        content = (f"[Codeforces] {handle}\n\n"
                   f"{info}\n"
                   f"通过题数: {total_sums}\n\n"
                   f"{last_contest}\n\n"
                   f"{daily}{weekly}\n"
                   f"{last_submit}")

    await message.reply(content, img_url=avatar, modal_words=False)


async def send_user_last_submit(message: RobotMessage, handle: str, count: int):
    await message.reply(f"正在查询 {handle} 的 Codeforces 提交记录，请稍等")

    info, _ = Codeforces.get_user_info(handle)

    if info is None:
        content = (f"[Codeforces] {handle}\n\n"
                   f"用户不存在")
    else:
        last_submit = Codeforces.get_user_last_submit(handle, count)
        content = (f"[Codeforces] {handle}\n\n"
                   f"{last_submit}")

    await message.reply(content, modal_words=False)


async def send_prob_tags(message: RobotMessage):
    await message.reply("正在查询 Codeforces 平台的所有问题标签，请稍等")

    prob_tags = Codeforces.get_prob_tags_all()

    if prob_tags is None:
        content = "查询异常"
    else:
        content = "\n[Codeforces] 问题标签:\n"
        for tag in prob_tags:
            content += "\n" + tag

    await message.reply(content, modal_words=False)


async def send_prob_filter_tag(message: RobotMessage, tag: str, limit: str = None, newer: bool = False) -> bool:
    await message.reply("正在随机选题，请稍等")

    chosen_prob = await Codeforces.get_prob_filter_tag(message, tag, limit, newer)

    if chosen_prob is None:
        return False

    tags = ', '.join(chosen_prob['tags'])
    content = (f"[Codeforces] 随机选题\n\n"
               f"P{chosen_prob['contestId']}{chosen_prob['index']} {chosen_prob['name']}\n\n"
               f"链接: [codeforces] /contest/{chosen_prob['contestId']}/problem/{chosen_prob['index']}\n"
               f"标签: {tags}")

    if 'rating' in chosen_prob:
        content += f"\n难度: *{chosen_prob['rating']}"

    await message.reply(content, modal_words=False)

    return True


async def send_contest(message: RobotMessage):
    await message.reply(f"正在查询近期 Codeforces 比赛，请稍等")

    info = Codeforces.get_recent_contests()

    content = (f"[Codeforces] 近期比赛\n\n"
               f"{info}")

    await message.reply(content, modal_words=False)


async def send_logo(message: RobotMessage):
    await message.reply("[Codeforces] 网站当前的图标", img_url=Codeforces.logo_url)


@command(tokens=['cf', 'codeforces'])
async def reply_cf_request(message: RobotMessage):
    try:
        content = re.sub(r'<@!\d+>', '', message.content).strip().split()
        if len(content) < 2:
            await message.reply(f"[Codeforces]\n\n{Constants.cf_help_content}", modal_words=False)
            return

        func = content[1]

        if func == "info" or func == "user":
            if len(content) != 3:
                await message.reply("请输入正确的指令格式，如\"/cf info jiangly\"")
                return

            await send_user_info(message, content[2])

        elif func == "recent":
            if len(content) != 3 and len(content) != 4:
                await message.reply("请输入正确的指令格式，如\"/cf recent jiangly 5\"")
                return

            if len(content) == 4 and (len(content[3]) >= 3 or not check_is_int(content[3]) or int(content[3]) <= 0):
                await message.reply("参数错误，请输入 [1, 99] 内的整数")
                return

            await send_user_last_submit(message, content[2], int(content[3]) if len(content) > 3 else 5)

        elif func == "pick" or func == "prob" or func == "problem" or (
                content[0] == "rand" and func == "cf"):  # 让此处能被 /rand 模块调用
            if not await send_prob_filter_tag(
                    message=message,
                    tag=content[2],
                    limit=content[3] if len(content) >= 4 and content[3] != "new" else None,
                    newer=content[3] == "new" if len(content) == 4 else (
                            content[4] == "new" if len(content) == 5 else False)
            ):
                func_prefix = f"/cf {func}"
                if func == "cf":
                    func_prefix = "/rand cf"
                await message.reply("请输入正确的指令格式，如:\n\n"
                                    f"{func_prefix} dp 1700-1900 new\n"
                                    f"{func_prefix} dfs-and-similar\n"
                                    f"{func_prefix} all 1800", modal_words=False)

        elif func == "contest" or func == "contests":
            await send_contest(message)

        elif func == "tag" or func == "tags":
            await send_prob_tags(message)

        elif func == "logo" or func == "icon":
            await send_logo(message)

        else:
            await message.reply(f"[Codeforces]\n\n{Constants.cf_help_content}", modal_words=False)

    except Exception as e:
        await report_exception(message, 'Codeforces', traceback.format_exc(), repr(e))
