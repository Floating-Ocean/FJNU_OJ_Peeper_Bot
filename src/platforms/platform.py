from typing import TypedDict


class ContestDict(TypedDict):
    start_time: int
    duration: int
    platform: str
    name: str
    supplement: str


class Platform:
    @staticmethod
    def get_contest_list() -> list[ContestDict] | None:
        pass
