import json
import unittest

from dataclasses import asdict

from src.platforms.atcoder import AtCoder
from src.platforms.codeforces import Codeforces
from src.platforms.nowcoder import NowCoder


class Creep(unittest.TestCase):
    def test_codeforces_contest_list(self):
        p = Codeforces.get_contest_list()
        self.assertIsNotNone(p)
        print(json.dumps([asdict(d) for d in p], indent=4, ensure_ascii=False))

    def test_atcoder_contest_list(self):
        p = AtCoder.get_contest_list()
        self.assertIsNotNone(p)
        print(json.dumps([asdict(d) for d in p], indent=4, ensure_ascii=False))

    def test_nowcoder_contest_list(self):
        p = NowCoder.get_contest_list()
        self.assertIsNotNone(p)
        print(json.dumps([asdict(d) for d in p], indent=4, ensure_ascii=False))

    def test_atcoder_user(self):
        handle = "FluctuateOcean"
        p = AtCoder.get_user_info(handle)
        self.assertIsNotNone(p)
        # print(json.dumps([asdict(d) for d in p], indent=4, ensure_ascii=False))


if __name__ == '__main__':
    unittest.main()
