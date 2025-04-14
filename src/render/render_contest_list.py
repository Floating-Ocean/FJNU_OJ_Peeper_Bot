import time
from datetime import datetime

import pixie
from easy_pixie import StyledString, calculate_height, draw_text, calculate_width, Loc, draw_img, \
    pick_gradient_color, draw_gradient_rect, GradientDirection, draw_mask_rect, darken_color

from src.core.constants import Constants
from src.core.tools import format_timestamp, format_timestamp_diff, format_seconds
from src.platform.model import Contest
from src.render.model import Renderer


class ContestListRenderer(Renderer):
    """渲染比赛列表"""
    _CONTENT_WIDTH = 1024
    _CONTEST_PADDING = 108
    _TYPE_PADDING = 128

    class _ContestItem:
        def __init__(self, contest: Contest, idx: int):
            self._contest = contest
            self._idx = idx + 1

            if int(time.time()) >= self._contest.start_time:
                _status = self._contest.phase  # 用于展示"比赛中"，或者诸如 Codeforces 平台的 "正在重测中"
            else:
                _status = format_timestamp_diff(int(time.time()) - self._contest.start_time)

            self._00_idx_text = StyledString("00",'H', 72)
            self._begin_x = ContestListRenderer._CONTEST_PADDING + calculate_width(self._00_idx_text) + 48
            max_width = ContestListRenderer._CONTENT_WIDTH + 32 - self._begin_x - 48 - ContestListRenderer._CONTEST_PADDING

            self._idx_text = StyledString(f"{self._idx:02d}",
                                          'H', 78,
                                          font_color=(0, 0, 0, 30), padding_bottom=12)
            self._subtitle_text = StyledString(f"{self._contest.platform.upper()} · {self._contest.abbr}",
                                               'H', 20, max_width=max_width, padding_bottom=12)
            self._title_text = StyledString(f"{self._contest.name}",
                                               'H', 56, max_width=max_width, padding_bottom=12)
            self._time_text = StyledString(f"{_status}, {format_timestamp(self._contest.start_time)}",
                                           'M', 32, max_width=max_width, padding_bottom=12)
            self._status_text = StyledString(f"持续 {format_seconds(self._contest.duration)}, {self._contest.supplement}",
                                          'M', 32, max_width=max_width, padding_bottom=12)

        def calculate_height(self):
            return calculate_height([self._subtitle_text, self._title_text, self._time_text, self._status_text])

        def render_item(self, img: pixie.Image, y: int) -> int:
            current_x, current_y = self._begin_x - calculate_width(self._idx_text) - 48, y

            draw_text(img, self._idx_text, current_x, current_y - 14)
            current_x = self._begin_x

            draw_img(img, Renderer._get_img_path(self._contest.platform), Loc(current_x, current_y + 4, 20, 20),
                     pixie.Color(0, 0, 0, 1))
            current_y = draw_text(img, self._subtitle_text, current_x + 28, current_y)
            current_y = draw_text(img, self._title_text, current_x, current_y)
            current_y = draw_text(img, self._time_text, current_x, current_y)
            current_y = draw_text(img, self._status_text, current_x, current_y)

            return current_y

    def __init__(self, running_contests: list[Contest], upcoming_contests: list[Contest], finished_contests: list[Contest]):
        self._raw_running_contests = running_contests
        self._raw_upcoming_contests = upcoming_contests
        self._raw_finished_contests = finished_contests
        self._running_contests = [self._ContestItem(contest, idx) for idx, contest in enumerate(running_contests)]
        self._upcoming_contests = [self._ContestItem(contest, idx) for idx, contest in enumerate(upcoming_contests)]
        self._finished_contests = [self._ContestItem(contest, idx) for idx, contest in enumerate(finished_contests)]

    def render(self) -> pixie.Image:
        logo_path = self._get_img_path("Contest")
        running_logo_path = self._get_img_path("Running")
        upcoming_logo_path = self._get_img_path("Pending")
        finished_logo_path = self._get_img_path("Ended")
        gradient_color = pick_gradient_color()
        accent_dark_color = darken_color(pixie.parse_color(gradient_color.color_list[-1]), 0.3)
        accent_dark_color_tran = pixie.Color(accent_dark_color.r, accent_dark_color.g, accent_dark_color.b, 136 / 255)
        mild_text_color = pixie.Color(0, 0, 0, 136 / 255)
        mild_ext_text_color = pixie.Color(0.2, 0.2, 0.2, 1)

        title_text = StyledString("近日算法竞赛", 'H', 96, padding_bottom=4,
                                  font_color=accent_dark_color)
        subtitle_text = StyledString("Recent Competitive Programming Competitions", 'H', 28, padding_bottom=108,
                                     font_color=accent_dark_color_tran)
        tips_title_text = StyledString("Tips:", 'H', 36, padding_bottom=64)
        tips_detail_text = StyledString("数据源于平台数据爬取/API调用/手动填写，仅供参考", 'M', 28,
                                        line_multiplier=1.32, padding_bottom=64,
                                        max_width=(self._CONTENT_WIDTH - 108 - # 考虑右边界，不然画出去了
                                                   calculate_width(tips_title_text) - 12 - 48))
        generator_text = StyledString("Contest List Renderer", 'H', 36,
                                            font_color=(0, 0, 0, 208), padding_bottom=16)
        generation_info_text = StyledString(f'Generated at {datetime.now().strftime("%Y/%m/%d %H:%M:%S")}.\n'
                                            f'Initiated by OBot {Constants.core_version}.\n'
                                            f'{gradient_color.name}.', 'B', 20,
                                            line_multiplier=1.32, font_color=mild_text_color)
        none_title_text = StyledString("最近没有比赛，放松一下吧", 'H', 52, padding_bottom=72)
        running_title_text = StyledString("RUNNING 正在进行", 'H', 52, padding_bottom=72,
                                          font_color=mild_ext_text_color)
        upcoming_title_text = StyledString("PENDING 即将进行", 'H', 52, padding_bottom=72,
                                           font_color=mild_ext_text_color)
        finished_title_text = StyledString("ENDED 已结束", 'H', 52, padding_bottom=72,
                                           font_color=mild_ext_text_color)

        width, height = self._CONTENT_WIDTH, calculate_height([title_text, subtitle_text, tips_title_text,
                                                               generator_text, generation_info_text]) + 264
        if len(self._upcoming_contests) == 0 and len(self._running_contests) == 0 and len(self._finished_contests) == 0:
            height += calculate_height(none_title_text)
        else:
            for _contests, _type_title_text in [(self._running_contests, running_title_text),
                                                (self._upcoming_contests, upcoming_title_text),
                                                (self._finished_contests, finished_title_text)]:
                if len(_contests) > 0:
                    height += calculate_height(_type_title_text)
                    height += sum([contest.calculate_height() for contest in _contests]) + self._TYPE_PADDING
                    height += self._CONTEST_PADDING * (len(_contests) - 1)  # 各比赛间的 padding

        img = pixie.Image(width + 64, height + 64)
        img.fill(pixie.Color(0, 0, 0, 1))  # 填充黑色背景

        draw_gradient_rect(img, Loc(32, 32, self._CONTENT_WIDTH, height), gradient_color,
                           GradientDirection.DIAGONAL_RIGHT_TO_LEFT, 96)
        draw_mask_rect(img, Loc(32, 32, self._CONTENT_WIDTH, height), pixie.Color(1, 1, 1, 0.7), 96)

        current_x, current_y = 108, 168
        draw_img(img, logo_path, Loc(106, 181, 102, 102), accent_dark_color)
        current_y = draw_text(img, title_text, 232, current_y)
        current_y = draw_text(img, subtitle_text, current_x, current_y)

        if len(self._running_contests) == 0 and len(self._upcoming_contests) == 0 and len(self._finished_contests) == 0:
            current_y = draw_text(img, none_title_text, current_x, current_y)
        else:
            for _contests, _type_logo_path, _type_title_text in [(self._running_contests, running_logo_path, running_title_text),
                                                                 (self._upcoming_contests, upcoming_logo_path, upcoming_title_text),
                                                                 (self._finished_contests, finished_logo_path, finished_title_text)]:
                if len(_contests) > 0:
                    draw_img(img, _type_logo_path, Loc(current_x, current_y + 10, 50, 50), mild_ext_text_color)
                    current_y = draw_text(img, _type_title_text, current_x + 50 + 28, current_y)
                    current_y -= self._CONTEST_PADDING
                    for contest in _contests:
                        current_y += self._CONTEST_PADDING
                        current_y = contest.render_item(img, current_y)
                    current_y += self._TYPE_PADDING

        draw_text(img, tips_title_text, current_x, current_y)
        current_y = draw_text(img, tips_detail_text, current_x + calculate_width(tips_title_text) + 12, current_y + 8)
        current_y = draw_text(img, generator_text, current_x, current_y)
        draw_text(img, generation_info_text, current_x, current_y)

        return img
