import abc
import time
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import pixie

from src.core.tools import format_timestamp_diff, format_seconds, format_timestamp, check_intersect, \
    get_a_month_timestamp_range


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


class DynamicContestPhase(Enum):
    UPCOMING = 0
    RUNNING = 1
    ENDED = 2


@dataclass
class DynamicContest(Contest):
    """根据当前时间确定phase，需要传递除phase外的所有参数"""

    def get_phase(self) -> DynamicContestPhase:
        current_tick = int(datetime.now().timestamp())
        start_tick, end_tick = self.start_time, self.start_time + self.duration
        if current_tick < start_tick:
            return DynamicContestPhase.UPCOMING
        elif current_tick > end_tick:
            return DynamicContestPhase.ENDED
        else:
            return DynamicContestPhase.RUNNING

    def __init__(self, **kwargs):
        self.platform = kwargs['platform']
        self.abbr = kwargs['abbr']
        self.name = kwargs['name']
        self.start_time = kwargs['start_time']
        self.duration = kwargs['duration']
        self.supplement = kwargs['supplement']
        current_phase = self.get_phase()
        if current_phase != DynamicContestPhase.RUNNING:
            current_tick = int(datetime.now().timestamp())
            self.phase = format_timestamp_diff(current_tick - self.start_time)
        else:
            self.phase = "正在比赛中"


class CompetitivePlatform(abc.ABC):
    platform_name: str
    rks_color: dict[str, str]

    @classmethod
    @abstractmethod
    def _get_contest_list(cls) -> tuple[list[Contest], list[Contest], list[Contest]] | None:
        """
        需被重载。
        指定平台分类比赛列表
        其中，已结束的比赛为 上一个已结束的比赛 与 当天所有已结束的比赛 的并集
        :return: tuple[正在进行的比赛, 待举行的比赛，已结束的比赛] | None
        """
        pass

    @classmethod
    def get_contest_list(cls) -> tuple[list[Contest], list[Contest], list[Contest]] | None:
        """
        指定平台分类比赛列表，限定一个月内
        其中，已结束的比赛为 上一个已结束的比赛 与 当天所有已结束的比赛 的并集
        :return: tuple[正在进行的比赛, 待举行的比赛，已结束的比赛] | None
        """
        contests = cls._get_contest_list()
        if contests is None:
            return None

        running_full_contests, upcoming_full_contests, finished_full_contests = contests
        running_contests = [contest for contest in running_full_contests
                            if check_intersect((contest.start_time, contest.start_time + contest.duration),
                                               get_a_month_timestamp_range())]
        upcoming_contests = [contest for contest in upcoming_full_contests
                             if check_intersect((contest.start_time, contest.start_time + contest.duration),
                                                get_a_month_timestamp_range())]
        finished_contests = finished_full_contests

        return running_contests, upcoming_contests, finished_contests

    @classmethod
    def get_recent_contests(cls) -> str:
        """
        指定平台待举行的比赛以及上一个已结束的比赛
        :return: 格式化后的相关信息
        """
        contest_list = cls.get_contest_list()

        if contest_list is None:
            return "查询异常"

        running_contests, upcoming_contests, finished_contests = contest_list
        running_contests.sort(key=lambda c: c.start_time)
        upcoming_contests.sort(key=lambda c: c.start_time)
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
    @abstractmethod
    def get_user_id_card(cls, handle: str) -> pixie.Image | str:
        """
        获取指定用户的基础信息卡片
        :return: 绘制完成的图片对象 | 错误信息
        """
        pass

    @classmethod
    @abstractmethod
    def get_user_info(cls, handle: str) -> tuple[str, str | None]:
        """
        获取指定用户的详细信息
        :return: tuple[信息, 头像url | None]
        """
        pass
