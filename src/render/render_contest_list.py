import time
from datetime import datetime

import pixie
from easy_pixie import StyledString, calculate_height, draw_text, calculate_width, Loc, draw_img, \
    pick_gradient_color, draw_gradient_rect, GradientDirection, draw_mask_rect, darken_color

from src.core.constants import Constants
from src.core.tools import format_timestamp, format_timestamp_diff, format_seconds
from src.platform.model import Contest
from src.render.model import Renderer, RenderableSection


_CONTENT_WIDTH = 1024
_TOP_PADDING = 168
_BOTTOM_PADDING = 128
_SIDE_PADDING = 108
_CONTEST_PADDING = 108
_SECTION_PADDING = 108
_TYPE_PADDING = 128


class _ContestItem(RenderableSection):
    def __init__(self, contest: Contest, idx: int):
        self._contest = contest
        self._idx = idx + 1

        if int(time.time()) >= self._contest.start_time:
            _status = self._contest.phase  # 用于展示"比赛中"，或者诸如 Codeforces 平台的 "正在重测中"
        else:
            _status = format_timestamp_diff(int(time.time()) - self._contest.start_time)

        self._00_idx_text = StyledString("00",'H', 72)
        self._begin_x = _SIDE_PADDING + calculate_width(self._00_idx_text) + 48
        max_width = _CONTENT_WIDTH + 32 - self._begin_x - 48 - _SIDE_PADDING

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

    def get_height(self):
        return calculate_height([self._subtitle_text, self._title_text, self._time_text, self._status_text])

    def render(self, img: pixie.Image, x: int, y: int) -> int:
        current_x, current_y = self._begin_x - _SIDE_PADDING + x - calculate_width(self._idx_text) - 48, y

        draw_text(img, self._idx_text, current_x, current_y - 14)
        current_x = self._begin_x

        draw_img(img, ContestListRenderer.get_img_path(self._contest.platform), Loc(current_x, current_y + 4, 20, 20),
                 pixie.Color(0, 0, 0, 1))
        current_y = draw_text(img, self._subtitle_text, current_x + 28, current_y)
        current_y = draw_text(img, self._title_text, current_x, current_y)
        current_y = draw_text(img, self._time_text, current_x, current_y)
        current_y = draw_text(img, self._status_text, current_x, current_y)

        return current_y


class _TitleSection(RenderableSection):

    def __init__(self, accent_color: str):
        self.accent_dark_color = darken_color(pixie.parse_color(accent_color), 0.3)
        self.accent_dark_color_tran = pixie.Color(self.accent_dark_color.r, self.accent_dark_color.g,
                                                  self.accent_dark_color.b, 136 / 255)
        self.logo_path = ContestListRenderer.get_img_path("Contest")
        self.title_text = StyledString("近日算法竞赛", 'H', 96, padding_bottom=4,
                                       font_color=self.accent_dark_color)
        self.subtitle_text = StyledString("Recent Competitive Programming Competitions", 'H', 28,
                                          font_color=self.accent_dark_color_tran)

    def render(self, img: pixie.Image, x: int, y: int) -> int:
        draw_img(img, self.logo_path, Loc(106, 181, 102, 102), self.accent_dark_color)

        current_x, current_y = x, y
        current_y = draw_text(img, self.title_text, 232, current_y)
        current_y = draw_text(img, self.subtitle_text, current_x, current_y)

        return current_y

    def get_height(self):
        return calculate_height([self.title_text, self.subtitle_text])


class _ContestsSection(RenderableSection):

    def __init__(self, running_contests: list[_ContestItem], upcoming_contests: list[_ContestItem],
                 finished_contests: list[_ContestItem]):
        self.running_contests = running_contests
        self.upcoming_contests = upcoming_contests
        self.finished_contests = finished_contests
        self.running_logo_path = ContestListRenderer.get_img_path("Running")
        self.upcoming_logo_path = ContestListRenderer.get_img_path("Pending")
        self.finished_logo_path = ContestListRenderer.get_img_path("Ended")
        self.mild_ext_text_color = pixie.Color(0.2, 0.2, 0.2, 1)
        self.none_title_text = StyledString("最近没有比赛，放松一下吧", 'H', 52, padding_bottom=72)
        self.running_title_text = StyledString("RUNNING 正在进行", 'H', 52, padding_bottom=72,
                                               font_color=self.mild_ext_text_color)
        self.upcoming_title_text = StyledString("PENDING 即将进行", 'H', 52, padding_bottom=72,
                                                font_color=self.mild_ext_text_color)
        self.finished_title_text = StyledString("ENDED 已结束", 'H', 52, padding_bottom=72,
                                                font_color=self.mild_ext_text_color)

    def render(self, img: pixie.Image, x: int, y: int) -> int:
        current_x, current_y = x, y

        if len(self.running_contests) == 0 and len(self.upcoming_contests) == 0 and len(self.finished_contests) == 0:
            current_y = draw_text(img, self.none_title_text, current_x, current_y)
        else:
            current_y -= _TYPE_PADDING
            for _contests, _type_logo_path, _type_title_text in \
                    [(self.running_contests, self.running_logo_path, self.running_title_text),
                     (self.upcoming_contests, self.upcoming_logo_path, self.upcoming_title_text),
                     (self.finished_contests, self.finished_logo_path, self.finished_title_text)]:
                if len(_contests) > 0:
                    current_y += _TYPE_PADDING
                    draw_img(img, _type_logo_path, Loc(current_x, current_y + 10, 50, 50), self.mild_ext_text_color)
                    current_y = draw_text(img, _type_title_text, current_x + 50 + 28, current_y)
                    current_y -= _CONTEST_PADDING
                    for contest in _contests:
                        current_y += _CONTEST_PADDING
                        current_y = contest.render(img, current_x, current_y)

        return current_y

    def get_height(self):
        height = 0
        if len(self.upcoming_contests) == 0 and len(self.running_contests) == 0 and len(self.finished_contests) == 0:
            height += calculate_height(self.none_title_text)
        else:
            height -= _TYPE_PADDING
            for _contests, _type_title_text in [(self.running_contests, self.running_title_text),
                                                (self.upcoming_contests, self.upcoming_title_text),
                                                (self.finished_contests, self.finished_title_text)]:
                if len(_contests) > 0:
                    height += calculate_height(_type_title_text)
                    height += sum([contest.get_height() for contest in _contests]) + _TYPE_PADDING
                    height += _CONTEST_PADDING * (len(_contests) - 1)  # 各比赛间的 padding
        return height


