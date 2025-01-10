import abc
from dataclasses import dataclass


@dataclass
class Contest:
    start_time: int
    duration: int
    platform: str
    name: str
    supplement: str


class Platform(abc.ABC):
    @staticmethod
    def get_contest_list() -> list[Contest] | None:
        pass
