from typing import List

from ..data.skill import MonsterSkill
from .skill_info_constants import ALL_ATTR, ATTRIBUTES, TYPES


class ActiveSkill(object):
    def __init__(self, monster_skill: MonsterSkill):
        self.name = monster_skill.name
        self.raw_description = monster_skill.description
        self.skill_type = monster_skill.skill_type
        self.levels = monster_skill.levels
        self.turn_max = monster_skill.turn_max
        self.turn_min = monster_skill.turn_min


class MultiTargetNuke(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)
        self.attribute = monster_skill.other_fields[0]
        self.damage = monster_skill.other_fields[1]


class SingleTargetNuke(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)
        self.multiplier = monster_skill.other_fields[0] / 100

def convert(skill_list: List[MonsterSkill]):
    results = []
    for s in skill_list:
        ns = convert_skill(s)
        if ns:
            results.append(ns)
    return results

def convert_skill(s):
    if s.skill_type == 1:
        return MultiTargetNuke(s)
    if s.skill_type == 2:
        return SingleTargetNuke(s)
    return None
