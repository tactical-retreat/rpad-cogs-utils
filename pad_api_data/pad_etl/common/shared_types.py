import math
from typing import NewType

from . import pad_util


AttrId = NewType('AttrId', int)
CardId = NewType('CardId', int)
DungeonId = NewType('DungeonId', int)
DungeonFloorId = NewType('DungeonFloorId', int)
SkillId = NewType('SkillId', int)
TypeId = NewType('TypeId', int)


class Curve(pad_util.JsonDictEncodable):
    def __init__(self, min_val: int, max_val: int, scale: float):
        self.min_val = min_val
        self.max_val = max_val
        self.scale = scale

    def value_at(self, level: int, max_level: int):
        f = 1 if max_level == 1 else (level - 1) / (max_level - 1)
        return int(round(self.min_val + (self.max_val - self.min_val) * math.pow(f, self.scale), 0))


def curve_value(min_val, max_val, scale, level, max_level):
    return Curve(min_val, max_val, scale).value_at(level, max_level)
