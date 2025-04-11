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
        return os.path.join(_lib_path, f"{img_name}.png")
