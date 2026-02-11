"""GW spectrum engine choices"""

import enum


class Engine(enum.IntEnum):
    BPL = DEFAULT = 0
    DBPL = 1
    SSM = 2

    @staticmethod
    def from_str(value: str) -> "Engine":
        return Engine(int(value))


ENGINE_NAMES: dict[Engine, str] = {
    Engine.BPL: "Broken power law (default)",
    Engine.DBPL: "Double broken power law",
    Engine.SSM: "Sound Shell Model",
}
ENGINE_SHORT_NAMES: list[str] = [key.name for key in Engine]
ENGINE_CHOICES: list[tuple[Engine, str]] = list(ENGINE_NAMES.items())
