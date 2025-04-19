import os
import random
import unittest
from datetime import datetime

from src.core.constants import Constants
from src.core.util.tools import png2jpg
from src.module.color_rand import load_colors, _colors, transform_color, add_qrcode
from src.platform.manual.manual import ManualPlatform
from src.platform.online.atcoder import AtCoder
from src.platform.online.codeforces import Codeforces
from src.platform.online.nowcoder import NowCoder
from src.render.html.markdown import md_to_html, render_md_html
from src.render.pixie.render_color_card import ColorCardRenderer
from src.render.pixie.render_contest_list import ContestListRenderer


class Render(unittest.TestCase):

    def test_color_rand(self):
        load_colors()
        picked_color = random.choice(_colors)
        hex_raw_text, rgb_raw_text, hsv_raw_text = transform_color(picked_color)
        color_card = ColorCardRenderer(picked_color, hex_raw_text, rgb_raw_text, hsv_raw_text).render()
        self.assertIsNotNone(color_card)
        color_card.write_file("test_color_rand.png")

    def test_color_qrcode(self):
        load_colors()
        picked_color = random.choice(_colors)
        hex_raw_text, rgb_raw_text, hsv_raw_text = transform_color(picked_color)
        color_card = ColorCardRenderer(picked_color, hex_raw_text, rgb_raw_text, hsv_raw_text).render()
        self.assertIsNotNone(color_card)
        color_card.write_file("test_color_qrcode.png")
        add_qrcode("test_color_qrcode.png", picked_color)
        png2jpg("test_color_qrcode.png")

    def test_contest_list(self):
        upcoming_contests, running_contests, finished_contests = [], [], []
        for platform in [Codeforces, AtCoder, NowCoder, ManualPlatform]:
            upcoming, running, finished = platform.get_contest_list()
            upcoming_contests.extend(upcoming)
            running_contests.extend(running)
            finished_contests.extend(finished)

        upcoming_contests.sort(key=lambda c: c.start_time)
        running_contests.sort(key=lambda c: c.start_time)
        finished_contests.sort(key=lambda c: c.start_time)

        contest_list_img = ContestListRenderer(upcoming_contests, running_contests, finished_contests).render()
        self.assertIsNotNone(contest_list_img)
        contest_list_img.write_file("test_contest_list.png")

    def test_cook_md(self):
        _lib_path = os.path.join(Constants.config["lib_path"], "How-To-Cook")
        hui_guo_rou_path = os.path.join(_lib_path, "lib", "dishes", "meat_dish", "回锅肉", "回锅肉.md")
        css_path = os.path.join(_lib_path, "style", "index.css")
        self.assertTrue(os.path.exists(hui_guo_rou_path))
        extra_body = f"""
        <div class="copyright">
            <div class="tool-container">
                <p class="tool-name">How to Cook</p>
                <p class="tool-version">v1.4.0</p>
            </div>
            <p class="generation-info">Generated at {datetime.now().strftime("%Y/%m/%d %H:%M:%S")}.<br>
                                       Initiated by OBot\'s ACM {Constants.core_version}.<br>
                                       Wish you everything goes well.</p>
        </div>
        """
        md_html = md_to_html(hui_guo_rou_path, css_path, extra_body)
        print(md_html)
        self.assertIsNotNone(md_html)
        render_md_html(hui_guo_rou_path, css_path, "回锅肉.png", extra_body)

if __name__ == '__main__':
    unittest.main()
