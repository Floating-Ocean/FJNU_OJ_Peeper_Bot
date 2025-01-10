import difflib
import random
import re
import time

from src.core.tools import fetch_json, format_timestamp, get_week_start_timestamp, get_today_start_timestamp, \
    format_timestamp_diff, format_seconds
from src.lib.cf_rating_calc import PredictResult, Contestant, predict
from src.modules.message import RobotMessage
from src.platforms.platform import Platform, Contest


class Codeforces(Platform):
    logo_url = "https://codeforces.org/s/24321/images/codeforces-sponsored-by-ton.png"
    rated_ranks = {
        (-float('inf'), 1200): 'N',  # Newbie
        (1200, 1400): 'P',           # Pupil
        (1400, 1600): 'S',           # Specialist
        (1600, 1900): 'E',           # Expert
        (1900, 2100): 'CM',          # Candidate Master
        (2100, 2300): 'M',           # Master
        (2300, 2400): 'IM',          # International Master
        (2400, 2600): 'GM',          # Grandmaster
        (2600, 3000): 'IGM',         # International Grandmaster
        (3000, 4000): 'LGM',         # Legendary Grandmaster
        (4000, float('inf')): 'T'    # Tourist
    }

    @staticmethod
    def _api(api: str, **kwargs) -> dict | int:
        """传递参数构造payload，添加首尾下划线可避免与关键词冲突"""
        url = f"https://codeforces.com/api/{api}"
        if len(kwargs) > 0:
            payload = '&'.join([f'{key.strip("_")}={val}' for key, val in kwargs.items()])
            url += f"?{payload}"
        json_data = fetch_json(url, throw=False)

        if isinstance(json_data, int) or json_data['status'] != "OK":
            if isinstance(json_data, int) and json_data != 400:
                return -1
            return 0

        return json_data['result']

    @staticmethod
    def _format_verdict(verdict: str, passed_count: int) -> str:
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
    def _format_contest_name(name: str) -> str:
        """aaa.bbb -> aaaBbb"""
        return re.sub(r'(\w+)\.(\w+)', lambda m: m.group(1) + m.group(2).capitalize(), name)

    @staticmethod
    def _format_rank_delta(old_rating: int, delta: int) -> str:
        old_rank = next((rank for (l, r), rank in Codeforces.rated_ranks.items() if l <= old_rating < r), 'N')
        new_rank = next((rank for (l, r), rank in Codeforces.rated_ranks.items() if l <= old_rating + delta < r), 'N')
        if old_rank == new_rank:
            return "段位无变化"
        else:
            return f"段位变化 {old_rank}->{new_rank}"

    @staticmethod
    def _format_standing(standing: dict, contest_id: str) -> str:
        participant_types = {
            "CONTESTANT": "参赛",
            "PRACTICE": "练习",
            "VIRTUAL": "虚拟参赛",
            "MANAGER": "管理比赛",
            "OUT_OF_COMPETITION": "打星参赛"
        }
        member_info = "以个人为单位"
        if 'teamId' in standing['party']:
            member_info = f"作为团队 {standing['party']['teamName']} 的一员"
        member_info += participant_types[standing['party']['participantType']]
        if standing['party']['ghost']:
            member_info += " (Ghost)"

        accepted_prob_count = len([prob for prob in standing['problemResults'] if 'bestSubmissionTimeSeconds' in prob])
        rejected_attempt_count = sum(prob['rejectedAttemptCount'] for prob in standing['problemResults'])
        submission_info = f"通过 {accepted_prob_count} 题" if accepted_prob_count > 0 else "暂无题目通过"
        submission_info += f"，包含 {rejected_attempt_count} 次失败尝试" if rejected_attempt_count > 0 else "，无失败尝试"

        contestant_info = f"位次 {standing['rank']}，总分 {standing['points']}，总罚时 {standing['penalty']}"
        hack_info = "Hack "
        hack_prop = []
        if standing['successfulHackCount'] > 0:
            hack_prop.append(Codeforces._format_int_delta(standing['successfulHackCount']))
        if standing['unsuccessfulHackCount'] > 0:
            hack_prop.append(Codeforces._format_int_delta(standing['unsuccessfulHackCount']))
        if len(hack_prop) > 0:
            hack_info += ':'.join(hack_prop)
            contestant_info += f"，{hack_info}"

        if standing['party']['participantType'] == 'PRACTICE':
            contestant_info = None

        if standing['party']['participantType'] == 'CONTESTANT':
            all_predictions = Codeforces.get_contest_predict(contest_id)
            if not isinstance(all_predictions, int) and standing['party']['members'][0]['handle'] in all_predictions:
                prediction = all_predictions[standing['party']['members'][0]['handle']]
                contestant_info += (f'\n表现分 {prediction.performance}，'
                                    f'预测变化 {Codeforces._format_int_delta(prediction.delta)}，'
                                    f'{Codeforces._format_rank_delta(prediction.rating, prediction.delta)}')

        return '\n'.join([section for section in [member_info, submission_info, contestant_info]
                          if section is not None])

    @staticmethod
    def _format_contest(contest: dict) -> str:
        phase = format_timestamp_diff(contest['relativeTimeSeconds'])
        if contest['phase'] == 'CODING':
            phase = "正在比赛中"
        elif contest['phase'] == 'PENDING_SYSTEM_TEST':
            phase = "正在等待重测"
        elif contest['phase'] == 'SYSTEM_TEST':
            phase = "正在重测中"
        return (f"[{contest['id']}] {Codeforces._format_contest_name(contest['name'])}\n"
                f"{phase}, "
                f"{format_timestamp(contest['startTimeSeconds'])}\n"
                f"持续 {format_seconds(contest['durationSeconds'])}, {contest['type']} 赛制")

    @staticmethod
    def _format_int_delta(delta: int) -> str:
        if delta >= 0:
            return f"+{delta}"
        else:
            return f"{delta}"

    @staticmethod
    def _adjust_old_ratings(contest_id: int, rating_changes: list) -> dict:
        """
        Adapted from carrot at
        https://github.com/meooow25/carrot/blob/master/carrot/src/background/cache/contests-complete.js

        Note: This a band-aid for CF's fake ratings (see GitHub #18).
        If CF tells us that a user had rating 0, we consider that the user is in fact unrated.
        This unfortunately means that a user who truly has rating 0 will be considered to have
        DEFAULT_RATING, but such cases are unlikely compared to the regular presence of unrated
        users.
        """
        if contest_id < 1360:  # FAKE_RATINGS_SINCE_CONTEST
            return {change['handle']: {'oldRating': change['oldRating'],
                                       'realChange': (change['oldRating'], change['newRating'])}
                    for change in rating_changes}
        else:
            def _adjust(old: int) -> int:
                return 1400 if old == 0 else old  # NEW_DEFAULT_RATING
            return {change['handle']: {'oldRating': _adjust(change['oldRating']),
                                       'realChange': (change['oldRating'], change['newRating'])}
                    for change in rating_changes}

    @staticmethod
    def _is_old_contest(standings: dict) -> bool:
        """
        Adapted from carrot at
        https://github.com/meooow25/carrot/blob/master/carrot/src/background/cache/contests-complete.js
        """
        days_since_contest_end = ((time.time() - standings['startTimeSeconds'] - standings['durationSeconds'])
                                  / (60 * 60 * 24))
        return days_since_contest_end > 3  # RATING_PENDING_MAX_DAYS

    @staticmethod
    def _get_predicted_prefs(standings: dict) -> dict[str, PredictResult] | None:
        """
        Adapted from carrot at
        https://github.com/meooow25/carrot/blob/master/carrot/src/background/cache/contests-complete.js
        """
        ratings = Codeforces._api('user.ratedList', activeOnly=True, contestId=standings['contest']['id'])
        if isinstance(ratings, int):
            return None
        ratings = {user['handle']: user['rating'] for user in ratings}

        is_edu_round = 'educational' in standings['contest']['name'].lower()
        rows = standings['rows']
        if is_edu_round:
            # For educational rounds, standings include contestants for whom the contest is not rated.
            rows = [row for row in standings['rows'] if
                    row['party']['members'][0]['handle'] in ratings and
                    row['party']['members'][0]['handle'] < 2100]  # EDU_ROUND_RATED_THRESHOLD

        contestants = [Contestant(
            handle=row['party']['members'][0]['handle'],
            points=row['points'],
            penalty=row['penalty'],
            rating=ratings[row['party']['members'][0]['handle']]
        ) for row in rows]

        return predict(contestants, True)

    @staticmethod
    def _get_final_prefs(standings: dict, old_ratings: dict) -> dict[str, PredictResult] | None:
        """
        Adapted from carrot at
        https://github.com/meooow25/carrot/blob/master/carrot/src/background/cache/contests-complete.js
        """
        rows = [row for row in standings['rows'] if
                row['party']['members'][0]['handle'] in old_ratings]

        contestants = [Contestant(
            handle=row['party']['members'][0]['handle'],
            points=row['points'],
            penalty=row['penalty'],
            rating=old_ratings[row['party']['members'][0]['handle']]['oldRating'],
            real_change=old_ratings[row['party']['members'][0]['handle']]['realChange']
        ) for row in rows]

        return predict(contestants, True)

    @staticmethod
    def get_prob_tags_all() -> list[str] | None:
        problems = Codeforces._api('problemset.problems')
        if isinstance(problems, int):
            return None

        tags = []
        for problem in problems['problems']:
            for tag in problem['tags']:
                tags.append(tag.replace(" ", "-"))
        tags = list(set(tags))
        return tags

    @staticmethod
    async def get_prob_filtered_by_tag(tag_needed: str, limit: str = None, newer: bool = False,
                                       on_tag_chosen=None) -> dict | int:
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
            problems = Codeforces._api('problemset.problems')
        else:
            all_tags = Codeforces.get_prob_tags_all()
            if all_tags is None:
                return -1
            if tag_needed not in all_tags:  # 模糊匹配
                closet_tag = difflib.get_close_matches(tag_needed, all_tags)
                if len(closet_tag) == 0:
                    return -2
                tag_needed = closet_tag[0]
                if on_tag_chosen is not None:
                    await on_tag_chosen(f"标签最佳匹配: {tag_needed}")
            problems = Codeforces._api('problemset.problems', tags=tag_needed.replace("-", " "))

        if isinstance(problems, int) or len(problems) == 0:
            return -3

        filtered_data = problems['problems']
        if limit is not None:
            filtered_data = [prob for prob in problems['problems']
                             if 'rating' in prob and min_point <= prob['rating'] <= max_point]
        if newer:
            filtered_data = [prob for prob in filtered_data if prob['contestId'] >= 1000]

        return random.choice(filtered_data) if len(filtered_data) > 0 else 0

    @staticmethod
    def get_user_info(handle: str) -> tuple[str, str | None]:
        info = Codeforces._api('user.info', handles=handle)

        if info == -1:
            return "查询异常", None
        if info == 0 or len(info) == 0:
            return "用户不存在", None

        info = info[-1]
        sections = []

        # 归属地
        belong, home, name = [], [], []
        if 'firstName' in info:
            name.append(info['firstName'])
        if 'lastName' in info:
            name.append(info['lastName'])
        if len(name) > 0:
            home.append(' '.join(name))
        if 'city' in info:
            home.append(info['city'])
        if 'country' in info:
            home.append(info['country'])
        if len(home) > 0:
            belong.append(', '.join(home))
        if 'organization' in info:
            if len(info['organization']) == 0:  # meme
                info['organization'] = '地球'
            belong.append(f"来自 {info['organization']}")
        if len(belong) > 0:
            sections.append('\n'.join(belong))

        # 平台上的信息
        rating = "0 Unrated"
        if 'rating' in info:
            rating = (f"{info['rating']} {info['rank'].capitalize()} "
                      f"(max. {info['maxRating']} {info['maxRank']})")
        platform = (f"比赛Rating: {rating}\n"
                    f"贡献: {info['contribution']}\n"
                    f"粉丝: {info['friendOfCount']}")
        sections.append(platform)

        return '\n\n'.join(sections), info.get('titlePhoto')

    @staticmethod
    def get_user_last_contest(handle: str) -> str:
        rating = Codeforces._api('user.rating', handle=handle)

        if rating == -1:
            return "查询异常"
        if rating == 0:
            return "用户不存在"

        rating = list(rating)
        contest_count = len(rating)
        if contest_count == 0:
            return "还未参加过 Rated 比赛"

        last = rating[-1]
        info = (f"Rated 比赛数: {contest_count}\n"
                f"最近一次比赛: {Codeforces._format_contest_name(last['contestName'])}\n"
                f"比赛编号: {last['contestId']}\n"
                f"位次: {last['rank']}\n"
                f"Rating 变化: {Codeforces._format_int_delta(last['newRating'] - last['oldRating'])}")

        return info

    @staticmethod
    def get_user_last_submit(handle: str, count: int = 5) -> str:
        status = Codeforces._api('user.status', handle=handle, _from_=1, count=count)

        if status == -1:
            return "查询异常"
        if status == 0:
            return "用户不存在"

        status = list(status)
        if len(status) == 0:
            return "还未提交过题目"

        info = f"最近{count}发提交:"
        for submit in status:
            verdict = (Codeforces._format_verdict(submit['verdict'], submit['passedTestCount'])
                       if 'verdict' in submit else "In queue")
            points = f" *{int(submit['problem']['rating'])}" if 'rating' in submit['problem'] else ""
            time = f" {submit['timeConsumedMillis']}ms" if 'timeConsumedMillis' in submit else ""
            info += (f"\n[{submit['id']}] {verdict} "
                     f"P{submit['problem']['contestId']}{submit['problem']['index']}{points}{time} "
                     f"{format_timestamp(submit['creationTimeSeconds'])}")

        return info

    @staticmethod
    def get_user_submit_counts(handle: str) -> tuple[int, int, int]:
        status = Codeforces._api('user.status', handle=handle)

        if isinstance(status, int):
            return -1, -1, -1

        status = list(status)
        submit_len = len(status)
        if submit_len == 0:
            return 0, 0, 0

        total_set, weekly_set, daily_set = set(), set(), set()
        week_start_time, today_start_time = get_week_start_timestamp(), get_today_start_timestamp()
        for submit in status:
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
    def get_user_contest_standings(handle: str, contest_id: str) -> tuple[str, list[str] | None]:
        standings = Codeforces._api('contest.standings', handles=handle, contestId=contest_id, showUnofficial=True)

        if standings == -1:
            return "查询异常", None
        if standings == 0:
            return "比赛不存在", None

        contest_info = Codeforces._format_contest(standings['contest'])
        standings_info = [Codeforces._format_standing(standing, contest_id) for standing in standings['rows']]

        return contest_info, standings_info

    @staticmethod
    def get_contest_list_all() -> list[dict] | None:
        contest_list = Codeforces._api('contest.list')

        if isinstance(contest_list, int):
            return None

        contest_list = list(contest_list)
        if len(contest_list) == 0:
            return []

        return contest_list

    @staticmethod
    def get_contest_list() -> list[Contest] | None:
        contest_list = Codeforces.get_contest_list_all()

        if contest_list is None:
            return None

        return [Contest(
            start_time=contest['startTimeSeconds'],
            duration=contest['durationSeconds'],
            platform='Codeforces',
            name=contest['name'],
            supplement=f"{contest['type']} 赛制"
        ) for contest in contest_list if contest['phase'] == 'BEFORE']

    @staticmethod
    def get_recent_contests() -> str:
        contest_list = Codeforces.get_contest_list_all()

        if contest_list is None:
            return "查询异常"

        if len(contest_list) == 0:
            return "最近没有比赛"

        limit = len(contest_list) - 1
        for i, contest in enumerate(contest_list):
            if contest['phase'] == 'FINISHED':
                limit = i - 1
                break

        unfinished_contests = contest_list[limit::-1]  # 按日期升序排列
        info = ""
        for contest in unfinished_contests:
            info += Codeforces._format_contest(contest) + "\n\n"

        last_finished_contest = contest_list[limit + 1]
        info += "上一场已结束的比赛:\n" + Codeforces._format_contest(last_finished_contest)

        return info

    @staticmethod
    def get_contest_predict(contest_id: str) -> dict[str, PredictResult] | int:
        """
        Adapted from carrot at
        https://github.com/meooow25/carrot/blob/master/carrot/src/background/cache/contests-complete.js
        and
        https://github.com/meooow25/carrot/blob/master/carrot/src/background/background.js
        """
        standings = Codeforces._api('contest.standings', contestId=contest_id)

        if standings == -1:
            return -1
        if standings == 0:
            return 0

        rated, old_ratings = None, None

        if standings['contest']['phase'] == 'FINISHED':
            rating_changes = Codeforces._api('contest.ratingChanges', contestId=contest_id)
            if rating_changes == -1:
                return -2
            if rating_changes == 0:
                rated = False
            else:
                rating_changes = list(rating_changes)
                if len(rating_changes) == 0:
                    return -2
                rated = True
                old_ratings = Codeforces._adjust_old_ratings(int(contest_id), rating_changes)

        if rated is None and Codeforces._is_old_contest(standings):
            rated = False

        contest_finished = rated is not None

        if contest_finished:
            if not rated:
                return 1

            # We can ensure that old_ratings is not None
            return Codeforces._get_final_prefs(standings, old_ratings)

        if (standings['contest'].lower()
                in ['unrated', 'fools', 'q#', 'kotlin', 'marathon', 'teams']):  # UNRATED_HINTS
            return 1

        if any('teamId' in standing for standing in standings['rows']):
            return 1

        return Codeforces._get_predicted_prefs(standings)
