import random
from datetime import datetime

import pixie

from src.core.tools import fetch_url_element, fetch_url_json, format_int_delta, patch_https_url, decode_range
from src.platform.cp.codeforces import Codeforces
from src.platform.it.clist import Clist
from src.platform.model import CompetitivePlatform, Contest


class AtCoder(CompetitivePlatform):
    platform_name = "AtCoder"
    rks_color = {
        '10 Kyu': '#808080', '9 Kyu': '#808080',
        '8 Kyu': '#804000', '7 Kyu': '#804000',
        '6 Kyu': '#008000', '5 Kyu': '#008000',
        '4 Kyu': '#00c0c0', '3 Kyu': '#00c0c0',
        '2 Kyu': '#0000ff', '1 Kyu': '#0000ff',
        '1 Dan': '#c0c000', '2 Dan': '#c0c000',
        '3 Dan': '#ff8000', '4 Dan': '#ff8000',
        '5 Dan': '#ff0000', '6 Dan': '#ff0000',
        '7 Dan': '#ff0000', '8 Dan': '#ff0000',
        '9 Dan': '#ff0000', '10 Dan': '#ff0000',
        'King': '#ff0000'
    }

    @classmethod
    def _extract_timestamp(cls, time_str: str) -> int:
        return int(datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S%z").timestamp())

    @classmethod
    def _extract_duration(cls, time_str: str) -> int:
        hour, minute = map(int, time_str.split(":"))
        return hour * 3600 + minute * 60

    @classmethod
    def _format_rated_range(cls, rating_str: str) -> str:
        rating_str = rating_str.replace(' ', '')
        if rating_str == '-':
            return "不计分"
        if rating_str[0] == '-':
            return f"为 0{rating_str} 计分"
        if rating_str[-1] == '-':
            return f"为 {rating_str}∞ 计分"
        if rating_str == 'All':
            return "为所有人计分"
        return f"为 {rating_str} 计分"

    @classmethod
    def _format_social_info(cls, info: dict, i18n: tuple[str, str, str] = ("国家/地区", "出生年份", "来自")) -> list[str]:
        social_info = []
        tag_trans = {
            "Country/Region": i18n[0],
            "Birth Year": i18n[1],
            "Affiliation": i18n[2]
        }
        for tag, trans in tag_trans.items():
            if tag in info:
                social_info.append(f"{trans} {info[tag]}")
        return social_info

    @classmethod
    def get_contest_list(cls, overwrite_tag: bool = False) -> tuple[list[Contest], Contest] | None:
        html = fetch_url_element("https://atcoder.jp/contests/")
        contest_table_upcoming = html.xpath("//div[@id='contest-table-upcoming']//tbody/tr")
        contest_table_recent = html.xpath("//div[@id='contest-table-recent']//tbody/tr")

        upcoming_contests = [Contest(
            start_time=cls._extract_timestamp(contest.xpath(".//td[1]/a/time/text()")[0]),
            duration=cls._extract_duration(contest.xpath(".//td[3]/text()")[0]),
            tag=cls.platform_name if overwrite_tag else contest.xpath(".//td[2]/a/@href")[0].split('/')[-1],
            name=contest.xpath(".//td[2]/a/text()")[0],
            supplement=cls._format_rated_range(contest.xpath(".//td[4]/text()")[0])
        ) for contest in contest_table_upcoming]
        finished_contest = Contest(
            start_time=cls._extract_timestamp(contest_table_recent[0].xpath(".//td[1]/a/time/text()")[0]),
            duration=cls._extract_duration(contest_table_recent[0].xpath(".//td[3]/text()")[0]),
            tag=(cls.platform_name if overwrite_tag else
                 contest_table_recent[0].xpath(".//td[2]/a/@href")[0].split('/')[-1]),
            name=contest_table_recent[0].xpath(".//td[2]/a/text()")[0],
            supplement=cls._format_rated_range(contest_table_recent[0].xpath(".//td[4]/text()")[0])
        )

        return upcoming_contests, finished_contest

    @classmethod
    def get_prob_filtered(cls, contest_type: str = 'common', limit: str = None) -> dict | int:
        min_point, max_point = 0, 0
        if limit is not None:
            min_point, max_point = decode_range(limit, length=(3, 4))
            if min_point == -2:
                return -1
            elif min_point == -3:
                return 0

        filter_regex = ''
        if contest_type == 'common':
            filter_regex = r'^https:\/\/atcoder\.jp\/contests\/(abc|arc|agc|ahc)'
        elif contest_type in ['abc', 'arc', 'agc', 'ahc']:
            filter_regex = rf'^https:\/\/atcoder\.jp\/contests\/{contest_type}'
        elif contest_type == 'sp':
            filter_regex = r'^(?!https:\/\/atcoder\.jp\/contests\/(abc|arc|agc|ahc)).*'
        elif contest_type != 'all':
            return -2

        if limit is not None:
            filtered_data = Clist.api("problem", resource_id=93, rating__gte=min_point, rating__lte=max_point,
                                      url__regex=filter_regex)
        else:
            filtered_data = Clist.api("problem", resource_id=93, url__regex=filter_regex)

        if isinstance(filtered_data, int):
            return filtered_data

        return random.choice(filtered_data) if len(filtered_data) > 0 else 0

    @classmethod
    def get_user_id_card(cls, handle: str) -> pixie.Image | str:
        html = fetch_url_element(f"https://atcoder.jp/users/{handle}")

        info_table = html.xpath("//table[@class='dl-table']//tr")
        info_dict = {row.xpath('.//th/text()')[0]: row.xpath('.//td//text()')[0].strip() for row in info_table}

        social = '. '.join(cls._format_social_info(info_dict, ('', 'Born in', 'From'))).lstrip()
        if len(social) > 0:
            social = f"{social}."

        rated_table = html.xpath("//div[h3[text()='Contest Status']]")[0].xpath(".//table")[0].xpath(".//tr")
        rated_dict = {row.xpath('.//th/text()')[0].strip(): row.xpath('.//td//text()') for row in rated_table}

        rating = rated_dict['Rating'][0]
        rank = rated_dict['Highest Rating'][4]
        return cls._render_user_card(handle=html.xpath("//a[@class='username']//text()")[0],
                                     social=social, rank=rank, rank_alias=rank, rating=rating)

    @classmethod
    def get_user_info(cls, handle: str) -> tuple[str, str | None]:
        html = fetch_url_element(f"https://atcoder.jp/users/{handle}")

        sections = []

        info_table = html.xpath("//table[@class='dl-table']//tr")
        info_dict = {row.xpath('.//th/text()')[0]: row.xpath('.//td//text()')[0].strip() for row in info_table}

        social = cls._format_social_info(info_dict)
        if len(social) > 0:
            sections.append('\n'.join(social))

        linked = ["关联账号"]
        for tag in ["Twitter ID", "TopCoder ID", "Codeforces ID"]:
            if tag == "Codeforces ID":
                info_dict[tag] += f" ({Codeforces.get_user_rank(info_dict[tag])})"
            if tag in info_dict:
                linked.append(f"{tag[:-3]}: {info_dict[tag]}")
        if len(linked) > 1:
            sections.append('\n'.join(linked))

        rated_table = html.xpath("//div[h3[text()='Contest Status']]")[0].xpath(".//table")[0].xpath(".//tr")
        rated_dict = {row.xpath('.//th/text()')[0].strip(): row.xpath('.//td//text()') for row in rated_table}
        rated_dict['Highest Rating'][0] = rated_dict['Highest Rating'][0].replace(' Kyu', '级').replace(' Dan', '段')
        platform = [
            f"位次: {rated_dict['Rank'][0]}",
            f"比赛Rating: {rated_dict['Rating'][0]}",
            f"最高Rating: {rated_dict['Highest Rating'][0]}"
            f" {rated_dict['Highest Rating'][4]} {rated_dict['Highest Rating'][6]}"
        ]
        sections.append('\n'.join(platform))

        return '\n\n'.join(sections), patch_https_url(html.xpath("//img[@class='avatar']/@src")[0])

    @classmethod
    def get_user_last_contest(cls, handle: str) -> str:
        url = f"https://atcoder.jp/users/{handle}/history/json"
        json_data = fetch_url_json(url, throw=False, method='get')

        if isinstance(json_data, int):
            return "查询异常"

        rated_contests = list([contest for contest in json_data if contest['IsRated']])
        contest_count = len(rated_contests)
        if contest_count == 0:
            return "还未参加过 Rated 比赛"

        last = rated_contests[-1]
        info = (f"Rated 比赛数: {contest_count}\n"
                f"最近一次比赛: {last['ContestName']}\n"
                f"位次: {last['Place']}\n"
                f"表现分: {last['Performance']} ({last['InnerPerformance']})\n"
                f"Rating 变化: {format_int_delta(last['NewRating'] - last['OldRating'])}")

        return info
