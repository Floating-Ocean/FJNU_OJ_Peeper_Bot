import json
import random
import unittest
from dataclasses import asdict
from datetime import datetime

from aiohttp import ClientConnectorSSLError
from botpy.errors import ServerError

from src.core.exception import handle_exception, UnauthorizedError, ModuleRuntimeError
from src.core.tools import png2jpg, decode_range
from src.module.color_rand import load_colors, _colors, add_qrcode
from src.platform.online.atcoder import AtCoder
from src.platform.online.codeforces import Codeforces
from src.platform.model import Contest, DynamicContest


class Module(unittest.TestCase):

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

    def test_contest_json(self):
        contest = DynamicContest(
            platform='ICPC',
            abbr='武汉邀请赛',
            name='2025年ICPC国际大学生程序设计竞赛全国邀请赛（武汉）',
            start_time=int(datetime.strptime("2025-04-27T10:00:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()),
            duration=60*60*5,
            supplement='华中科技大学'
        )
        print(json.dumps(asdict(contest), ensure_ascii=False, indent=4))


if __name__ == '__main__':
    unittest.main()
