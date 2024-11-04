import difflib
import json
import random

import re
import traceback
from typing import Tuple

from utils.interact import RobotMessage
from utils.tools import report_exception, fetch_json, format_timestamp, format_timestamp_diff, check_is_int, get_today_start_timestamp, get_week_start_timestamp

__cf_version__ = "v2.1.1"

__cf_help_content__ = """/cf info [handle]: 获取用户名为 handle 的 Codeforces 基础用户信息.
/cf recent [handle] (count): 获取用户名为 handle 的 Codeforces 最近 count 发提交，count 默认为 5.
/cf pick [标签|all] (难度) (New): 从 Codeforces 上随机选题. 标签中间不能有空格，支持模糊匹配. 难度为整数或一个区间，格式为xxx-xxx. 末尾加上 New 参数则会忽视 P1000A 以前的题.
/cf contest: 列出最近的 Codeforces 比赛.
/cf tags: 列出 Codeforces 上的所有题目标签."""


def get_prob_tags_all() -> list[str] | None:
    url = f"https://codeforces.com/api/problemset.problems"
    json_data = fetch_json(url)
    tags = []
    for problems in json_data['result']['problems']:
        for tag in problems['tags']:
            tags.append(tag.replace(" ", "-"))
    tags = list(set(tags))
    return tags


async def get_prob_filter_tag(message: RobotMessage, tag_needed: str,
                              limit: str = None, newer: bool = False) -> dict | None:
    if tag_needed == "all":
        url = f"https://codeforces.com/api/problemset.problems"
    else:
        all_tags = get_prob_tags_all()
        if all_tags is None:
            return None

        # 模糊匹配
        if tag_needed not in all_tags:
            closet_tag = difflib.get_close_matches(tag_needed, all_tags)
            if len(closet_tag) == 0:
                return None
            tag_needed = closet_tag[0]
            await message.reply(f"最佳匹配 Tag: {tag_needed}")

        now_tag = tag_needed.replace("-", " ")
        url = f"https://codeforces.com/api/problemset.problems?tags={now_tag}"

    json_data = fetch_json(url)

    min_point = 0
    max_point = 0
    if limit is not None:
        if "-" in limit:
            [min_point, max_point] = list(map(int, limit.split("-")))
        else:
            min_point = max_point = int(limit)

    filtered_data = json_data['result']['problems']
    if limit is not None:
        filtered_data = [prob for prob in json_data['result']['problems']
                         if 'rating' in prob and min_point <= prob['rating'] <= max_point]
    if newer:
        filtered_data = [prob for prob in filtered_data if prob['contestId'] >= 1000]

    return random.choice(filtered_data)


def get_user_info(handle: str) -> Tuple[str | None, str | None]:
    url = f"https://codeforces.com/api/user.info?handles={handle}"
    json_data = fetch_json(url, throw=False)

    if json_data['status'] != "OK" or len(json_data['result']) == 0:
        return None, None

    result = json_data['result'][-1]
    sections = []

    # 归属地
    belong, home, name = [], [], []
    if 'firstName' in result:
        name.append(result['firstName'])
    if 'lastName' in result:
        name.append(result['lastName'])
    if len(name) > 0:
        home.append(' '.join(name))
    if 'city' in result:
        home.append(result['city'])
    if 'country' in result:
        home.append(result['country'])
    if len(home) > 0:
        belong.append(', '.join(home))
    if 'organization' in result:
        belong.append(f"来自 {result['organization']}")
    if len(belong) > 0:
        sections.append('\n'.join(belong))

    # 平台上的信息
    rating = "0 Unrated"
    if 'rating' in result:
        rating = (f"{result['rating']} {result['rank'].capitalize()} "
                  f"(max. {result['maxRating']} {result['maxRank']})")
    platform = (f"比赛Rating: {rating}\n"
                f"贡献: {result['contribution']}\n"
                f"粉丝: {result['friendOfCount']}")
    sections.append(platform)

    return '\n\n'.join(sections), result.get('titlePhoto')


