import random
import unittest

from src.modules.color_rand import load_colors, _colors, generate_color_card


class Module(unittest.TestCase):
    def test_color_rand(self):
        load_colors()
        picked_color = random.choice(_colors)
        color_card = generate_color_card(picked_color)
        color_card.write_file("test.png")


if __name__ == '__main__':
    unittest.main()
