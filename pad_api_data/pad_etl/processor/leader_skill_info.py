from typing import List

from ..data.skill import MonsterSkill
from .skill_info_constants import ALL_ATTR, ATTRIBUTES, TYPES, COLLAB_MAP

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


class AttrDamageReduction(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)
        self.reduction_attributes = [monster_skill.other_fields[0]]
        self.damage_reduction = monster_skill.other_fields[1] / 100

class TypeAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TypeHpBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TypeRcvBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class StaticAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AtkRcvBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AllStatBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class DragonGodHpBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class DragonGodAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TaikoDrum(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TwoAttrDamageReduction(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class LowHpShield(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class LowHpAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TwoAttrAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class Counterattack(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class FullHpShield(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HighHpAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TwoAttrAtkHpBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TwoAttrHpBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrHpBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrRcvBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class EggDropRateBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class CoinDropBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class Rainbow(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TypeHpAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TypeHpRcvBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TypeAtkRcvBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TypeAllStatBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class ComboFlatMultiplier(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrHpRcvBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrTypeAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrTypeHpAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrTypeAtkRcvBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrTypeAllStatBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class GodDragonHpAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class GodDragonAtkRcvBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class LowHpConditionalAttrAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class LowHpConditionalTypeAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HighHpConditionalAttrAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HighHpConditionalTypeAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class ComboScaledMultiplier(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class SkillActivationAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AtkBoostwithExactCombos(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AtkBoostwithExactCombos(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class ComboFlatMultiplierAttrAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class ReducedRcvAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AtkRcvBoostwithCombosFlat(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HpReduction(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class ReducedHpTypeAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class RowAtkBoostnotscaled(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TwoAttrHpAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TwoAttrAllStatBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class RowMatch(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class StatBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class LowHpConditionalAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HighHpConditionalBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrComboScalingAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TeamUnitConditionalStatBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class LowHpAttrAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HighHpAttrAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class SkillActivationConditionalAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class MultiAttrConditionalStatBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class MultiTypeConditionalStatBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class TwoPartLeaderSkill(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HpMuLtiConditionalAtkBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class XPorCoinDropBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HealMatchRcvBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class EnhanceOrbMatch5(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HeartCross(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class Multiboost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrCross(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class MatchXOrMoreOrbs(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AdvancedRowMatch(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class SevenBySix(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class NoSkyfallBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AttrComboConditionalAtkRcvBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class RainbowAtkRcv(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class AtkRcvComboScale(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class RowAtkRcvBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class ComboMultPlusShield(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class RainbowMultPlusShield(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class MatchAttrPlusShield(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class CollabConditionalBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class CollabConditionalBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class OrbRemainingMultiplier(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class FourSecondsMovementTime(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class RowMatcHPlusDamageReduction(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class HpConditionalBoost(LeaderSkill):
    def __init__(self, monster_skill: MonsterSkill):
        super().__init__(monster_skill)


class SevenBySixStatBoost(LeaderSkill):
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
    if s.skill_type == 17:
        return AttrDamageReduction(s)
    if s.skill_type == 22:
        return TypeAtkBoost(s)
    if s.skill_type == 23:
        return TypeHpBoost(s)
    if s.skill_type == 24:
        return TypeRcvBoost(s)
    if s.skill_type == 26:
        return StaticAtkBoost(s)
    if s.skill_type == 28:
        return AtkRcvBoost(s)
    if s.skill_type == 29:
        return AllStatBoost(s)
    if s.skill_type == 30:
        return DragonGodHpBoost(s)
    if s.skill_type == 31:
        return DragonGodAtkBoost(s)
    if s.skill_type == 33:
        return TaikoDrum(s)
    if s.skill_type == 36:
        return TwoAttrDamageReduction(s)
    if s.skill_type == 38:
        return LowHpShield(s)
    if s.skill_type == 39:
        return LowHpAtkBoost(s)
    if s.skill_type == 40:
        return TwoAttrAtkBoost(s)
    if s.skill_type == 41:
        return Counterattack(s)
    if s.skill_type == 43:
        return FullHpShield(s)
    if s.skill_type == 44:
        return HighHpAtkBoost(s)
    if s.skill_type == 45:
        return TwoAttrAtkHpBoost(s)
    if s.skill_type == 46:
        return TwoAttrHpBoost(s)
    if s.skill_type == 48:
        return AttrHpBoost(s)
    if s.skill_type == 49:
        return AttrRcvBoost(s)
    if s.skill_type == 53:
        return EggDropRateBoost(s)
    if s.skill_type == 54:
        return CoinDropBoost(s)
    if s.skill_type == 61:
        return Rainbow(s)
    if s.skill_type == 62:
        return TypeHpAtkBoost(s)
    if s.skill_type == 63:
        return TypeHpRcvBoost(s)
    if s.skill_type == 64:
        return TypeAtkRcvBoost(s)
    if s.skill_type == 65:
        return TypeAllStatBoost(s)
    if s.skill_type == 66:
        return ComboFlatMultiplier(s)
    if s.skill_type == 67:
        return AttrHpRcvBoost(s)
    if s.skill_type == 69:
        return AttrTypeAtkBoost(s)
    if s.skill_type == 73:
        return AttrTypeHpAtkBoost(s)
    if s.skill_type == 75:
        return AttrTypeAtkRcvBoost(s)
    if s.skill_type == 76:
        return AttrTypeAllStatBoost(s)
    if s.skill_type == 77:
        return GodDragonHpAtkBoost(s)
    if s.skill_type == 79:
        return GodDragonAtkRcvBoost(s)
    if s.skill_type == 94:
        return LowHpConditionalAttrAtkBoost(s)
    if s.skill_type == 95:
        return LowHpConditionalTypeAtkBoost(s)
    if s.skill_type == 96:
        return HighHpConditionalAttrAtkBoost(s)
    if s.skill_type == 97:
        return HighHpConditionalTypeAtkBoost(s)
    if s.skill_type == 98:
        return ComboScaledMultiplier(s)
    if s.skill_type == 100:
        return SkillActivationAtkBoost(s)
    if s.skill_type == 101:
        return AtkBoostwithExactCombos(s)
    if s.skill_type == 104:
        return ComboFlatMultiplierAttrAtkBoost(s)
    if s.skill_type == 105:
        return ReducedRcvAtkBoost(s)
    if s.skill_type == 106:
        return AtkRcvBoostwithCombosFlat(s)
    if s.skill_type == 107:
        return HpReduction(s)
    if s.skill_type == 108:
        return ReducedHpTypeAtkBoost(s)
    if s.skill_type == 109:
        return RowAtkBoostnotscaled(s)
    if s.skill_type == 111:
        return TwoAttrHpAtkBoost(s)
    if s.skill_type == 114:
        return TwoAttrAllStatBoost(s)
    if s.skill_type == 119:
        return RowMatch(s)
    if s.skill_type in [121, 129, 185]:
        return StatBoost(s)
    if s.skill_type == 122:
        return LowHpConditionalAtkBoost(s)
    if s.skill_type == 123:
        return HighHpConditionalBoost(s)
    if s.skill_type == 124:
        return AttrComboScalingAtkBoost(s)
    if s.skill_type == 125:
        return TeamUnitConditionalStatBoost(s)
    if s.skill_type == 130:
        return LowHpAttrAtkBoost(s)
    if s.skill_type == 131:
        return HighHpAttrAtkBoost(s)
    if s.skill_type == 133:
        return SkillActivationConditionalAtkBoost(s)
    if s.skill_type == 136:
        return MultiAttrConditionalStatBoost(s)
    if s.skill_type == 137:
        return MultiTypeConditionalStatBoost(s)
    if s.skill_type == 138:
        return TwoPartLeaderSkill(s)
    if s.skill_type == 139:
        return HpMuLtiConditionalAtkBoost(s)
    if s.skill_type == 148:
        return XPorCoinDropBoost(s)
    if s.skill_type == 149:
        return HealMatchRcvBoost(s)
    if s.skill_type == 150:
        return EnhanceOrbMatch5(s)
    if s.skill_type == 151:
        return HeartCross(s)
    if s.skill_type == 155:
        return Multiboost(s)
    if s.skill_type == 157:
        return AttrCross(s)
    if s.skill_type == 158:
        return MatchXOrMoreOrbs(s)
    if s.skill_type == 159:
        return AdvancedRowMatch(s)
    if s.skill_type == 162:
        return SevenBySix(s)
    if s.skill_type == 163:
        return NoSkyfallBoost(s)
    if s.skill_type == 164:
        return AttrComboConditionalAtkRcvBoost(s)
    if s.skill_type == 165:
        return RainbowAtkRcv(s)
    if s.skill_type == 166:
        return AtkRcvComboScale(s)
    if s.skill_type == 167:
        return RowAtkRcvBoost(s)
    if s.skill_type == 169:
        return ComboMultPlusShield(s)
    if s.skill_type == 170:
        return RainbowMultPlusShield(s)
    if s.skill_type == 171:
        return MatchAttrPlusShield(s)
    if s.skill_type == 175:
        return CollabConditionalBoost(s)
    if s.skill_type == 177:
        return OrbRemainingMultiplier(s)
    if s.skill_type == 178:
        return FourSecondsMovementTime(s)
    if s.skill_type == 182:
        return RowMatcHPlusDamageReduction(s)
    if s.skill_type == 183:
        return HpConditionalBoost(s)
    if s.skill_type == 186:
        return SevenBySixStatBoost(s)
    return None
