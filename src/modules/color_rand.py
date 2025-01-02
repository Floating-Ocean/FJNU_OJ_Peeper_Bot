import json
import random
from datetime import datetime

import pixie

from src.core.command import command
from src.core.constants import Constants
from src.modules.message import RobotMessage

_lib_path = Constants.config["lib_path"] + "\\Color-Rand"
__color_rand_version__ = "v1.0.1"

_colors = []


def register_module():
    pass


def load_colors():
    with open(_lib_path + "\\chinese_traditional.json", 'r', encoding="utf-8") as f:
        _colors.clear()
        _colors.extend(json.load(f))


def choose_text_color(color: dict) -> tuple[int, int, int]:
    luminance = 0.299 * color["RGB"][0] + 0.587 * color["RGB"][1] + 0.114 * color["RGB"][2]
    return (18, 18, 18) if luminance > 128 else (252, 252, 252)


def rgb_to_hsv(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
    max_val, min_val = max(r, g, b), min(r, g, b)
    delta = max_val - min_val
    if delta == 0:
        h = 0
    elif max_val == r:
        h = ((g - b) / delta) % 6
    elif max_val == g:
        h = (b - r) / delta + 2
    else:
        h = (r - g) / delta + 4
    return (round(h * 60) + 360) % 360, round(0 if max_val == 0 else delta / max_val * 100), round(max_val * 100)


def draw_text(img: pixie.Image, content: str, x: int, y: int, font_weight: str, font_size: int, color: dict) -> int:
    font = pixie.read_font(_lib_path + f"\\data\\OPPOSans-{font_weight}.ttf")
    font.size = font_size
    font_color = choose_text_color(color)
    font.paint.color = pixie.Color(font_color[0] / 255, font_color[1] / 255, font_color[2] / 255, 1)
    img.fill_text(font, content, pixie.translate(x, y))
    return font.layout_bounds(content).x


def draw_round_rect(image: pixie.Image, paint: pixie.Paint, x: int, y: int, width: int, height: int, round_size: float):
    ctx = image.new_context()
    ctx.fill_style = paint
    ctx.rounded_rect(x, y, width, height, round_size, round_size, round_size, round_size)
    ctx.fill()


def generate_color_card(color) -> pixie.Image:
    hex_text = "#FF" + color["hex"].upper()[1:]
    rgb_text = ", ".join([f"{val}" for val in color["RGB"]])
    hsv_text = ", ".join([f"{val}" for val in rgb_to_hsv(color["RGB"])])
    img = pixie.Image(432, 276)
    img.fill(pixie.Color(0, 0, 0, 1))
    paint_bg = pixie.Paint(pixie.SOLID_PAINT)
    paint_bg.color = pixie.Color(color["RGB"][0] / 255, color["RGB"][1] / 255, color["RGB"][2] / 255, 1.0)
    draw_round_rect(img, paint_bg, 16, 16, 400, 244, 20)
    draw_text(img, f"Color Collect - {color['pinyin']}", 36 + 16, 30 + 16, 'H', 12, color)
    draw_text(img, f"{color['name']}", 36 + 16, 58 + 16, 'H', 36, color)
    hex_width = draw_text(img, f"{hex_text}", 36 + 16, 118 + 16, 'M', 18, color)
    rgb_width = draw_text(img, f"{rgb_text}", 36 + 16, 154 + 16, 'M', 18, color)
    hsv_width = draw_text(img, f"{hsv_text}", 36 + 16, 190 + 16, 'M', 18, color)
    draw_text(img, "HEX", 36 + hex_width + 16 + 8, 118 + 16 + 6, 'R', 12, color)
    draw_text(img, "RGB", 36 + rgb_width + 16 + 8, 154 + 16 + 6, 'R', 12, color)
    draw_text(img, "HSV", 36 + hsv_width + 16 + 8, 190 + 16 + 6, 'R', 12, color)
    return img


@command(tokens=["color", "颜色", "色", "来个颜色", "来个色卡", "色卡"])
async def reply_color_rand(message: RobotMessage):
    load_colors()
    picked_color = random.choice(_colors)

    color_card = generate_color_card(picked_color)
    img_path = _lib_path + f"\\output\\{datetime.now().timestamp()}.png"
    color_card.write_file(img_path)

    name = picked_color["name"]
    pinyin = picked_color["pinyin"]
    hex_text = "#FF" + picked_color["hex"].upper()[1:]
    rgb_text = ", ".join([f"{val}" for val in picked_color["RGB"]])
    hsv_text = ", ".join([f"{val}" for val in rgb_to_hsv(picked_color["RGB"])])

    await message.reply(f"[Color] {name} {pinyin}\n"
                        f"HEX: {hex_text}\nRGB: {rgb_text}\nHSV: {hsv_text}", img_path=img_path, modal_words=False)
