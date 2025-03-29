import random
import re
import traceback

from pypinyin import pinyin, Style
from thefuzz import process

from src.core.command import command, __commands__, PermissionLevel
from src.core.constants import Constants
from src.core.exception import UnauthorizedError
from src.core.output_cached import get_cached_prefix
from src.core.tools import png2jpg, get_simple_qrcode, check_intersect, get_today_timestamp_range
from src.module.message import RobotMessage, MessageType
from src.platform.cp.atcoder import AtCoder
from src.platform.cp.codeforces import Codeforces
from src.platform.cp.nowcoder import NowCoder

_fixed_reply = {
    "ping": "pong",
    "活着吗": "你猜捏",
    "似了吗": "？",
    "死了吗": "？？？",
    "help": Constants.merged_help_content,
    "帮助": Constants.merged_help_content
}


def match_key_words(content: str) -> str:
    random.shuffle(Constants.key_words)  # 多个关键词时的处理
    for asks, answers in Constants.key_words:
        for ask in asks:
            ask_pinyin = ''.join(word[0] for word in pinyin(ask, Style.NORMAL))
            ctx_pinyin = ''.join(word[0] for word in pinyin(content.lower(), Style.NORMAL))
            if ask_pinyin in ctx_pinyin:
                return random.choice(answers)
    return random.choice(["你干嘛", "干什么", "咋了", "how", "what"])


def call_handle_message(message: RobotMessage):
    """分发消息处理"""
    try:
        content = message.tokens

        if len(content) == 0 and not message.is_guild_public():
            return message.reply(f"{match_key_words('')}")

        func = content[0].lower()
        for cmd in __commands__:
            starts_with = cmd[-1] == '*' and func.startswith(cmd[:-1])
            if starts_with or cmd == func:
                original_command, execute_level, is_command, need_to_check_exclude = __commands__[cmd]

                if not is_command and message.is_guild_public():
                    continue

                if message.user_permission_level < execute_level:
                    Constants.log.info(f'{message.author_id} attempted to call {original_command.__name__} but failed.')
                    raise UnauthorizedError("权限不足，操作被拒绝" if func != "/去死" else "阿米诺斯")

                if need_to_check_exclude and (message.message_type == MessageType.GROUP and
                                              message.message.group_openid in Constants.config['exclude_group_id']):
                    Constants.log.info(f'{message.message.group_openid} was banned to call {original_command.__name__}.')
                    raise UnauthorizedError("榜单功能被禁用")
                try:
                    if starts_with:
                        name = cmd[:-1]
                        replaced = func.replace(name, '')
                        message.tokens = [name] + ([replaced] if replaced else []) + message.tokens[1:]
                    original_command(message)
                except Exception as e:
                    message.report_exception(f'Command<{original_command.__name__}>', traceback.format_exc(), e)
                return

        # 如果是频道无at消息可能是发错了或者并非用户希望的处理对象
        if message.is_guild_public():
            return

        if '/' in func:
            message.reply("其他指令还在开发中")
        else:
            message.reply(f"{match_key_words(func)}")

    except Exception as e:
        message.report_exception('Core', traceback.format_exc(), e)


@command(tokens=list(_fixed_reply.keys()))
def reply_fixed(message: RobotMessage):
    message.reply(_fixed_reply.get(message.tokens[0][1:], ""), modal_words=False)


@command(tokens=['contest', 'contests', '比赛', '近日比赛', '最近的比赛', '今天比赛', '今天的比赛', '今日比赛', '今日的比赛'])
def recent_contests(message: RobotMessage):
    query_today = message.tokens[0] in ['/今天比赛', '/今天的比赛', '/今日比赛', '/今日的比赛']
    if len(message.tokens) >= 3 and message.tokens[1] == 'today':
        query_today = True
        message.tokens[1] = message.tokens[2]
    queries = [AtCoder, Codeforces, NowCoder]
    if len(message.tokens) >= 2:
        if message.tokens[1] == 'today':
            query_today = True
        else:
            closest_type = process.extract(message.tokens[1].lower(), [
                "cf", "codeforces", "atc", "atcoder", "牛客", "nk", "nc", "nowcoder"], limit=1)[0]
            if closest_type[1] >= 60:
                if closest_type[0] in ["cf", "codeforces"]:
                    queries = [Codeforces]
                elif closest_type[0] in ["atc", "atcoder"]:
                    queries = [AtCoder]
                else:
                    queries = [NowCoder]
    tip_time_range = '今日' if query_today else '近期'
    if len(queries) == 1:
        message.reply(f"正在查询{tip_time_range} {queries[0].platform_name} 比赛，请稍等")
    else:
        message.reply(f"正在查询{tip_time_range}比赛，请稍等")

    upcoming_contests, running_contests, finished_contests = [], [], []
    for platform in queries:
        upcoming, running, finished = platform.get_contest_list(overwrite_tag=len(queries) > 1)
        upcoming_contests.extend(upcoming)
        running_contests.extend(running)
        finished_contests.extend(finished)

    upcoming_contests.sort(key=lambda c: c.start_time)
    running_contests.sort(key=lambda c: c.start_time)
    finished_contests.sort(key=lambda c: c.start_time)

    if query_today:
        upcoming_contests = [contest for contest in upcoming_contests if check_intersect(
            range1=get_today_timestamp_range(),
            range2=(contest.start_time, contest.start_time + contest.duration)
        )]
        running_contests = [contest for contest in running_contests if check_intersect(
            range1=get_today_timestamp_range(),
            range2=(contest.start_time, contest.start_time + contest.duration)
        )]
        finished_contests = [contest for contest in finished_contests if check_intersect(
            range1=get_today_timestamp_range(),
            range2=(contest.start_time, contest.start_time + contest.duration)
        )]

    if len(upcoming_contests) == 0 and len(running_contests) == 0 and len(finished_contests) == 0:
        content = f"{tip_time_range}无比赛"
    else:
        sections = []
        if len(running_contests) > 0:
            sections.append(">> 正在进行的比赛 >>\n\n" + ('\n\n'.join([contest.format() for contest in running_contests])))
        if len(upcoming_contests) > 0:
            sections.append(">> 即将开始的比赛 >>\n\n" + ('\n\n'.join([contest.format() for contest in upcoming_contests])))
        if len(finished_contests) > 0:
            sections.append(">> 已结束的比赛 >>\n\n" + ('\n\n'.join([contest.format() for contest in finished_contests])))
        info = '\n\n'.join(sections)
        content = (f"{tip_time_range}比赛\n\n"
                   f"{info}")

    message.reply(content, modal_words=False)


@command(tokens=["qr", "qrcode", "二维码", "码"])
def reply_qrcode(message: RobotMessage):
    content = re.sub(r'<@!\d+>', '', message.content).strip()
    content = re.sub(rf'{message.tokens[0]}', '', content, count=1).strip()
    if len(content) == 0:
        message.reply("请输入要转化为二维码的内容")
        return

    cached_prefix = get_cached_prefix('QRCode-Generator')
    qr_img = get_simple_qrcode(content)
    qr_img.save(f"{cached_prefix}.png")

    message.reply("生成了一个二维码", png2jpg(f"{cached_prefix}.png"))
