import random
import unittest

from src.modules.color_rand import load_colors, _colors, generate_color_card, add_qrcode


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


if __name__ == '__main__':
    unittest.main()
