"""
Parses monster skill (leader/active) data.
"""

import json
import os
from typing import List, Any

from ..common import pad_util
from ..common.shared_types import SkillId

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
        self.clean_description = pad_util.strip_colors(
            self.description).replace('\n', ' ').replace('^p', '')

        # Encodes the type of skill (requires parsing other_fields).
        self.skill_type = int(raw[2])

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

        # Fields used in coordination with skill_type.
        self.data = self.other_fields

        # NEW FIELDS. The skills that a skill links to if it has multiple
        # clauses/conditions for activation
        self.skill_part_1_id = None
        self.skill_part_2_id = None
        self.skill_part_3_id = None

        if self.skill_type == 116 or self.skill_type == 138:
            self.skill_part_1_id = self.other_fields[0]
            self.skill_part_2_id = self.other_fields[1]
            if len(self.other_fields) == 3:
                self.skill_part_3_id = self.other_fields[2]

        try:
            multipliers = pad_util.parse_skill_multiplier(
                int(raw[2]), self.other_fields, len(self.other_fields))
        except Exception as e:
            print('skill parsing failed for', raw[2], 'with exception:', e)
            multipliers = pad_util.Multiplier()

        self.hp_mult = multipliers.hp
        self.atk_mult = multipliers.atk
        self.rcv_mult = multipliers.rcv

        # This gives you the shield as a percent rather than a fraction
        self.shield = multipliers.shield * 100

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return 'Skill(%s, %r)' % (self.skill_id, self.name)


def load_skill_data(data_dir=None, skill_json_file: str = None) -> List[MonsterSkill]:
    """Load MonsterSkill objects from the PAD json file."""
    if skill_json_file is None:
        skill_json_file = os.path.join(data_dir, FILE_NAME)

    with open(skill_json_file) as f:
        skill_json = json.load(f)

    if skill_json['v'] > 1220:
        print('Warning! Version of skill file is not tested: {}'.format(skill_json['v']))

    return [MonsterSkill(i, ms) for i, ms in enumerate(skill_json['skill'])]


def load_raw_skill_data(data_dir=None, skill_json_file: str = None) -> object:
    """Load raw PAD json file."""
    # Temporary hack
    if skill_json_file is None:
        skill_json_file = os.path.join(data_dir, FILE_NAME)

    with open(skill_json_file) as f:
        skill_json = json.load(f)

    return skill_json
