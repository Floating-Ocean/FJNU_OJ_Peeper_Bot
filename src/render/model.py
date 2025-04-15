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
    def get_img_path(cls, img_name: str) -> str:
        img_path = os.path.join(_lib_path, f"{img_name}.png")
        if os.path.exists(img_path):
            return img_path
        else:
            return os.path.join(_lib_path, "Unknown.png")


class RenderableSection(abc.ABC):
    """图片渲染分块基类"""

    def get_columns(self):
        """占几列，重写本方法以实现多列"""
        return 1

    @abstractmethod
    def render(self, img: pixie.Image, x: int, y: int) -> int:
        pass

    @abstractmethod
    def get_height(self):
        pass
