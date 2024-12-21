import re
from datetime import datetime

from lxml import etree
from lxml.etree import Element

from src.core.tools import fetch_html
from src.platforms.platform import Platform, ContestDict


class NowCoder(Platform):

    @staticmethod
    def extract_timestamp(time_str: str) -> int:
        return int(datetime.strptime(time_str, "%Y-%m-%d %H:%M").timestamp())

    @staticmethod
    def extract_duration(time_str: str) -> int:
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

    @staticmethod
    def decode_contest_time_set(contest: Element) -> list[str]:
        return re.split(r' {4}|\n ', contest.xpath(".//li[@class='match-time-icon']/text()")[0])

    @staticmethod
    def decode_rated(contest: Element) -> str:
        rated_icon = contest.xpath(".//span[contains(@class, 'tag-rating')]")
        if len(rated_icon) == 0:
            return "不计分"

        unrated_range_li = contest.xpath(".//li[@class='icon-nc-flash2']/text()")
        if len(unrated_range_li) == 0:
            return "为所有人计分"

        unrated_range = int(unrated_range_li[0].split('＞')[1])
        return f"为 0-{unrated_range} 计分"

    @staticmethod
    def get_contest_list() -> list[ContestDict] | None:
        contests: list[ContestDict] = []
        for category_id in [13, 14]:
            html = fetch_html(f"https://ac.nowcoder.com/acm/contest/vip-index?topCategoryFilter={category_id}")
            js_current = html.xpath("//div[@class='platform-mod js-current']//div[@class='platform-item-cont']")
            contests.extend([{
                'start_time': NowCoder.extract_timestamp(NowCoder.decode_contest_time_set(contest)[1]),
                'duration': NowCoder.extract_duration(NowCoder.decode_contest_time_set(contest)[4]),
                'platform': 'NowCoder',
                'name': contest.xpath(".//a/text()")[0],
                'supplement': NowCoder.decode_rated(contest)
            } for contest in js_current
                if contest.xpath(".//span[contains(@class, 'match-status')]/text()")[0].strip() == '报名中'])

        return contests
