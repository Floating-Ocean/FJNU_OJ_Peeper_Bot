import os

import pixie

from src.core.constants import Constants

_lib_path = os.path.join(Constants.config["lib_path"], "Painter")


def apply_tint(img_name: str, tint: pixie.Color) -> pixie.Image:
    image = pixie.read_image(os.path.join(_lib_path, "img", f"{img_name}.png"))
    width, height = image.width, image.height
    tinted_image = pixie.Image(width, height)
    alpha = 1
    for x in range(width):
        for y in range(height):
            orig_pixel = image.get_color(x, y)
            mixed_r = orig_pixel.r * (1 - alpha) + tint.r * alpha
            mixed_g = orig_pixel.g * (1 - alpha) + tint.g * alpha
            mixed_b = orig_pixel.b * (1 - alpha) + tint.b * alpha
            tinted_image.set_color(x, y, pixie.Color(mixed_r, mixed_g, mixed_b, orig_pixel.a))
    return tinted_image


def choose_text_color(color: dict) -> tuple[int, int, int]:
    luminance = 0.299 * color["RGB"][0] + 0.587 * color["RGB"][1] + 0.114 * color["RGB"][2]
    return (18, 18, 18) if luminance > 128 else (252, 252, 252)


def darken_color(color: pixie.Color, ratio: float = 0.7) -> pixie.Color:
    return pixie.Color(color.r * ratio, color.g * ratio, color.b * ratio, color.a)


def draw_img(img: pixie.Image, img_name: str, x: int, y: int, img_size: tuple[int, int], color: pixie.Color):
    tinted_img = apply_tint(img_name, color).resize(img_size[0], img_size[1])
    img.draw(tinted_img, pixie.translate(x, y))


def draw_text(img: pixie.Image, content: str, x: int, y: int, font_weight: str, font_size: int,
              color: pixie.Color) -> int:
    font = pixie.read_font(os.path.join(_lib_path, "font", f"OPPOSans-{font_weight}.ttf"))
    font.size = font_size
    font.paint.color = color
    img.fill_text(font, content, pixie.translate(x, y))
    return font.layout_bounds(content).x


def draw_round_rect(image: pixie.Image, paint: pixie.Paint, x: int, y: int, width: int, height: int, round_size: float):
    ctx = image.new_context()
    ctx.fill_style = paint
    ctx.rounded_rect(x, y, width, height, round_size, round_size, round_size, round_size)
    ctx.fill()


def get_gradient_paint(width: int, height: int, colors: list[str], positions: list[float]) -> pixie.Paint:
    paint = pixie.Paint(pixie.LINEAR_GRADIENT_PAINT if len(colors) == 2 else pixie.RADIAL_GRADIENT_PAINT)
    for i in range(len(colors)):
        color = pixie.parse_color(colors[i])
        paint.gradient_handle_positions.append(pixie.Vector2(32 + (width - 64) * positions[i],
                                                             32 + (height - 64) * positions[i]))
        paint.gradient_stops.append(pixie.ColorStop(color, i))
    return paint
