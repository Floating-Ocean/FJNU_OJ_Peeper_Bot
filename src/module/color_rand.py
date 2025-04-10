import json
import os
import random
from colorsys import rgb_to_hsv

import pixie
import qrcode
from PIL import Image
from easy_pixie import choose_text_color, draw_rect, draw_text, StyledString, color_to_tuple, calculate_string_width, \
    Loc
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.main import QRCode

from src.core.command import command
from src.core.constants import Constants
from src.core.output_cached import get_cached_prefix
from src.core.tools import png2jpg
from src.module.message import RobotMessage

_lib_path = os.path.join(Constants.config["lib_path"], "Color-Rand")
__color_rand_version__ = "v1.1.1"

_colors = []


def register_module():
    pass


def load_colors():
    with open(os.path.join(_lib_path, "chinese_traditional.json"), 'r', encoding="utf-8") as f:
        _colors.clear()
        _colors.extend(json.load(f))


def transform_color(color: dict) -> tuple[str, str, str]:
    hex_text = "#FF" + color["hex"].upper()[1:]
    rgb_text = ", ".join([f"{val}" for val in color["RGB"]])
    h, s, v = rgb_to_hsv(color["RGB"][0], color["RGB"][1], color["RGB"][2])
    hsv_text = ", ".join([f"{val}" for val in [round(h * 360), round(s * 100), int(v)]])
    return hex_text, rgb_text, hsv_text


def render_color_card(color: dict) -> pixie.Image:
    hex_raw_text, rgb_raw_text, hsv_raw_text = transform_color(color)

    img = pixie.Image(1664, 1040)
    img.fill(pixie.Color(0, 0, 0, 1))

    paint_bg = pixie.Paint(pixie.SOLID_PAINT)
    paint_bg.color = pixie.parse_color(color["hex"])
    draw_rect(img, paint_bg, Loc(32, 32, 1600, 976), 96)

    text_color = choose_text_color(paint_bg.color)
    title_raw_text = f"Color Collect - {color['pinyin']}"

    title_text = StyledString(title_raw_text, 'H', 48, font_color=text_color, padding_bottom=52)
    name_text = StyledString(color['name'], 'H', 144, font_color=text_color, padding_bottom=60)
    hex_text = StyledString(hex_raw_text, 'M', 72, font_color=text_color, padding_bottom=80)
    rgb_text = StyledString(rgb_raw_text, 'M', 72, font_color=text_color, padding_bottom=80)
    hsv_text = StyledString(hsv_raw_text, 'M', 72, font_color=text_color, padding_bottom=80)
    hex_tag = StyledString("HEX", 'R', 48, font_color=text_color, padding_bottom=56)
    rgb_tag = StyledString("RGB", 'R', 48, font_color=text_color, padding_bottom=56)
    hsv_tag = StyledString("HSV", 'R', 48, font_color=text_color, padding_bottom=56)

    current_x, current_y = 144 + 32, 120 + 32
    current_y = draw_text(img, title_text, current_x, current_y)
    current_y = draw_text(img, name_text, current_x, current_y)
    draw_text(img, hex_text, current_x, current_y)
    current_y += 24
    current_y = draw_text(img, hex_tag, current_x + calculate_string_width(hex_text) + 32, current_y)
    draw_text(img, rgb_text, current_x, current_y)
    current_y += 24
    current_y = draw_text(img, rgb_tag, current_x + calculate_string_width(rgb_text) + 32, current_y)
    draw_text(img, hsv_text, current_x, current_y)
    current_y += 24
    draw_text(img, hsv_tag, current_x + calculate_string_width(hsv_text) + 32, current_y)

    return img


def add_qrcode(target_path: str, color: dict):
    qr = QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8)

    hex_clean = color["hex"][1:].lower()
    qr.add_data(f"https://gradients.app/zh/color/{hex_clean}")

    font_color = choose_text_color(pixie.parse_color(color["hex"]))
    font_transparent_color = pixie.Color(font_color.r, font_color.g, font_color.b, 0)
    qrcode_img = qr.make_image(image_factory=StyledPilImage,
                               module_drawer=RoundedModuleDrawer(), eye_drawer=RoundedModuleDrawer(),
                               color_mask=SolidFillColorMask(color_to_tuple(font_transparent_color),
                                                             color_to_tuple(font_color)))

    target_img = Image.open(target_path)
    target_img.paste(qrcode_img, (1215, 618), qrcode_img)
    target_img.save(target_path)


@command(tokens=["color", "颜色", "色", "来个颜色", "来个色卡", "色卡"])
def reply_color_rand(message: RobotMessage):
    cached_prefix = get_cached_prefix('Color-Rand')
    img_path = f"{cached_prefix}.png"

    load_colors()
    picked_color = random.choice(_colors)

    color_card = render_color_card(picked_color)
    color_card.write_file(img_path)
    add_qrcode(img_path, picked_color)

    name = picked_color["name"]
    pinyin = picked_color["pinyin"]
    hex_text, rgb_text, hsv_text = transform_color(picked_color)

    message.reply(f"[Color] {name} {pinyin}\nHEX: {hex_text}\nRGB: {rgb_text}\nHSV: {hsv_text}",
                        img_path=png2jpg(img_path), modal_words=False)
