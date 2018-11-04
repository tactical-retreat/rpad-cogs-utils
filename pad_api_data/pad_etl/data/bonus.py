"""
Parses limited time event data.

Data files can be different depending on the account; all 5 groups (and
potentially all 3 starters) need to be parsed and then deduped against
each other to get the full list.
"""

import json
import os
from typing import Dict, List, Any

from ..common import pad_util
from ..common.pad_util import ghmult, ghchance
from ..common.shared_types import DungeonId, DungeonFloorId


# The typical JSON file name for this data.
FILE_NAME = 'download_limited_bonus_data_{}.json'


class Bonus(pad_util.JsonDictEncodable):
    """Basically any type of modifier text shown in a menu."""

    types = {
        # EXP multiplier.
        1: {'name': 'Exp x{}!', 'mod_fn': ghmult},

        # Coin multiplier.
        2: {'name': 'Coin x{}!', 'mod_fn': ghmult},

        # Drop rate increased.
        3: {'name': 'Drop% x{}!', 'mod_fn': ghmult},

        # Stamina reduced.
        5: {'name': 'Stamina {}!', 'mod_fn': ghmult},

        # Special/co-op dungeon list.
        6: {'name': 'dungeon'},

        # PEM text.
        8: {'name': 'PEM Event', },

        # REM text.
        9: {'name': 'REM Event', },

        # Current PEM pal point cost.
        10: {'name': 'PEM cost: {}', 'mod_fn': int},

        # Feed XP modifier.
        11: {'name': 'great*', 'mod_fn': ghmult},

        # Increased plus rate 1?
        12: {'name': '+egg%', 'mod_fn': ghchance},

        # ?
        14: {'name': 'gf_?', },

        # Increased plus rate 2?
        16: {'name': '+egg*', 'mod_fn': ghmult},

        # Increased skillup chance
        17: {'name': 'skill*', 'mod_fn': ghmult},

        # "tourney is over, results pending"?
        20: {'name': 'tournament_active', },

        # "tourney is over, results pending"?
        21: {'name': 'tournament_closed', },

        # ?
        22: {'name': 'score_announcement', },

        # metadata?
        23: {'name': 'meta?', },

        # Bosses drop as +99 Eggs
        # None (but associated with dungeon)
        25: {'name': 'dungeon_special_event'},

        # Limited Time Dungeon arrives! (on multiplayer mode button)
        29: {'name': 'multiplayer_announcement'},

        36: {'name': 'daily_dragons'},

        37: {'name': 'monthly_quest_dungeon'}
    }

    keys = 'sebiadmf'

    def __init__(self, raw: Dict[str, Any]):
        if not set(raw) <= set(Bonus.keys):
            raise ValueError('Unexpected keys: ' + str(set(raw) - set(Bonus.keys)))

        # Start time as gungho time string
        self.start_time_str = str(raw['s'])

        # End time as gungho time string
        self.end_time_str = str(raw['e'])

        # Optional DungeonId
        self.dungeon_id = None  # type: DungeonId
        if 'd' in raw:
            self.dungeon_id = DungeonId(raw['d'])

        # Optional DungeonFloorId
        # Stuff like rewards text in monthly quests
        self.dungeon_floor_id = None  # type: DungeonFloorId
        if 'f' in raw:
            self.dungeon_floor_id = DungeonFloorId(raw['f'])

        # If REM/PEM, the ID of the machine
        self.egg_machine_id = None  # type: int
        if 'i' in raw:
            self.egg_machine_id = int(raw['i'])

        # Optional human-readable message (with formatting)
        self.message = None  # type: str
        # Optional human-readable message (no formatting)
        self.clean_message = None  # type: str
        if 'm' in raw:
            self.message = str(raw['m'])
            self.clean_message = pad_util.strip_colors(self.message)

        bonus_id = int(raw['b'])
        bonus_info = Bonus.types.get(bonus_id, {'name': 'unknown_id:{}'.format(bonus_id)})

        # Bonus value, if provided and a processor is set
        self.bonus_value = None  # type: number
        if 'mod_inf' in bonus_info and 'a' in raw:
            self.bonus_value = bonus_info['mod_fn'](raw['a'])

        # Human readable name for the bonus
        self.bonus_name = bonus_info['name'].format(self.bonus_value)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return 'Bonus({} - {}/{})'.format(self.bonus_name, self.dungeon_id, self.dungeon_floor_id)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


def load_bonus_data(data_dir: str=None, data_group: str=None,
                    bonus_json_file: str=None) -> List[Bonus]:
    """Load Bonus objects from the PAD json file."""
    if bonus_json_file is None:
        bonus_json_file = os.path.join(data_dir, FILE_NAME.format(data_group))

    with open(bonus_json_file) as f:
        bonus_json = json.load(f)

    if bonus_json['v'] > 2:
        print('Warning! Version of bonus file is not tested: {}'.format(bonus_json['v']))

    return [Bonus(item) for item in bonus_json['bonuses']]
