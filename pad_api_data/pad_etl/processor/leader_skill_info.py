from typing import List

from ..data.skill import MonsterSkill
from .skill_info_constants import ALL_ATTR, ATTRIBUTES, TYPES

class LeaderSkill(object):
    def __init__(self, monster_skill: MonsterSkill):
        self.name = monster_skill.name
        self.raw_description = monster_skill.description
        self.skill_type = monster_skill.skill_type


class AttrAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)
        self.for_attr = [monster_skill.other_fields[0]]
        self.atk_multiplier = monster_skill.other_fields[0] / 100


class BonusAttack(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)
        self.multiplier = monster_skill.other_fields[0] / 100


class Autoheal(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)
        self.multiplier = monster_skill.other_fields[0] / 100


class Resolve(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)
        self.threshold = monster_skill.other_fields[0] / 100


class MovementTimeIncrease(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)
        self.time = monster_skill.other_fields[0] / 100

class DamageReduction(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)
        self.reduction_attributions = ALL_ATTR
        self.damage_reduction = monster_skill.other_fields[0] / 100

def convert(skill_list: List[MonsterSkill]):
    results = []
    for s in skill_list:
        ns = convert_skill(s)
        if ns:
            results.append(ns)
    return results

def convert_skill(s):
    if s.skill_type == 11:
        return AttrAtkBoost(s)
    if s.skill_type == 12:
        return BonusAttack(s)
    if s.skill_type == 13:
        return Autoheal(s)
    if s.skill_type == 14:
        return Resolve(s)
    if s.skill_type == 15:
        return MovementTimeIncrease(s)
    if s.skill_type == 16:
        return DamageReduction(s)
    return None
