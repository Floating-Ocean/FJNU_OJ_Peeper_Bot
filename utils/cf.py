import difflib
import re
import time
from typing import Any, Tuple

import requests

from utils.interact import *


async def get_json(url: str) -> Any:
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.77 Safari/537.36",
        'Connection': 'close'
    }
    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise ConnectionError(f"Filed to connect {url}, code {response.status_code}.")


async def get_prob_tags_all() -> list[str] | None:
    url = f"https://codeforces.com/api/problemset.problems"
    json_data = await get_json(url)
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


async def get_user_info(handle: str) -> Tuple[str, str | None]:
    url = f"https://codeforces.com/api/user.info?handles={handle}"
    json_data = await get_json(url)

    if json_data['status'] != "OK":
        return "用户不存在", None

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
    if verdict == "OK":
        return "ACCEPTED"
    else:
        return f"{verdict} on test {passed_count + 1}"


async def get_user_last_contest(handle: str) -> str:
    url = f"https://codeforces.com/api/user.rating?handle={handle}"
    json_data = await get_json(url)

    if json_data['status'] != "OK":
        return "用户不存在"

    result = list(json_data['result'])
    contest_count = len(result)
    if contest_count == 0:
        return "还未参加过 Rated 比赛"

    last = result[-1]
    info = (f"Rated 比赛数: {contest_count}\n"
            f"最近一次比赛: {last['contestName']}\n"
            f"比赛id: {last['contestId']}\n"
            f"位次: {last['rank']}\n"
            f"Rating变化: {last['newRating'] - last['oldRating']}")

    return info


async def get_user_last_submit(handle: str) -> str:
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=5"
    json_data = await get_json(url)

    if json_data['status'] != "OK":
        return "用户不存在"

    result = list(json_data['result'])
    submit_len = len(result)
    if submit_len == 0:
        return "还未提交过题目"

    info = "最近几次提交:\n"
    for submit in result:
        info += (f"[{submit['id']}] {format_verdict(submit['verdict'], submit['passedTestCount'])} "
                 f"P{submit['problem']['contestId']}{submit['problem']['index']} at "
                 f"{time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(int(submit['creationTimeSeconds'])))}\n")

    return info


async def send_user_info(message: RobotMessage, handle: str):
    await message.reply(f"正在查询 {handle} 的 Codeforces 平台信息，请稍等")

    info, avatar = await get_user_info(handle)
    last_contest = await get_user_last_contest(handle)
    last_submit = await get_user_last_submit(handle)

    content = (f"[Codeforces] {handle}\n\n"
               f"{info}\n\n"
               f"{last_contest}\n\n"
               f"{last_submit}")

    await message.reply(content, img_url=avatar)


async def send_prob_tags(message: RobotMessage):
    await message.reply("正在查询 Codeforces 平台的所有问题标签，请稍等")

    prob_tags = await get_prob_tags_all()

    if prob_tags is None:
        content = "查询异常"
    else:
        content = "\n[Codeforces] 问题标签:\n"
        for tag in prob_tags:
            content += "\n" + tag

    await message.reply(content)


async def send_prob_filter_tag(message: RobotMessage, tag: str, limit: str = None, newer: bool = False):
    await message.reply("正在随机选题，请稍等")

    chosen_prob = await get_prob_filter_tag(message, tag, limit, newer)

    if chosen_prob is None:
        content = "查询异常"
    else:
        tags = ', '.join(chosen_prob['tags'])
        content = (f"[Codeforces] 随机选题\n\n"
                   f"P{chosen_prob['contestId']}{chosen_prob['index']} {chosen_prob['name']}\n\n"
                   f"链接: [codeforces] /contest/{chosen_prob['contestId']}/problem/{chosen_prob['index']}\n"
                   f"标签: {tags}")

        if 'rating' in chosen_prob:
            content += f"\n难度: *{chosen_prob['rating']}"

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
