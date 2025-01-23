import json
import unittest

from dataclasses import asdict

from src.platform.cp.atcoder import AtCoder
from src.platform.cp.codeforces import Codeforces
from src.platform.cp.nowcoder import NowCoder
from src.platform.it.clist import Clist


class Platform(unittest.TestCase):
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

    def test_clist(self):
        problems = Clist.api("problem", resource_id=93, rating__gte=800, rating__lte=1000,
                             url__regex=r'^(?!https:\/\/atcoder\.jp\/contests\/(abc|arc|agc|ahc)).*')
        self.assertIsNotNone(problems)
        print(json.dumps(problems, indent=4, ensure_ascii=False))

    def test_nowcoder_user(self):
        handle = "144128559"
        p = NowCoder.get_user_info(handle)
        print(p[0])
        print(p[1])
        self.assertIsNotNone(p)

    def test_nowcoder_user_last_contest(self):
        handle = "144128559"
        p = NowCoder.get_user_last_contest(handle)
        print(p)
        self.assertIsNotNone(p)


if __name__ == '__main__':
    unittest.main()
