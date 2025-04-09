import abc
import time
from dataclasses import dataclass

import pixie
from easy_pixie import draw_gradient_rect, GradientDirection, draw_mask_rect, darken_color, draw_img, draw_text, \
    StyledString, GradientColor, Loc

from src.core.painter import get_img_path
from src.core.tools import format_timestamp_diff, format_seconds, format_timestamp


@dataclass
class Contest:
    start_time: int
    phase: str
    duration: int
    tag: str | None
    name: str
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
        return ((f"[{self.tag}] " if self.tag is not None else "") +
                (f"{self.name}\n"
                 f"{status}, {format_timestamp(self.start_time)}\n"
                 f"持续 {format_seconds(self.duration)}, {self.supplement}"))


class CompetitivePlatform(abc.ABC):
    platform_name: str
    rks_color: dict[str, str]

    @classmethod
    def _render_user_card(cls, handle: str, social: str,
                          rank: str, rank_alias: str, rating: int | str) -> pixie.Image:
        """
        渲染用户基础信息卡片
        :return: 绘制完成的图片对象
        """
        img = pixie.Image(1664, 1040)
        img.fill(pixie.Color(0, 0, 0, 1))

        rk_color = cls.rks_color[rank_alias]
        draw_gradient_rect(img, Loc(32, 32, 1600, 976), GradientColor(["#fcfcfc", rk_color], [0.0, 1.0], ''),
                           GradientDirection.DIAGONAL_LEFT_TO_RIGHT, 96)
        draw_mask_rect(img, Loc(32, 32, 1600, 976), pixie.Color(1, 1, 1, 0.6), 96)

        text_color = darken_color(pixie.parse_color(rk_color), 0.2)
        pf_raw_text = f"{cls.platform_name} ID"
        draw_img(img, get_img_path(cls.platform_name), Loc(144 + 32, 120 + 6 + 32, 48, 48), text_color)

        pf_text = StyledString(pf_raw_text, 'H', 44, font_color=text_color, padding_bottom=30)
        handle_text = StyledString(handle, 'H', 96, font_color=text_color, padding_bottom=20)
        social_text = StyledString(social, 'B', 28, font_color=text_color, padding_bottom=112)
        rank_text = StyledString(rank, 'H', 44, font_color=text_color, padding_bottom=-6)
        rating_text = StyledString(f"{rating}", 'H', 256, font_color=text_color, padding_bottom=44)

        current_x, current_y = 144 + 32, 120 + 32
        current_y = draw_text(img, pf_text, current_x + 48 + 18, current_y)
        current_y = draw_text(img, handle_text, current_x, current_y)
        current_y = draw_text(img, social_text, current_x, current_y)
        current_y = draw_text(img, rank_text, current_x, current_y)
        draw_text(img, rating_text, current_x - 10, current_y)

        return img

    @classmethod
    def get_contest_list(cls, overwrite_tag: bool = False) -> tuple[list[Contest], list[Contest], list[Contest]] | None:
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
