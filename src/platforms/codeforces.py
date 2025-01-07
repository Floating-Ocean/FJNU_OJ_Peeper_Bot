import difflib
import random
import re

from src.core.tools import fetch_json, format_timestamp, get_week_start_timestamp, get_today_start_timestamp, \
    format_timestamp_diff, format_seconds
from src.modules.message import RobotMessage
from src.platforms.platform import Platform, ContestDict


class Codeforces(Platform):
    logo_url = "https://codeforces.org/s/24321/images/codeforces-sponsored-by-ton.png"

    @staticmethod
    def get_prob_tags_all() -> list[str] | None:
        url = f"https://codeforces.com/api/problemset.problems"
        json_data = fetch_json(url)
        tags = []
        for problems in json_data['result']['problems']:
            for tag in problems['tags']:
                tags.append(tag.replace(" ", "-"))
        tags = list(set(tags))
        return tags

    @staticmethod
    async def get_prob_filter_tag(message: RobotMessage, tag_needed: str,
                                  limit: str = None, newer: bool = False) -> dict | int:
        min_point, max_point = 0, 0
        if limit is not None:
            # 检查格式是否为 dddd-dddd 或 dddd
            if not re.match("^[0-9]+-[0-9]+$", limit) or not re.match("^[0-9]+$", limit):
                return -3
            # 检查范围数值是否合法
            field_validate = True
            if "-" in limit:
                field_validate &= 7 <= len(limit) <= 9
                [min_point, max_point] = list(map(int, limit.split("-")))
            else:
                field_validate &= 3 <= len(limit) <= 4
                min_point = max_point = int(limit)
            if not field_validate:
                return 0

        if tag_needed == "all":
            url = f"https://codeforces.com/api/problemset.problems"
        else:
            all_tags = Codeforces.get_prob_tags_all()
            if all_tags is None:
                return -1
            if tag_needed not in all_tags:  # 模糊匹配
                closet_tag = difflib.get_close_matches(tag_needed, all_tags)
                if len(closet_tag) == 0:
                    return -2
                tag_needed = closet_tag[0]
                await message.reply(f"标签最佳匹配: {tag_needed}")
            now_tag = tag_needed.replace("-", " ")
            url = f"https://codeforces.com/api/problemset.problems?tags={now_tag}"

        json_data = fetch_json(url)
        filtered_data = json_data['result']['problems']
        if limit is not None:
            filtered_data = [prob for prob in json_data['result']['problems']
                             if 'rating' in prob and min_point <= prob['rating'] <= max_point]
        if newer:
            filtered_data = [prob for prob in filtered_data if prob['contestId'] >= 1000]

        return random.choice(filtered_data) if len(filtered_data) > 0 else 0

    @staticmethod
    def get_user_info(handle: str) -> tuple[str | None, str | None]:
        url = f"https://codeforces.com/api/user.info?handles={handle}"
        json_data = fetch_json(url, throw=False)

        if json_data is None or json_data['status'] != "OK" or len(json_data['result']) == 0:
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
            if len(result['organization']) == 0:  # meme
                result['organization'] = '地球'
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

    @staticmethod
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

    @staticmethod
    def format_contest_name(name: str) -> str:
        # aaa.bbb -> aaaBbb
        return re.sub(r'(\w+)\.(\w+)', lambda m: m.group(1) + m.group(2).capitalize(), name)

    @staticmethod
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
                f"最近一次比赛: {Codeforces.format_contest_name(last['contestName'])}\n"
                f"比赛编号: {last['contestId']}\n"
                f"位次: {last['rank']}\n"
                f"Rating 变化: {symbol}{last['newRating'] - last['oldRating']}")

        return info

    @staticmethod
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
            verdict = Codeforces.format_verdict(submit['verdict'], submit['passedTestCount']) \
                if 'verdict' in submit else "In queue"
            points = f" *{int(submit['problem']['rating'])}" if 'rating' in submit['problem'] else ""
            time = f" {submit['timeConsumedMillis']}ms" if 'timeConsumedMillis' in submit else ""
            info += (f"\n[{submit['id']}] {verdict} "
                     f"P{submit['problem']['contestId']}{submit['problem']['index']}{points}{time} "
                     f"{format_timestamp(submit['creationTimeSeconds'])}")

        return info

    @staticmethod
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

    @staticmethod
    def format_contest(contest: dict) -> str:
        phase = format_timestamp_diff(contest['relativeTimeSeconds'])
        if contest['phase'] == 'CODING':
            phase = "正在比赛中"
        elif contest['phase'] == 'PENDING_SYSTEM_TEST':
            phase = "正在等待重测"
        elif contest['phase'] == 'SYSTEM_TEST':
            phase = "正在重测中"
        return (f"[{contest['id']}] {Codeforces.format_contest_name(contest['name'])}\n"
                f"{phase}, "
                f"{format_timestamp(contest['startTimeSeconds'])}\n"
                f"持续 {format_seconds(contest['durationSeconds'])}, {contest['type']}赛制")

    @staticmethod
    def get_contest_list_all() -> list[dict] | None:
        url = "https://codeforces.com/api/contest.list"
        json_data = fetch_json(url)

        if json_data['status'] != "OK":
            return None

        if len(json_data['result']) == 0:
            return []

        return list(json_data['result'])

    @staticmethod
    def get_contest_list() -> list[ContestDict] | None:
        result = Codeforces.get_contest_list_all()

        if result is None:
            return None

        return [{
            'start_time': contest['startTimeSeconds'],
            'duration': contest['durationSeconds'],
            'platform': 'Codeforces',
            'name': contest['name'],
            'supplement': f"{contest['type']}赛制"
        } for contest in result if contest['phase'] == 'BEFORE']

    @staticmethod
    def get_recent_contests() -> str:
        result = Codeforces.get_contest_list_all()

        if result is None:
            return "查询异常"

        if len(result) == 0:
            return "最近没有比赛"

        limit = len(result) - 1
        for i, contest in enumerate(result):
            if contest['phase'] == 'FINISHED':
                limit = i - 1
                break

        unfinished_contests = result[limit::-1]  # 按日期升序排列
        info = ""
        for contest in unfinished_contests:
            info += Codeforces.format_contest(contest) + "\n\n"

        last_finished_contest = result[limit + 1]
        info += "上一场已结束的比赛:\n" + Codeforces.format_contest(last_finished_contest)

        return info
