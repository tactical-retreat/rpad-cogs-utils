"""
Parses monster skill (leader/active) data.
"""

import json
import os
from typing import List, Any

from ..common import pad_util
from ..common.shared_types import SkillId
from ..common.skill_type_maps import SKILL_TYPE, BOOSTED_ATTRS, BOOSTED_TYPES

# The typical JSON file name for this data.
FILE_NAME = 'download_skill_data.json'


class MonsterSkill(pad_util.JsonDictEncodable):
    """Leader/active skill info for a player-ownable monster."""

    def __init__(self, skill_id: int, raw: List[Any]):
        self.skill_id = SkillId(skill_id)

        # Skill name text.
        self.name = str(raw[0])

        # Skill description text (may include formatting).
        self.description = str(raw[1])

        # Skill description text (no formatting).
        self.clean_description = pad_util.strip_colors(self.description).replace('\n', ' ').replace('^p', '')

        # Encodes the type of skill (requires parsing other_fields).
        self.skill_type = int(raw[2])

        # New field. Describes the idea that a skill falls into
        self.skill_class = SKILL_TYPE(self.skill_type)


        # If an active skill, number of levels to max.
        levels = int(raw[3])
        self.levels = levels if levels else None

        # If an active skill, maximum cooldown.
        self.turn_max = int(raw[4]) if self.levels else None

        # If an active skill, minimum cooldown.
        self.turn_min = self.turn_max - (self.levels - 1) if levels else None

        # Unknown field.
        self.unknown_005 = raw[5]

        # Fields used in coordination with skill_type.
        self.other_fields = raw[6:]

        # NEW FIELDS. The skills that a skill links two if it has multiple clauses
        self.skill_part_1_id = None
        self.skill_part_2_id = None
        self.skill_part_3_id = None

        if self.skill_type == 116 or self.skill_type == 138:
            self.skill_part_1_id = self.other_fields[0]
            self.skill_part_2_id = self.other_fields[1]
            if len(self.other_fields) == 3:
                self.skill_part_3_id = self.other_fields[2]

        multipliers = parse_leader_skill_multiplier(int(raw[2]), self.other_fields)
        self.hp_mult = multipliers['hp']
        self.atk_mult = multipliers['atk']
        self.rcv_mult = multipliers['rcv']
        self.damage_reduction = multipliers['shield']

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return 'Skill(%s, %r)' % (self.skill_id, self.name)


