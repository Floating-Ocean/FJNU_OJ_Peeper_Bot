import re
from datetime import datetime

from lxml.etree import Element

from src.core.tools import fetch_url_element, patch_https_url, fetch_url_json, format_int_delta
from src.platform.model import CompetitivePlatform, Contest


class NowCoder(CompetitivePlatform):
    platform_name = "NowCoder"
    rated_rks = {
        (-float('inf'), 700): '#灰',
        (700, 1100): '#紫',
        (1100, 1500): '#蓝',
        (1500, 2000): '#青',
        (2000, 2400): '#黄',
        (2400, 2800): '#橙',
        (2800, float('inf')): '#红'
    }

    @classmethod
    def _api(cls, url: str) -> list[dict] | int:
        json_data = fetch_url_json(url, throw=False, method='get')

        if isinstance(json_data, int) or json_data['msg'] != "OK":
            if isinstance(json_data, int):
                return -1
            return 0

        data_list = json_data['data']['dataList']
        all_data = list(data_list)

        # 爬取所有页
        page_count = json_data['data']['pageInfo']['pageCount']
        for page in range(2, page_count + 1):
            json_data = fetch_url_json(f"{url}&page={page}", throw=False, method='get')
            if isinstance(json_data, int) or json_data['msg'] != "OK":
                return -1
            all_data.extend(list(json_data['data']['dataList']))

        return all_data

    @classmethod
    def _extract_timestamp(cls, time_str: str) -> int:
        return int(datetime.strptime(time_str, "%Y-%m-%d %H:%M").timestamp())

    @classmethod
    def _extract_duration(cls, time_str: str) -> int:
        units_in_seconds = {
            '天': 24 * 3600,
            '小时': 3600,
            '分钟': 60,
            '秒': 1
        }
        matches = re.findall(r'(\d+)(天|小时|分钟|秒)', time_str)
        total_seconds = 0
        for val, unit in matches:
            total_seconds += int(val) * units_in_seconds[unit]

        return total_seconds

    @classmethod
    def _decode_contest_time_set(cls, contest: Element) -> list[str]:
        return re.split(r' {4}|\n ', contest.xpath(".//li[@class='match-time-icon']/text()")[0])

    @classmethod
    def _decode_rated(cls, contest: Element) -> str:
        rated_icon = contest.xpath(".//span[contains(@class, 'tag-rating')]")
        if len(rated_icon) == 0:
            return "不计分"

        unrated_range_li = contest.xpath(".//li[@class='icon-nc-flash2']/text()")
        if len(unrated_range_li) == 0:
            return "为所有人计分"

        unrated_range = int(unrated_range_li[0].split('＞')[1])
        return f"为 0-{unrated_range} 计分"

    @classmethod
    def _format_rating(cls, rating: int) -> str:
        rk = next((rk for (l, r), rk in NowCoder.rated_rks.items() if l <= rating < r), '#灰')
        return f"{rating} {rk}"

    @classmethod
    def _fetch_user_rating(cls, handle: str) -> str:
        html = fetch_url_element(f"https://ac.nowcoder.com/acm/contest/profile/{handle}")
        rating = int(html.xpath("//div[contains(@class, 'state-num rate-score')]/text()")[0])
        return cls._format_rating(rating)

    @classmethod
    def _fetch_team_members_info(cls, handle: str) -> str:
        url = f"https://ac.nowcoder.com/acm/team/member-list?token=&teamId={handle}"
        members = cls._api(url)

        if members == -1:
            return "查询异常"
        if members == 0:
            return "用户不存在"

        member_infos = []

        for member in members:
            member_info = [member['name']]
            if member['isTeamAdmin']:
                member_info.append("队长")
            member_info.append(cls._fetch_user_rating(member['uid']))
            member_infos.append(' '.join(member_info))

        return '\n'.join(member_infos)

    @classmethod
    def _fetch_user_teams_info(cls, handle: str) -> str | None:
        url = f"https://ac.nowcoder.com/acm/contest/profile/user-team-list?token=&uid={handle}"
        teams = cls._api(url)

        if isinstance(teams, int):
            return None

        teams_infos = []

        for team in teams:
            team_info = [team['name'], cls._format_rating(int(team['rating']))]
            teams_infos.append(' '.join(team_info))

        if len(teams_infos) == 0:
            return None

        return '\n'.join(teams_infos)

    @classmethod
    def get_contest_list(cls, overwrite_tag: bool = False) -> tuple[list[Contest], Contest] | None:
        upcoming_contests: list[Contest] = []
        finished_contests: list[Contest] = []
        for category_id in [13, 14]:
            html = fetch_url_element(f"https://ac.nowcoder.com/acm/contest/vip-index?topCategoryFilter={category_id}")
            js_current = html.xpath("//div[@class='platform-mod js-current']//div[@class='platform-item-cont']")
            js_end = html.xpath("//div[@class='platform-mod js-end']//div[@class='platform-item-cont']")
            upcoming_contests.extend([Contest(
                start_time=NowCoder._extract_timestamp(NowCoder._decode_contest_time_set(contest)[1]),
                duration=NowCoder._extract_duration(NowCoder._decode_contest_time_set(contest)[4]),
                tag=NowCoder.platform_name if overwrite_tag else None,
                name=contest.xpath(".//a/text()")[0],
                supplement=NowCoder._decode_rated(contest)
            ) for contest in js_current
                if contest.xpath(".//span[contains(@class, 'match-status')]/text()")[0].strip() == '报名中'])
            finished_contests.append(Contest(
                start_time=NowCoder._extract_timestamp(NowCoder._decode_contest_time_set(js_end[0])[1]),
                duration=NowCoder._extract_duration(NowCoder._decode_contest_time_set(js_end[0])[4]),
                tag=NowCoder.platform_name if overwrite_tag else None,
                name=js_end[0].xpath(".//a/text()")[0],
                supplement=NowCoder._decode_rated(js_end[0])
            ))

        finished_contests.sort(key=lambda c: -c.start_time)
        if len(finished_contests) == 0:
            return None

        return upcoming_contests, finished_contests[0]

    @classmethod
    def get_user_info(cls, handle: str) -> tuple[str, str | None]:
        html = fetch_url_element(f"https://ac.nowcoder.com/acm/contest/profile/{handle}")

        sections = []

        belong = []
        name = html.xpath("//a[contains(@class, 'coder-name')]/text()")[0].strip()
        belong.append(name)
        brief_intro = html.xpath("//div[@class='coder-brief']/text()")[0].strip()
        belong.append(brief_intro)
        edu_span = html.xpath('//div[contains(@class, "edu-item")]//span[@class="coder-edu-txt"]/text()')
        coll_span = html.xpath('//div[contains(@class, "coll-item")]//span[@class="coder-edu-txt"]/text()')
        edu_text = f"来自 {edu_span[0]}" if len(edu_span) > 0 else None
        coll_text = f"{coll_span[0]}er" if len(coll_span) > 0 else None
        edu_info = [edu_txt for edu_txt in [coll_text, edu_text] if edu_txt is not None]
        if len(edu_info) > 0:
            belong.append('，'.join(edu_info))

        if len(belong) > 0:
            sections.append('\n'.join(belong))

        is_group = len(html.xpath("//a[@class='group-member-btn']")) > 0
        if is_group:
            members = cls._fetch_team_members_info(handle)
            sections.append(f"队伍成员:\n{members}")

        platform = []
        rating = int(html.xpath("//div[contains(@class, 'state-num rate-score')]/text()")[0])
        platform.append(f"比赛Rating: {cls._format_rating(rating)}")
        rating_rank = html.xpath('//div[@class="profile-status-box"]//a[contains(@href, "/rating-index")]/text()')
        following = html.xpath('//div[@class="profile-status-box"]//a[contains(@href, "/following")]/text()')
        followers = html.xpath('//div[@class="profile-status-box"]//a[contains(@href, "/followers")]/text()')
        if len(rating_rank) > 0:
            platform.append(f"位次: {rating_rank[0]}")
        if len(following) > 0:
            platform.append(f"关注: {following[0]}")
        if len(followers) > 0:
            platform.append(f"粉丝: {followers[0]}")
        sections.append('\n'.join(platform))

        joined_teams = cls._fetch_user_teams_info(handle)
        if joined_teams is not None:
            sections.append(f"加入的队伍:\n{joined_teams}")

        return '\n\n'.join(sections), html.xpath("//a[contains(@class, 'head-pic')]//img/@src")[0]

    @classmethod
    def get_user_last_contest(cls, handle: str) -> str:
        url = (f"https://ac.nowcoder.com/acm-heavy/acm/contest/profile/contest-joined-history?token=&"
               f"uid={handle}&onlyJoinedFilter=true&searchContestName=&onlyRatingFilter=true&"
               f"contestEndFilter=true")
        rated_contests = cls._api(url)

        if rated_contests == -1:
            return "查询异常"
        if rated_contests == 0:
            return "用户不存在"

        contest_count = len(rated_contests)
        if contest_count == 0:
            return "还未参加过 Rated 比赛"

        group_contest_count = len([contest for contest in rated_contests if contest['isTeamSignUp']])
        if group_contest_count > 0:
            contest_count = f"{contest_count}，包含团队赛 {group_contest_count} 场"

        last = rated_contests[0]
        info = (f"Rated 比赛数: {contest_count}\n"
                f"最近一次比赛: {last['contestName']}\n"
                f"位次: {last['rank']}\n"
                f"AC 数量: {last['acceptedCount']}\n"
                f"Rating 变化: {format_int_delta(int(last['changeValue']))}\n")

        return info