def format_verdict(verdict: str, passed_count: int) -> str:
    verdict = verdict.replace("_", " ").capitalize()
    if verdict == "Ok":
        return "Accepted"
    elif verdict == "Skipped" or verdict == "Compilation error":
        return verdict
    elif verdict == "Challenged":
        return "Hacked"
    elif verdict == "Testing":
        return f"Running on test {passed_count + 1}"
    else:
        return f"{verdict} on test {passed_count + 1}"


def format_contest_name(name: str) -> str:
    # aaa.bbb -> aaaBbb
    return re.sub(r'(\w+)\.(\w+)', lambda m: m.group(1) + m.group(2).capitalize(), name)


def get_user_last_contest(handle: str) -> str:
    url = f"https://codeforces.com/api/user.rating?handle={handle}"
    json_data = fetch_json(url)

    if json_data['status'] != "OK":
        return "用户不存在"

    result = list(json_data['result'])
    contest_count = len(result)
    if contest_count == 0:
        return "还未参加过 Rated 比赛"

    last = result[-1]
    symbol = "" if (last['newRating'] - last['oldRating'] <= 0) else "+"
    info = (f"Rated 比赛数: {contest_count}\n"
            f"最近一次比赛: {format_contest_name(last['contestName'])}\n"
            f"比赛id: {last['contestId']}\n"
            f"位次: {last['rank']}\n"
            f"Rating变化: {symbol}{last['newRating'] - last['oldRating']}")

    return info


def get_user_last_submit(handle: str, count: int = 5) -> str:
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count={count}"
    json_data = fetch_json(url)

    if json_data['status'] != "OK":
        return "用户不存在"

    result = list(json_data['result'])
    submit_len = len(result)
    if submit_len == 0:
        return "还未提交过题目"

    info = f"最近{count}发提交:"
    for submit in result:
        verdict = format_verdict(submit['verdict'], submit['passedTestCount']) if 'verdict' in submit else "In queue"
        points = f" *{int(submit['problem']['rating'])}" if 'rating' in submit['problem'] else ""
        time = f" {submit['timeConsumedMillis']}ms" if 'timeConsumedMillis' in submit else ""
        info += (f"\n[{submit['id']}] {verdict} "
                 f"P{submit['problem']['contestId']}{submit['problem']['index']}{points}{time} "
                 f"{format_timestamp(submit['creationTimeSeconds'])}")

    return info


def get_user_submit_sums(handle: str) -> tuple[int, int, int]:
    url = f"https://codeforces.com/api/user.status?handle={handle}"
    json_data = fetch_json(url)

    if json_data['status'] != "OK":
        return -1, -1, -1

    result = list(json_data['result'])
    submit_len = len(result)
    if submit_len == 0:
        return 0, 0, 0

    total_set, weekly_set, daily_set = set(), set(), set()
    week_start_time, today_start_time = get_week_start_timestamp(), get_today_start_timestamp()
    for submit in result:
        if submit['verdict'] != "OK":
            continue
        current_prob = f"{submit['problem'].get('contestId')}-{submit['problem'].get('index')}"
        total_set.add(current_prob)
        if submit['creationTimeSeconds'] >= week_start_time:
            weekly_set.add(current_prob)
        if submit['creationTimeSeconds'] >= today_start_time:
            daily_set.add(current_prob)

    return len(total_set), len(weekly_set), len(daily_set)