def parse_leader_skill_multiplier(skill, other_fields) -> {}:
    # HP, ATK, RCV, Damage Reduction
    multipliers = {'hp': 1.0, 'atk': 1.0, 'rcv': 1.0, 'shield': 0.0}

    # Attack boost only
    if skill in [11, 22, 26, 31, 40, 50, 66, 69, 88, 90, 94, 95, 96, 97, 100, 104, 122, 130, 131,  177]:
        multipliers['atk'] = get_last(other_fields)

    # HP boost only
    elif skill in [23, 48]:
        multipliers['hp'] = other_fields[1]/100

    elif skill in [24, 49]:
        multipliers['rcv'] = other_fields[1]/100

    # RCV and ATK
    elif skill in [28, 64, 75, 79]:
        multipliers['atk'] = get_last(other_fields)
        multipliers['rcv'] = get_last(other_fields)

    # All stat boost
    elif skill in [29, 65, 76, 114]:
        multipliers['hp'] = get_last(other_fields)
        multipliers['atk'] = get_last(other_fields)
        multipliers['rcv'] = get_last(other_fields)

    elif skill == 30:
        multipliers['hp'] = other_fields[2] / 100

    elif skill in [36, 38, 43]:
        multipliers['shield'] = other_fields[2] / 100

    elif skill in [39, 44]:
        multipliers['atk'] = other_fields[3] / 100
        if other_fields[2] == 2:
            multipliers['rcv'] = other_fields[3] / 100

    elif skill in [45, 62, 73, 77, 111]:
        multipliers['hp'] = get_last(other_fields)
        multipliers['atk'] = get_last(other_fields)

    elif skill == 46:
        multipliers['hp'] = other_fields[2] / 100

    # rainbow parsing
    elif skill == 61:
        if len(other_fields) == 3:
            multipliers['atk'] = other_fields[2]/100
        elif len(other_fields) == 4:
            r_type = other_fields[0]
            if r_type == 31:
                mult = other_fields[2]/100 + (other_fields[3]/100) * (5-other_fields[1])
                multipliers['atk'] = mult
            elif r_type % 14 == 0:
                multipliers['atk'] = other_fields[2]/100 + other_fields[3]/100
            else:
                # r_type is 63
                mult = other_fields[2] / 100 + (other_fields[3] / 100) * (6 - other_fields[1])
                multipliers['atk'] = mult
        elif len(other_fields) == 5:
            multipliers['atk'] = other_fields[2] + (other_fields[4]-other_fields[1]) * other_fields[3]

    elif skill in [63, 67]:
        multipliers['hp'] = other_fields[1]/100
        multipliers['rcv'] = other_fields[1]/100

    elif skill == 98:
        multipliers['atk'] = other_fields[1] + (other_fields[3] - other_fields[0]) * other_fields[2]

    elif skill == 105:
        multipliers['atk'] = other_fields[1]/100
        multipliers['rcv'] = other_fields[0]/100

    elif skill == 108:
        multipliers['atk'] = get_last(other_fields)
        multipliers['hp'] = other_fields[0]/100

    elif skill == 119:
        if len(other_fields) == 3:
            multipliers['atk'] = get_last(other_fields)
        elif len(other_fields) == 5:
            multipliers['atk'] = other_fields[2]/100 + (other_fields[4] - other_fields[1]) * (other_fields[3]/100)

    elif skill == 121:
        if len(other_fields) == 4:
            multipliers['atk'] = get_last(other_fields)
            if other_fields[2] != 0:
                multipliers['hp'] = other_fields[2]/100
        elif len(other_fields) == 5:
            if other_fields[2] != 0:
                multipliers['hp'] = other_fields[2]/100
            if other_fields[3] != 0:
                multipliers['atk'] = other_fields[3]/100
            if other_fields[4] != 0:
                multipliers['rcv'] = other_fields[4]/100

    elif skill == 123:
        if len(other_fields) == 4:
            multipliers['atk'] = get_last(other_fields)
        elif len(other_fields) == 5:
            multipliers['atk'] = other_fields[3]/100
            multipliers['rcv'] = other_fields[4]/100

    elif skill == 124:
        if len(other_fields) == 7:
            multipliers['atk'] = get_last(other_fields)
        elif len(other_fields) == 8:
            max_combos = 0
            for i in range(0,5):
                if other_fields[i] != 0:
                    max_combos += 1

            scale = get_last(other_fields)
            c_count = other_fields[5]
            multipliers['atk'] = other_fields[6] + scale*(max_combos - c_count)

    elif skill == 125:
        if len(other_fields) == 7:
            multipliers['atk'] = get_last(other_fields)
            multipliers['hp'] = get_second_last(other_fields)
        elif len(other_fields) == 8:
            if other_fields-[-2] != 0:
                multipliers['atk'] = get_second_last(other_fields)
            if other_fields[-1] != 0:
                multipliers['rcv'] = get_last(other_fields)
            if other_fields[-3] != 0:
                multipliers['hp'] = get_third_last(other_fields)

    elif skill == 129:
        if len(other_fields) == 4:
            multipliers['hp'] = get_second_last(other_fields)
            multipliers['atk'] = get_last(other_fields)
        elif len(other_fields) == 5:
            multipliers['hp'] = get_third_last(other_fields)
            multipliers['atk'] = get_second_last(other_fields)
            multipliers['rcv'] = get_last(other_fields)

    elif skill == 133:
        if len(other_fields) == 3:
            multipliers['atk'] = get_last(other_fields)
        elif len(other_fields) == 4:
            multipliers['atk'] = get_second_last(other_fields)
            multipliers['rcv'] = get_last(other_fields)

    elif skill == 136:
        if len(other_fields) == 6:
            multipliers['atk'] = get_mult(other_fields[2])
            multipliers['hp'] = get_last(other_fields)
        elif len(other_fields) == 7:
            multipliers['atk'] = get_mult(other_fields[2])*get_last(other_fields)
        elif len(other_fields) == 8:
            multipliers['atk'] = get_mult(other_fields[2])
            if get_second_last(other_fields) != 0:
                multipliers['atk'] *= get_second_last(other_fields)
            if get_third_last(other_fields) != 0:
                multipliers['hp'] = get_third_last(other_fields)
            if get_last(other_fields) != 0:
                multipliers['rcv'] = get_last(other_fields)

    elif skill == 137:

    return multipliers


def get_mult(val):
    return val/100


def get_last(other_fields):
    return other_fields[-1]/100


def get_second_last(other_fields):
    return other_fields[-2]/100


def get_third_last(other_fields):
    return other_fields[-3]/100


def load_skill_data(data_dir=None, skill_json_file: str = None) -> List[MonsterSkill]:
    """Load MonsterSkill objects from the PAD json file."""
    if skill_json_file is None:
        skill_json_file = os.path.join(data_dir, FILE_NAME)

    with open(skill_json_file) as f:
        skill_json = json.load(f)

    if skill_json['v'] != 1220:
        raise NotImplementedError('version: {}'.format(skill_json['v']))

    return [MonsterSkill(i, ms) for i, ms in enumerate(skill_json['skill'])]


def load_raw_skill_data(data_dir=None, skill_json_file: str = None) -> object:
    """Load raw PAD json file."""
    # Temporary hack
    if skill_json_file is None:
        skill_json_file = os.path.join(data_dir, FILE_NAME)

    with open(skill_json_file) as f:
        skill_json = json.load(f)

    return skill_json
