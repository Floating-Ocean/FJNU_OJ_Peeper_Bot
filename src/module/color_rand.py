import json
import os
import random
from colorsys import rgb_to_hsv

import pixie
import qrcode
from PIL import Image
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.main import QRCode

from src.core.command import command
from src.core.constants import Constants
from src.core.output_cached import get_cached_prefix
from src.core.painter import draw_round_rect, draw_text, choose_text_color
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
    hex_text, rgb_text, hsv_text = transform_color(color)

    img = pixie.Image(1664, 1040)
    img.fill(pixie.Color(0, 0, 0, 1))

    paint_bg = pixie.Paint(pixie.SOLID_PAINT)
    paint_bg.color = pixie.Color(color["RGB"][0] / 255, color["RGB"][1] / 255, color["RGB"][2] / 255, 1)
    draw_round_rect(img, paint_bg, 32, 32, 1600, 976, 96)

    text_color_dict = choose_text_color(color)
    text_color = pixie.Color(text_color_dict[0] / 255, text_color_dict[1] / 255, text_color_dict[2] / 255, 1)

    draw_text(img, f"Color Collect - {color['pinyin']}", 144 + 32, 120 + 32, 'H', 48, text_color)
    draw_text(img, color['name'], 144 + 32, 232 + 32, 'H', 144, text_color)
    hex_width = draw_text(img, hex_text, 144 + 32, 472 + 32, 'M', 72, text_color)
    rgb_width = draw_text(img, rgb_text, 144 + 32, 616 + 32, 'M', 72, text_color)
    hsv_width = draw_text(img, hsv_text, 144 + 32, 760 + 32, 'M', 72, text_color)
    draw_text(img, "HEX", 144 + hex_width + 32 + 32, 472 + 32 + 24, 'R', 48, text_color)
    draw_text(img, "RGB", 144 + rgb_width + 32 + 32, 616 + 32 + 24, 'R', 48, text_color)
    draw_text(img, "HSV", 144 + hsv_width + 32 + 32, 760 + 32 + 24, 'R', 48, text_color)

    return img


def add_qrcode(target_path: str, color: dict):
    qr = QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8)

    hex_clean = color["hex"][1:].lower()
    qr.add_data(f"https://gradients.app/zh/color/{hex_clean}")

    font_color = choose_text_color(color)
    qrcode_img = qr.make_image(image_factory=StyledPilImage,
                               module_drawer=RoundedModuleDrawer(), eye_drawer=RoundedModuleDrawer(),
                               color_mask=SolidFillColorMask((font_color[0], font_color[1], font_color[2], 0),
                                                             (font_color[0], font_color[1], font_color[2], 255)))

    target_img = Image.open(target_path)
    target_img.paste(qrcode_img, (1215, 618), qrcode_img)
    target_img.save(target_path)


@command(tokens=["color", "颜色", "色", "来个颜色", "来个色卡", "色卡"])
async def reply_color_rand(message: RobotMessage):
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

    await message.reply(f"[Color] {name} {pinyin}\nHEX: {hex_text}\nRGB: {rgb_text}\nHSV: {hsv_text}",
                        img_path=png2jpg(img_path), modal_words=False)
