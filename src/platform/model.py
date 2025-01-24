import abc
import time
from dataclasses import dataclass

from src.core.tools import format_timestamp_diff, format_seconds, format_timestamp


@dataclass
class Contest:
    start_time: int
    duration: int
    tag: str | None
    name: str
    supplement: str

    def format(self) -> str:
        """
        格式化为文本
        :return: 格式化后的文本信息
        """
        delta_time = format_timestamp_diff(int(time.time()) - self.start_time)
        return ((f"[{self.tag}] " if self.tag is not None else "") +
                (f"{self.name}\n"
                 f"{delta_time}, {format_timestamp(self.start_time)}\n"
                 f"持续 {format_seconds(self.duration)}, {self.supplement}"))


class CompetitivePlatform(abc.ABC):
    platform_name: str

    @classmethod
    def get_contest_list(cls, overwrite_tag: bool = False) -> tuple[list[Contest], Contest] | None:
        """
        指定平台待举行的比赛以及上一个已结束的比赛
        :return: tuple[平台待举行的比赛, 上一个已结束的比赛] | None
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

        upcoming_contests, finished_contest = contest_list
        info = ""

        if len(upcoming_contests) == 0:
            info = "最近没有比赛"

        info += '\n\n'.join([contest.format() for contest in upcoming_contests])
        info += "\n\n上一场已结束的比赛:\n" + finished_contest.format()

        return info
    
    @classmethod
    def get_contest(cls,contestId: str) -> Contest:
        pass
