"""GW spectrum engine choices"""

import enum


class Engine(enum.IntEnum):
    DEFAULT = 0
    SSM = 1
    DBPL = 2

    @staticmethod
    def from_str(value: str) -> "Engine":
        return Engine(int(value))


ENGINE_NAMES: dict[Engine, str] = {
    Engine.DEFAULT: "Default",
    Engine.SSM: "Sound Shell Model",
    Engine.DBPL: "Double broken power law",
}
ENGINE_SHORT_NAMES: list[str] = [key.name for key in Engine]
ENGINE_CHOICES: list[tuple[Engine, str]] = list(ENGINE_NAMES.items())