def format_contest(contest: dict) -> str:
    duration = str(contest['durationSeconds'] // 3600) + " 小时"
    if contest['durationSeconds'] % 3600 > 0:
        duration += " " + str(contest['durationSeconds'] % 3600 // 60) + " 分钟"
    phase = format_timestamp_diff(contest['relativeTimeSeconds'])
    if contest['phase'] == 'CODING':
        phase = "正在比赛中"
    elif contest['phase'] == 'PENDING_SYSTEM_TEST':
        phase = "正在等待重测"
    elif contest['phase'] == 'SYSTEM_TEST':
        phase = "正在重测中"
    return (f"[{contest['id']}] {format_contest_name(contest['name'])}\n"
            f"{phase}, "
            f"{format_timestamp(contest['startTimeSeconds'])}\n"
            f"持续 {duration}, {contest['type']}赛制")


def get_recent_contests() -> str:
    url = "https://codeforces.com/api/contest.list"
    json_data = fetch_json(url)

    if json_data['status'] != "OK":
        return "查询异常"

    if len(json_data['result']) == 0:
        return "最近没有比赛"

    result = list(json_data['result'])

    limit = len(result) - 1
    for i, contest in enumerate(result):
        if contest['phase'] == 'FINISHED':
            limit = i - 1
            break

    unfinished_contests = result[limit::-1]  # 按日期升序排列
    info = ""
    for contest in unfinished_contests:
        info += format_contest(contest) + "\n\n"

    last_finished_contest = result[limit + 1]
    info += "上一场已结束的比赛:\n" + format_contest(last_finished_contest)

    return info


async def send_user_info(message: RobotMessage, handle: str):
    await message.reply(f"正在查询 {handle} 的 Codeforces 平台信息，请稍等")

    info, avatar = get_user_info(handle)

    if info is None:
        content = (f"[Codeforces] {handle}\n\n"
                   f"用户不存在")
    else:
        last_contest = get_user_last_contest(handle)
        last_submit = get_user_last_submit(handle)
        total_sums, weekly_sums, daily_sums = get_user_submit_sums(handle)
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

    info, _ = get_user_info(handle)

    if info is None:
        content = (f"[Codeforces] {handle}\n\n"
                   f"用户不存在")
    else:
        last_submit = get_user_last_submit(handle, count)
        content = (f"[Codeforces] {handle}\n\n"
                   f"{last_submit}")

    await message.reply(content, modal_words=False)


async def send_prob_tags(message: RobotMessage):
    await message.reply("正在查询 Codeforces 平台的所有问题标签，请稍等")

    prob_tags = get_prob_tags_all()

    if prob_tags is None:
        content = "查询异常"
    else:
        content = "\n[Codeforces] 问题标签:\n"
        for tag in prob_tags:
            content += "\n" + tag

    await message.reply(content, modal_words=False)


async def send_prob_filter_tag(message: RobotMessage, tag: str, limit: str = None, newer: bool = False) -> bool:
    await message.reply("正在随机选题，请稍等")

    chosen_prob = await get_prob_filter_tag(message, tag, limit, newer)

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

    info = get_recent_contests()

    content = (f"[Codeforces] 近期比赛\n\n"
               f"{info}")

    await message.reply(content, modal_words=False)


async def send_logo(message: RobotMessage):
    await message.reply("[Codeforces] 网站当前的图标",
                        img_url="https://codeforces.org/s/24321/images/codeforces-sponsored-by-ton.png")


async def reply_cf_request(message: RobotMessage):
    try:
        content = re.sub(r'<@!\d+>', '', message.content).strip().split()
        if len(content) < 2:
            await message.reply(f"[Codeforces]\n\n{__cf_help_content__}", modal_words=False)
            return

        func = content[1]

        if func == "info":
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

        elif func == "pick":
            if not await send_prob_filter_tag(
                    message=message,
                    tag=content[2],
                    limit=content[3] if len(content) >= 4 and content[3] != "new" else None,
                    newer=content[3] == "new" if len(content) == 4 else (
                    content[4] == "new" if len(content) == 5 else False)
            ):
                await message.reply("请输入正确的指令格式，如:\n\n"
                                    "/cf pick dp 1700-1900 new\n"
                                    "/cf pick dfs-and-similar\n"
                                    "/cf pick all 1800", modal_words=False)

        elif func == "contest":
            await send_contest(message)

        elif func == "tags":
            await send_prob_tags(message)

        elif func == "logo":
            await send_logo(message)

        else:
            await message.reply(f"[Codeforces]\n\n{__cf_help_content__}", modal_words=False)

    except Exception as e:
        await report_exception(message, 'Codeforces', traceback.format_exc(), repr(e))
