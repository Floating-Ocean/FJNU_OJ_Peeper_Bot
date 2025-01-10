import json
import random
import unittest
from dataclasses import asdict

from src.core.tools import png2jpg
from src.modules.color_rand import load_colors, _colors, generate_color_card, add_qrcode
from src.platforms.codeforces import Codeforces


class Module(unittest.TestCase):
    def test_color_rand(self):
        load_colors()
        picked_color = random.choice(_colors)
        color_card = generate_color_card(picked_color)
        color_card.write_file("test.png")

    def test_color_qrcode(self):
        load_colors()
        picked_color = random.choice(_colors)
        color_card = generate_color_card(picked_color)
        color_card.write_file("test.png")
        add_qrcode("test.png", picked_color)
        png2jpg("test.png")

    def test_cf_user_standings(self):
        handle = "FloatingOcean"
        contest_id = "2043"
        contest_info, standings_info = Codeforces.get_user_contest_standings(handle, contest_id)

        content = (f"[Codeforces] {handle} 比赛榜单查询\n\n"
                   f"{contest_info}")
        if standings_info is not None:
            if len(standings_info) > 0:
                content += '\n\n'
                content += '\n\n'.join(standings_info)
            else:
                content += '\n\n暂无榜单信息'

        print(content)

    def test_cf_predict(self):
        with open('data.json', 'w', encoding='utf-8') as json_file:
            contest_id = "2043"
            json.dump([asdict(each) for each in Codeforces.get_contest_predict(contest_id)],
                      json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    unittest.main()
