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


class DamageReduction(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class PoisonEnemies(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class FreeOrbMovement(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class Gravity(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HpRecoverFromRcv(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HpRecoverStatic(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class OneAttrtoOneAttr(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class OrbRefresh(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class Delay(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class DefenseBreak(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TwoAttrtoOneTwoAttr(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class DamageVoid(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AtkBasedNuke(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class SingleTargetTeamAttrNuke(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrOnAttrNuke(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrBurst(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class MassAttack(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class OrbEnhance(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TrueDamageNuke(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TrueDamageNuke(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrMassAttack(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrNuke(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class Counterattack(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class BoardChange(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HpConditionalNuke(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TrueDamageHpConditionalNuke(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class NukeWithHpPenalty(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class CriticalAttackWithHpPenalty(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TypeBurst(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrBurst(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class BicolorOrbEnhance(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TypeBurst(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class LeaderSwap(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class LowHpConditionalAttrDamageBoost(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class MiniNukeandHpRecovery(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TwoPartActiveSkill(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HpRecoveryandBindClear(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class RandomSKill(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class IncreasedSkyfallChance(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class ColumnOrbChange(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class RowOrbChange(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class IncreasedOrbMovementTime(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class OrbEnhance(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class RandomLocationOrbSpawn(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttributeChange(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrNuke(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrNukeofAttrTwoAtk(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HpRecovery(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class Haste(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class OrbLock(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class EnemyAttrChange(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class ThreeAttrtoOneAttr(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AwokenSkillBurst(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AddAdditionalCombos(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class Gravity(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class OrbLockRemoval(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class VoidDamageAbsorption(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HpRecovery(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class IncreasedEnhanceOrbSkyfall(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class NoSkyfallForXTurns(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class ShowComboPath(ActiveSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)

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
    if s.skill_type == 3:
        return DamageReduction(s)
    if s.skill_type == 4:
        return PoisonEnemies(s)
    if s.skill_type == 5:
        return FreeOrbMovement(s)
    if s.skill_type == 6:
        return Gravity(s)
    if s.skill_type == 7:
        return HpRecoverFromRcv(s)
    if s.skill_type == 8:
        return HpRecoverStatic(s)
    if s.skill_type == 9:
        return OneAttrtoOneAttr(s)
    if s.skill_type == 10:
        return OrbRefresh(s)
    if s.skill_type == 18:
        return Delay(s)
    if s.skill_type == 19:
        return DefenseBreak(s)
    if s.skill_type == 20:
        return TwoAttrtoOneTwoAttr(s)
    if s.skill_type == 21:
        return DamageVoid(s)
    if s.skill_type == 35:
        return AtkBasedNuke(s)
    if s.skill_type == 37:
        return SingleTargetTeamAttrNuke(s)
    if s.skill_type == 42:
        return AttrOnAttrNuke(s)
    if s.skill_type == 50:
        return AttrBurst(s)
    if s.skill_type == 51:
        return MassAttack(s)
    if s.skill_type == 52:
        return OrbEnhance(s)
    if s.skill_type == 55:
        return TrueDamageNuke(s)
    if s.skill_type == 56:
        return TrueDamageNuke(s)
    if s.skill_type == 58:
        return AttrMassAttack(s)
    if s.skill_type == 59:
        return AttrNuke(s)
    if s.skill_type == 60:
        return Counterattack(s)
    if s.skill_type == 71:
        return BoardChange(s)
    if s.skill_type == 84:
        return HpConditionalNuke(s)
    if s.skill_type == 85:
        return TrueDamageHpConditionalNuke(s)
    if s.skill_type == 86:
        return NukeWithHpPenalty(s)
    if s.skill_type == 87:
        return CriticalAttackWithHpPenalty(s)
    if s.skill_type == 88:
        return TypeBurst(s)
    if s.skill_type == 90:
        return AttrBurst(s)
    if s.skill_type == 91:
        return BicolorOrbEnhance(s)
    if s.skill_type == 92:
        return TypeBurst(s)
    if s.skill_type == 93:
        return LeaderSwap(s)
    if s.skill_type == 110:
        return LowHpConditionalAttrDamageBoost(s)
    if s.skill_type == 115:
        return MiniNukeandHpRecovery(s)
    if s.skill_type == 116:
        return TwoPartActiveSkill(s)
    if s.skill_type == 117:
        return HpRecoveryandBindClear(s)
    if s.skill_type == 118:
        return RandomSKill(s)
    if s.skill_type == 126:
        return IncreasedSkyfallChance(s)
    if s.skill_type == 127:
        return ColumnOrbChange(s)
    if s.skill_type == 128:
        return RowOrbChange(s)
    if s.skill_type == 132:
        return IncreasedOrbMovementTime(s)
    if s.skill_type == 140:
        return OrbEnhance(s)
    if s.skill_type == 141:
        return RandomLocationOrbSpawn(s)
    if s.skill_type == 142:
        return AttributeChange(s)
    if s.skill_type == 143:
        return AttrNuke(s)
    if s.skill_type == 144:
        return AttrNukeofAttrTwoAtk(s)
    if s.skill_type == 145:
        return HpRecovery(s)
    if s.skill_type == 146:
        return Haste(s)
    if s.skill_type == 152:
        return OrbLock(s)
    if s.skill_type == 153:
        return EnemyAttrChange(s)
    if s.skill_type == 154:
        return ThreeAttrtoOneAttr(s)
    if s.skill_type == 156:
        return AwokenSkillBurst(s)
    if s.skill_type == 160:
        return AddAdditionalCombos(s)
    if s.skill_type == 161:
        return Gravity(s)
    if s.skill_type == 172:
        return OrbLockRemoval(s)
    if s.skill_type == 173:
        return VoidDamageAbsorption(s)
    if s.skill_type == 179:
        return HpRecovery(s)
    if s.skill_type == 180:
        return IncreasedEnhanceOrbSkyfall(s)
    if s.skill_type == 184:
        return NoSkyfallForXTurns(s)
    if s.skill_type == 189:
        return ShowComboPath(s)
    return None
