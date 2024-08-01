import difflib
import re
import time
from typing import Any, Tuple

import httpx

from utils.interact import *


async def get_json(url: str) -> Any:
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.77 Safari/537.36",
        'Connection': 'close'
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url=url, headers=headers)
        json_data = response.json()
        return json_data
    except:
        return -1


async def get_prob_tags_all() -> list[str] | None:
    url = f"https://codeforces.com/api/problemset.problems"
    json_data = await get_json(url)
    if json_data == -1:
        return None
    tags = []
    for problems in json_data['result']['problems']:
        for tag in problems['tags']:
            tags.append(tag.replace(" ", "-"))
    tags = list(set(tags))
    return tags


async def get_prob_filter_tag(message: RobotMessage, tag_needed: str,
                              limit: str = None, newer: bool = False) -> Tuple[str, str] | None:
    if tag_needed == "all":
        url = f"https://codeforces.com/api/problemset.problems"
    else:
        all_tags = await get_prob_tags_all()
        if all_tags is None:
            return None

        # 模糊匹配
        if tag_needed not in all_tags:
            closet_tag = difflib.get_close_matches(tag_needed, all_tags, 1, cutoff=0.6)
            if len(closet_tag) == 0:
                return None
            tag_needed = closet_tag[0]
            await message.reply(f"最佳匹配 Tag: {tag_needed}")

        now_tag = tag_needed.replace("-", " ")
        url = f"https://codeforces.com/api/problemset.problems?tags={now_tag}"

    json_data = await get_json(url)
    if json_data == -1:
        return None

    min_point = 0
    max_point = 0
    if limit is not None:
        if "-" in limit:
            [min_point, max_point] = list(map(int, limit.split("-")))
        else:
            min_point = max_point = int(limit)

    filtered_data = [prob for prob in json_data['result']['problems'] if
                     'rating' in prob and min_point <= prob['rating'] <= max_point] if limit is not None else \
        json_data['result']['problems']
    filtered_data = [prob for prob in filtered_data if prob['contestId'] >= 1000] if newer else filtered_data
    return tag_needed, random.choice(filtered_data)


def rating_type(rating: int) -> str:
    if rating < 1200:
        return "Newbie"
    if rating < 1400:
        return 'Pupil'
    if rating < 1600:
        return 'Specialist'
    if rating < 1900:
        return 'Expert'
    if rating < 2100:
        return 'Candidate master'
    if rating < 2300:
        return 'International Master'
    if rating < 2400:
        return 'Master'
    if rating < 2600:
        return 'Grandmaster'
    if rating < 3000:
        return 'International Grandmaster'
    else:
        return 'Legendary Grandmaster'


async def get_user_rating(handle: str) -> str:
    url = f"https://codeforces.com/api/user.rating?handle={handle}"
    json_data = await get_json(url)
    if json_data == -1:
        return "查询异常"
    json_data = dict(json_data)

    if json_data['status'] == "OK":
        json_data = json_data['result']
        contest_len = len(json_data)
        if contest_len == 0:
            return "还未进行过比赛"
        final_contest = json_data[-1]
        now_rating = int(final_contest['newRating'])
        return f"{now_rating} {rating_type(now_rating)}"
    else:
        return "用户不存在"


def format_verdict(verdict: str, passed_count: int) -> str:
    if verdict == "OK":
        return "ACCEPTED"
    else:
        return f"{verdict} on test {passed_count + 1}"


async def get_user_last_submit(handle: str) -> str:
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=3"
    json_data = await get_json(url)
    if json_data == -1:
        return "查询异常"
    json_data = dict(json_data)

    if json_data['status'] == "OK":
        json_data = list(json_data['result'])
        submit_len = len(json_data)
        if submit_len == 0:
            return "还未提交过题目"
        ans = ""
        for submit in json_data:
            ans += f"""
[{submit['id']}] {format_verdict(submit['verdict'], submit['passedTestCount'])}
P{submit['problem']['contestId']}{submit['problem']['index']} at {time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(int(submit['creationTimeSeconds'])))}"""
        return ans
    else:
        return "用户不存在"


async def send_user_info(message: RobotMessage, handle: str):
    rating = await get_user_rating(handle)
    last_submit = await get_user_last_submit(handle)

    content = f"""
[Codeforces] {handle}

Rating: {rating}

Recent Submit:{last_submit}"""

    await message.reply(content)


async def send_prob_tags(message: RobotMessage):
    prob_tags = await get_prob_tags_all()

    if prob_tags is None:
        content = "查询异常"
    else:
        content = "\n[Codeforces] Problem Tags:\n"
        for tag in prob_tags:
            content += "\n" + tag

    await message.reply(content)


async def send_prob_filter_tag(message: RobotMessage, tag: str, limit: str = None, newer: bool = False):
    chosen_prob = await get_prob_filter_tag(message, tag, limit, newer)

    if chosen_prob is None:
        content = "查询异常"
    else:
        content = f"""
[Codeforces] Problem Choose

Tag: {chosen_prob[0]}

Link: [codeforces] /contest/{chosen_prob[1]['contestId']}/problem/{chosen_prob[1]['index']}

Problem: P{chosen_prob[1]['contestId']}{chosen_prob[1]['index']} {chosen_prob[1]['name']}"""

        if 'rating' in chosen_prob[1]:
            content += "\n\nDifficulty: *" + str(chosen_prob[1]['rating'])

    await message.reply(content)


async def reply_cf_request(message: RobotMessage):
    content = re.sub(r'<@!\d+>', '', message.content).strip().split()
    if content[1] == "info":
        if len(content) != 3:
            await message.reply("请输入正确的指令格式，如 /cf info jiangly")
            return
        await send_user_info(message, content[2])
    elif content[1] == "prob":
        if content[2] == "pick":
            await send_prob_filter_tag(message, content[3],
                                       content[4] if len(content) >= 5 and content[4] != "new" else None,
                                       content[4] == "new" if len(content) == 5 else (
                                           content[5] == "new" if len(content) == 6 else False))
        elif content[2] == "tags":
            await send_prob_tags(message)
        else:
            await message.reply("请输入正确的指令格式，如:\n\n"
                                "/cf prob pick dp 1700-1900\n"
                                "/cf prob pick dfs-and-similar\n"
                                "/cf prob pick all 1800\n"
                                "/cf prob tags")
    else:
        await message.reply("目前仅支持 info 和 prob 指令\n\ninfo:\n/cf info [用户名]\n\n"
                            "prob:\n/cf prob pick [题目tag/all] [难度/可留空]\n"
                            "/cf prob tags")
