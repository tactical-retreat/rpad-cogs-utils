import time
from typing import List

from . import db_util
from ..api import wave_data
from ..common import monster_id_mapping
from ..data.skill import MonsterSkill
from .merged_data import MergedCard
from .monster import SqlItem


class WaveItem(SqlItem):
    def __init__(self, pull_id: int, entry_id: int, server: str, dungeon_id: int, dungeon_floor_id: int, floor: int, slot: int, monster: wave_data.WaveMonster):
        self.server = server
        self.dungeon_id = dungeon_id
        self.dungeon_floor_id = dungeon_floor_id
        self.floor = floor
        self.slot = slot

        self.unknown_0 = monster.unknown_0
        self.monster_id = monster.monster_id
        self.monster_level = monster.monster_level
        self.drop_monster_id = monster.drop_monster_id
        self.plus_amount = monster.plus_amount

        self.pull_id = pull_id
        self.entry_id = entry_id

    def _table(self):
        return 'wave_data'

    def _insert_columns(self):
        return self.__dict__.keys()
