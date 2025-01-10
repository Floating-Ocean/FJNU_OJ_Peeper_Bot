from datetime import datetime

from src.core.tools import fetch_html
from src.platforms.platform import Platform, Contest


class AtCoder(Platform):

    @staticmethod
    def extract_timestamp(time_str: str) -> int:
        return int(datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S%z").timestamp())

    @staticmethod
    def extract_duration(time_str: str) -> int:
        hour, minute = map(int, time_str.split(":"))
        return hour * 3600 + minute * 60

    @staticmethod
    def format_rated_range(rating_str: str) -> str:
        rating_str = rating_str.replace(' ', '')
        if rating_str == '-':
            return "不计分"
        if rating_str[0] == '-':
            return f"为 0{rating_str} 计分"
        if rating_str[-1] == '-':
            return f"为 {rating_str}∞ 计分"
        return f"为 {rating_str} 计分"

    @staticmethod
    def get_contest_list() -> list[Contest] | None:
        html = fetch_html("https://atcoder.jp/contests/")
        contest_table_upcoming = html.xpath("//div[@id='contest-table-upcoming']//tbody/tr")

        return [Contest(
            start_time=AtCoder.extract_timestamp(contest.xpath(".//td[1]/a/time/text()")[0]),
            duration=AtCoder.extract_duration(contest.xpath(".//td[3]/text()")[0]),
            platform='AtCoder',
            name=contest.xpath(".//td[2]/a/text()")[0],
            supplement=AtCoder.format_rated_range(contest.xpath(".//td[4]/text()")[0])
        ) for contest in contest_table_upcoming]
