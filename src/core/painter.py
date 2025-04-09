import os

from src.core.constants import Constants

_lib_path = os.path.join(Constants.config["lib_path"], "Painter")


def get_img_path(img_name: str) -> str:
    return os.path.join(_lib_path, "img", f"{img_name}.png")
