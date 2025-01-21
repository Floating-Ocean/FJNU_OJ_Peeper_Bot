import re
from datetime import datetime

from lxml.etree import Element

from src.core.tools import fetch_html
from src.platform.model import CompetitivePlatform, Contest


class NowCoder(CompetitivePlatform):
    platform_name = "NowCoder"

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
    def get_contest_list(cls, overwrite_tag: bool = False) -> tuple[list[Contest], Contest] | None:
        upcoming_contests: list[Contest] = []
        finished_contests: list[Contest] = []
        for category_id in [13, 14]:
            html = fetch_html(f"https://ac.nowcoder.com/acm/contest/vip-index?topCategoryFilter={category_id}")
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
