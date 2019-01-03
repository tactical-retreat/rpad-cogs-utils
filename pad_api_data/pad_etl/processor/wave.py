import time
from typing import List

from . import db_util
from ..api import wave_data
from ..common import monster_id_mapping
from ..data.skill import MonsterSkill
from .merged_data import MergedCard
from .monster import SqlItem


class WaveItem(SqlItem):
    DROP_MONSTER_ID_GOLD = 9900
    def __init__(self, pull_id: int, entry_id: int, server: str, dungeon_id: int, floor_id: int, stage: int, slot: int, monster: wave_data.WaveMonster):
        self.server = server
        self.dungeon_id = dungeon_id
        self.floor_id = floor_id # ID starts at 1 for lowest
        self.stage = stage # 0-indexed
        self.slot = slot # 0-indexed

        self.spawn_type = monster.spawn_type
        self.monster_id = monster.monster_id
        self.monster_level = monster.monster_level

        # If drop_monster_id == 9900, then drop_monster_level is the bonus gold amount
        self.drop_monster_id = monster.drop_monster_id
        self.drop_monster_level = monster.drop_monster_level
        self.plus_amount = monster.plus_amount

        self.pull_id = pull_id
        self.entry_id = entry_id

    def is_invade():
        return self.spawn_type == 2

    def get_drop(self):
        return self.drop_monster_id if self.drop_monster_id > 0 and self.get_coins() == 0  else None

    def get_coins(self):
        return self.drop_monster_level if self.drop_monster_id == WaveItem.DROP_MONSTER_ID_GOLD else 0

    def _table(self):
        return 'wave_data'

    def _insert_columns(self):
        return self.__dict__.keys()
