import abc
import time
from dataclasses import dataclass

import pixie

from src.core.tools import format_timestamp_diff, format_seconds, format_timestamp


@dataclass
class Contest:
    platform: str
    abbr: str
    name: str
    phase: str
    start_time: int
    duration: int
    supplement: str

    def format(self) -> str:
        """
        格式化为文本
        :return: 格式化后的文本信息
        """
        if int(time.time()) >= self.start_time:
            status = self.phase  # 用于展示"比赛中"，或者诸如 Codeforces 平台的 "正在重测中"
        else:
            status = format_timestamp_diff(int(time.time()) - self.start_time)
        return (f"[{self.platform} · {self.abbr}] "
                f"{self.name}\n"
                f"{status}, {format_timestamp(self.start_time)}\n"
                f"持续 {format_seconds(self.duration)}, {self.supplement}")


class CompetitivePlatform(abc.ABC):
    platform_name: str
    rks_color: dict[str, str]

    @classmethod
    def get_contest_list(cls) -> tuple[list[Contest], list[Contest], list[Contest]] | None:
        """
        指定平台分类比赛列表
        其中，已结束的比赛为 上一个已结束的比赛 与 当天所有已结束的比赛 的并集
        :return: tuple[待举行的比赛，正在进行的比赛, 已结束的比赛] | None
        """
        pass

    @classmethod
    def get_recent_contests(cls) -> str:
        """
        指定平台待举行的比赛以及上一个已结束的比赛
        :return: 格式化后的相关信息
        """
        contest_list = cls.get_contest_list()

        if contest_list is None:
            return "查询异常"

        upcoming_contests, running_contests, finished_contests = contest_list
        upcoming_contests.sort(key=lambda c: c.start_time)
        running_contests.sort(key=lambda c: c.start_time)
        finished_contests.sort(key=lambda c: c.start_time)

        info = ""

        if len(running_contests) > 0:
            info += ">> 正在进行的比赛 >>\n\n"
            info += '\n\n'.join([contest.format() for contest in running_contests])
            info += "\n\n"

        if len(upcoming_contests) == 0:
            info += ">> 最近没有比赛 >>\n\n"
        else:
            info += ">> 即将开始的比赛 >>\n\n"
            info += '\n\n'.join([contest.format() for contest in upcoming_contests])
            info += "\n\n"

        info += ">> 上一场已结束的比赛 >>\n\n" + finished_contests[0].format()

        return info

    @classmethod
    def get_user_id_card(cls, handle: str) -> pixie.Image | str:
        """
        获取指定用户的基础信息卡片
        :return: 绘制完成的图片对象 | 错误信息
        """
        pass

    @classmethod
    def get_user_info(cls, handle: str) -> tuple[str, str | None]:
        """
        获取指定用户的详细信息
        :return: tuple[信息, 头像url | None]
        """
        pass
