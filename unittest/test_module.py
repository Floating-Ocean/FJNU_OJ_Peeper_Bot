import json
import random
import unittest
from dataclasses import asdict

from aiohttp import ClientConnectorSSLError
from botpy.errors import ServerError

from src.core.exception import handle_exception, UnauthorizedError, ModuleRuntimeError
from src.core.tools import png2jpg, decode_range
from src.module.color_rand import load_colors, _colors, render_color_card, add_qrcode
from src.platform.cp.atcoder import AtCoder
from src.platform.cp.codeforces import Codeforces


class Module(unittest.TestCase):
    def test_color_rand(self):
        load_colors()
        picked_color = random.choice(_colors)
        color_card = render_color_card(picked_color)
        color_card.write_file("test.png")

    def test_color_qrcode(self):
        load_colors()
        picked_color = random.choice(_colors)
        color_card = render_color_card(picked_color)
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
            json.dump({handle: asdict(predict)
                       for handle, predict in Codeforces._fetch_contest_predict(contest_id).items()},
                      json_file, ensure_ascii=False, indent=4)

    def test_cf_rand_problem(self):
        print(decode_range("2100", (3, 4)))

    def test_atc_rand_problem(self):
        contest_type = "common"
        limit = "2100"
        print(AtCoder.get_prob_filtered(contest_type, limit))

    def test_error_handle(self):
        print(handle_exception(ServerError('This is a test server error.')))
        print(handle_exception(ClientConnectorSSLError(None, OSError('This is a test client connector ssl error.'))))
        print(handle_exception(UnauthorizedError('阿弥诺斯')))
        print(handle_exception(ModuleRuntimeError('IndexError(...)')))


if __name__ == '__main__':
    unittest.main()
