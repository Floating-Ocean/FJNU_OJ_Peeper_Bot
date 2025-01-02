import json
import os
import random
from colorsys import rgb_to_hsv
from datetime import datetime, timedelta

import pixie

from src.core.command import command
from src.core.constants import Constants
from src.core.tools import check_is_float, png2jpg
from src.modules.message import RobotMessage

_lib_path = os.path.join(Constants.config["lib_path"], "Color-Rand")
__color_rand_version__ = "v1.0.2"

_colors = []


def register_module():
    pass


def load_colors():
    with open(os.path.join(_lib_path, "chinese_traditional.json"), 'r', encoding="utf-8") as f:
        _colors.clear()
        _colors.extend(json.load(f))


def clean_tmp_hours_ago():
    one_hour_ago = datetime.now() - timedelta(hours=1)
    output_path = os.path.join(_lib_path, "output")
    for filename in os.listdir(output_path):
        for suffix in [".png", ".jpg"]:
            prefix = filename.replace(suffix, "")
            if filename.endswith(suffix) and check_is_float(prefix):
                file_mtime = datetime.fromtimestamp(float(prefix))
                if file_mtime < one_hour_ago:  # 清理一小时前的缓存图片
                    os.remove(os.path.join(_lib_path, "output", filename))


def choose_text_color(color: dict) -> tuple[int, int, int]:
    luminance = 0.299 * color["RGB"][0] + 0.587 * color["RGB"][1] + 0.114 * color["RGB"][2]
    return (18, 18, 18) if luminance > 128 else (252, 252, 252)


def draw_text(img: pixie.Image, content: str, x: int, y: int, font_weight: str, font_size: int, color: dict) -> int:
    font = pixie.read_font(os.path.join(_lib_path, "data", f"OPPOSans-{font_weight}.ttf"))
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


def transform_color(color: dict) -> tuple[str, str, str]:
    hex_text = "#FF" + color["hex"].upper()[1:]
    rgb_text = ", ".join([f"{val}" for val in color["RGB"]])
    h, s, v = rgb_to_hsv(color["RGB"][0], color["RGB"][1], color["RGB"][2])
    hsv_text = ", ".join([f"{val}" for val in [round(h * 360), round(s * 100), int(v)]])
    return hex_text, rgb_text, hsv_text


def generate_color_card(color) -> pixie.Image:
    hex_text, rgb_text, hsv_text = transform_color(color)
    img = pixie.Image(832, 520)
    img.fill(pixie.Color(0, 0, 0, 1))
    paint_bg = pixie.Paint(pixie.SOLID_PAINT)
    paint_bg.color = pixie.Color(color["RGB"][0] / 255, color["RGB"][1] / 255, color["RGB"][2] / 255, 1.0)
    draw_round_rect(img, paint_bg, 16, 16, 800, 488, 48)
    draw_text(img, f"Color Collect - {color['pinyin']}", 72 + 16, 60 + 16, 'H', 24, color)
    draw_text(img, color['name'], 72 + 16, 116 + 16, 'H', 72, color)
    hex_width = draw_text(img, hex_text, 72 + 16, 236 + 16, 'M', 36, color)
    rgb_width = draw_text(img, rgb_text, 72 + 16, 308 + 16, 'M', 36, color)
    hsv_width = draw_text(img, hsv_text, 72 + 16, 380 + 16, 'M', 36, color)
    draw_text(img, "HEX", 72 + hex_width + 16 + 16, 236 + 16 + 12, 'R', 24, color)
    draw_text(img, "RGB", 72 + rgb_width + 16 + 16, 308 + 16 + 12, 'R', 24, color)
    draw_text(img, "HSV", 72 + hsv_width + 16 + 16, 380 + 16 + 12, 'R', 24, color)
    return img


@command(tokens=["color", "颜色", "色", "来个颜色", "来个色卡", "色卡"])
async def reply_color_rand(message: RobotMessage):
    load_colors()
    clean_tmp_hours_ago()
    picked_color = random.choice(_colors)

    color_card = generate_color_card(picked_color)
    img_path = os.path.join(_lib_path, "output", f"{datetime.now().timestamp()}.png")
    color_card.write_file(img_path)

    name = picked_color["name"]
    pinyin = picked_color["pinyin"]
    hex_text, rgb_text, hsv_text = transform_color(picked_color)

    await message.reply(f"[Color] {name} {pinyin}\nHEX: {hex_text}\nRGB: {rgb_text}\nHSV: {hsv_text}",
                        img_path=png2jpg(img_path), modal_words=False)
