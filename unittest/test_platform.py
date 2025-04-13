import json
import unittest

from dataclasses import asdict

from src.platform.online.atcoder import AtCoder
from src.platform.online.codeforces import Codeforces
from src.platform.online.nowcoder import NowCoder
from src.platform.collect.clist import Clist


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

    def test_codeforces_user_card(self):
        test_handles = ['floatingocean', 'qwedc001', 'jiangly', 'Lingyu0qwq', 'I_am_real_wx', 'BingYu2023', 'C10udz']
        for handle in test_handles:
            img = Codeforces.get_user_id_card(handle)
            self.assertIsNotNone(img)
            img.write_file(f"cf_user_card_{handle}.png")

    def test_atcoder_user_card(self):
        test_handles = ['floatingocean', 'qwedc001', 'jiangly', 'Lingyu0qwq']
        for handle in test_handles:
            img = AtCoder.get_user_id_card(handle)
            self.assertIsNotNone(img)
            img.write_file(f"atc_user_card_{handle}.png")

    def test_nowcoder_user_card(self):
        test_handles = ['144128559', '140690880', '737857302', '329687984', '815516497', '882260751']
        for handle in test_handles:
            img = NowCoder.get_user_id_card(handle)
            self.assertIsNotNone(img)
            img.write_file(f"nk_user_card_{handle}.png")


if __name__ == '__main__':
    unittest.main()