class _CopyrightSection(RenderableSection):

    def __init__(self, gradient_color_name: str):
        self.mild_text_color = pixie.Color(0, 0, 0, 136 / 255)
        self.tips_title_text = StyledString("Tips:", 'H', 36, padding_bottom=64)
        self.tips_detail_text = StyledString("数据源于平台数据爬取/API调用/手动填写，仅供参考", 'M', 28,
                                        line_multiplier=1.32, padding_bottom=64,
                                        max_width=(_CONTENT_WIDTH - 108 -  # 考虑右边界，不然画出去了
                                                   calculate_width(self.tips_title_text) - 12 - 48))
        self.generator_text = StyledString("Contest List Renderer", 'H', 36,
                                      font_color=(0, 0, 0, 208), padding_bottom=16)
        self.generation_info_text = StyledString(f'Generated at {datetime.now().strftime("%Y/%m/%d %H:%M:%S")}.\n'
                                            f'Initiated by OBot\'s ACM {Constants.core_version}.\n'
                                            f'{gradient_color_name}.', 'B', 20,
                                            line_multiplier=1.32, font_color=self.mild_text_color)

    def render(self, img: pixie.Image, x: int, y: int) -> int:
        current_x, current_y = x, y

        draw_text(img, self.tips_title_text, current_x, current_y)
        current_y = draw_text(img, self.tips_detail_text, current_x + calculate_width(self.tips_title_text) + 12, current_y + 8)
        current_y = draw_text(img, self.generator_text, current_x, current_y)
        draw_text(img, self.generation_info_text, current_x, current_y)

        return current_y

    def get_height(self):
        return calculate_height([self.tips_title_text, self.generator_text, self.generation_info_text])


class ContestListRenderer(Renderer):
    """渲染比赛列表"""

    def __init__(self, running_contests: list[Contest], upcoming_contests: list[Contest], finished_contests: list[Contest]):
        self._raw_running_contests = running_contests
        self._raw_upcoming_contests = upcoming_contests
        self._raw_finished_contests = finished_contests
        self._running_contests = [_ContestItem(contest, idx) for idx, contest in enumerate(running_contests)]
        self._upcoming_contests = [_ContestItem(contest, idx) for idx, contest in enumerate(upcoming_contests)]
        self._finished_contests = [_ContestItem(contest, idx) for idx, contest in enumerate(finished_contests)]

    def render(self) -> pixie.Image:
        gradient_color = pick_gradient_color()

        title_section = _TitleSection(gradient_color.color_list[-1])
        contests_section = _ContestsSection(self._running_contests, self._upcoming_contests, self._finished_contests)
        copyright_section = _CopyrightSection(gradient_color.name)

        render_sections = [title_section, contests_section, copyright_section]

        width, height = (_CONTENT_WIDTH,
                         sum([section.get_height() for section in render_sections]) +
                         _SECTION_PADDING * (len(render_sections) - 1) + _TOP_PADDING + _BOTTOM_PADDING)

        img = pixie.Image(width + 64, height + 64)
        img.fill(pixie.Color(0, 0, 0, 1))  # 填充黑色背景

        draw_gradient_rect(img, Loc(32, 32, _CONTENT_WIDTH, height), gradient_color,
                           GradientDirection.DIAGONAL_RIGHT_TO_LEFT, 96)
        draw_mask_rect(img, Loc(32, 32, _CONTENT_WIDTH, height), pixie.Color(1, 1, 1, 0.7), 96)

        current_x, current_y = _SIDE_PADDING, _TOP_PADDING - _SECTION_PADDING

        for section in render_sections:
            current_y += _SECTION_PADDING
            current_y = section.render(img, current_x, current_y)

        return img
