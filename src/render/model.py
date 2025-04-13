import abc
import os
from abc import abstractmethod

import pixie

from src.core.constants import Constants

_lib_path = os.path.join(Constants.config["lib_path"], "Render-Images")


class Renderer(abc.ABC):
    """图片渲染基类"""

    @abstractmethod
    def render(self) -> pixie.Image:
        pass

    @classmethod
    def _get_img_path(cls, img_name: str) -> str:
        img_path = os.path.join(_lib_path, f"{img_name}.png")
        if os.path.exists(img_path):
            return img_path
        else:
            return os.path.join(_lib_path, "Unknown.png")
