import difflib
import random
import re
import traceback

from pypinyin import pinyin, Style

from src.core.command import command, __commands__
from src.core.constants import Constants
from src.core.output_cached import get_cached_prefix
from src.core.tools import png2jpg, get_simple_qrcode
from src.module.message import RobotMessage, report_exception
from src.platform.cp.atcoder import AtCoder
from src.platform.cp.codeforces import Codeforces
from src.platform.cp.nowcoder import NowCoder
from src.platform.model import Contest

_fixed_reply = {
    "ping": "pong",
    "活着吗": "你猜",
    "help": Constants.merged_help_content
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


async def call_handle_message(message: RobotMessage):
    try:
        content = message.tokens

        if len(content) == 0 and not message.guild_public:
            return await message.reply(f"{match_key_words('')}")

        func = content[0].lower()
        for cmd in __commands__.keys():
            starts_with = cmd[-1] == '*' and func.startswith(cmd[:-1])
            if starts_with or cmd == func:
                original_command, execute_level, is_command, need_check_exclude = __commands__[cmd]

                if not is_command and message.guild_public:
                    continue

                if execute_level > 0:
                    Constants.log.info(f'{message.author_id} attempted {original_command.__name__}.')
                    if execute_level > message.user_permission_level:
                        raise PermissionError("权限不足，操作被拒绝" if func != "/去死" else "阿米诺斯")

                if need_check_exclude:
                    if (message.group_message is not None and
                            message.group_message.group_openid in Constants.config['exclude_group_id']):
                        return await message.reply('榜单功能被禁用，请联系bot管理员')
                try:
                    if starts_with:
                        name = cmd[:-1]
                        replaced = func.replace(name, '')
                        message.tokens = [name] + ([replaced] if replaced else []) + message.tokens[1:]
                    await original_command(message)
                except Exception as e:
                    await report_exception(message, f'Command<{original_command.__name__}>', traceback.format_exc(),
                                           repr(e))
                return

        if message.guild_public:
            return

        if '/' in func:
            await message.reply(f"其他指令还在开发中")
        else:
            await message.reply(f"{match_key_words(func)}")

    except Exception as e:
        await report_exception(message, 'Core', traceback.format_exc(), repr(e))


@command(tokens=list(_fixed_reply.keys()))
async def reply_fixed(message: RobotMessage):
    await message.reply(_fixed_reply.get(message.tokens[0][1:], ""), modal_words=False)


@command(tokens=['contest', 'contests', '比赛', '近日比赛', '最近的比赛'])
async def recent_contests(message: RobotMessage):
    queries = [AtCoder, Codeforces, NowCoder]
    if len(message.tokens) >= 2:
        closest_type = difflib.get_close_matches(message.tokens[1].lower(),
                                                 ["cf", "codeforces", "atc", "atcoder", "牛客", "nk", "nc", "nowcoder"])
        if len(closest_type) > 0:
            if closest_type[0] in ["cf", "codeforces"]:
                queries = [Codeforces]
            elif closest_type[0] in ["atc", "atcoder"]:
                queries = [AtCoder]
            else:
                queries = [NowCoder]
    if len(queries) == 1:
        await message.reply(f"正在查询近日 {queries[0].platform_name} 比赛，请稍等")
    else:
        await message.reply(f"正在查询近日比赛，请稍等")
    contests: list[Contest] = []

    for platform in queries:
        contests.extend(platform.get_contest_list(overwrite_tag=len(queries) > 1)[0])

    contests.sort(key=lambda c: c.start_time)

    info = '\n\n'.join([contest.format() for contest in contests])
    content = (f"近期比赛\n\n"
               f"{info}")

    await message.reply(content, modal_words=False)


@command(tokens=["qr", "qrcode", "二维码", "码"])
async def reply_qrcode(message: RobotMessage):
    content = re.sub(r'<@!\d+>', '', message.content).strip()
    content = re.sub(rf'{message.tokens[0]}', '', content, count=1).strip()
    if len(content) == 0:
        await message.reply("请输入要转化为二维码的内容")
        return

    cached_prefix = get_cached_prefix('QRCode-Generator')
    qr_img = get_simple_qrcode(content)
    qr_img.save(f"{cached_prefix}.png")

    await message.reply("生成了一个二维码", png2jpg(f"{cached_prefix}.png"))
