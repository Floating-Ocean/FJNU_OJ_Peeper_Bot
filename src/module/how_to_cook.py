import os
import random

from src.core.bot.command import command
from src.core.constants import Constants
from src.core.util.output_cached import get_cached_prefix
from src.core.util.tools import png2jpg
from src.module.message import RobotMessage
from src.render.html.render_how_to_cook import render_how_to_cook

_lib_path = os.path.join(Constants.config["lib_path"], "How-To-Cook")
_dishes_path = os.path.join(_lib_path, "lib", "dishes")

_dishes: dict[str, str] = {}


def register_module():
    pass


def _load_dishes():
    _dishes.clear()
    for root, dirs, files in os.walk(_dishes_path):
        for file in files:
            if file.endswith(".md"):
                full_path = os.path.join(root, file)
                dish_name = file.rstrip('.md')
                _dishes[dish_name] = full_path


@command(tokens=['来道菜', '做菜', '菜', '饿了', '我饿了'])
def reply_how_to_cook(message: RobotMessage):
    message.reply("正在翻菜谱，请稍等")

    _load_dishes()
    chosen_dish_name = random.choice(list(_dishes.keys()))
    cached_prefix = get_cached_prefix('How-To-Cook')
    render_how_to_cook(_dishes[chosen_dish_name], f"{cached_prefix}.png")

    message.reply(f"可以学着做一下【{chosen_dish_name}】哦", png2jpg(f"{cached_prefix}.png"))
