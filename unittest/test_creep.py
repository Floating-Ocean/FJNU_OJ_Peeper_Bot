import json
import unittest

from src.platforms.atcoder import AtCoder
from src.platforms.codeforces import Codeforces
from src.platforms.nowcoder import NowCoder


class Creep(unittest.TestCase):
    def test_codeforces(self):
        p = Codeforces.get_contest_list()
        self.assertIsNotNone(p)
        print(json.dumps(p, indent=4, ensure_ascii=False))

    def test_atcoder(self):
        p = AtCoder.get_contest_list()
        self.assertIsNotNone(p)
        print(json.dumps(p, indent=4, ensure_ascii=False))

    def test_nowcoder(self):
        p = NowCoder.get_contest_list()
        self.assertIsNotNone(p)
        print(json.dumps(p, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    unittest.main()
