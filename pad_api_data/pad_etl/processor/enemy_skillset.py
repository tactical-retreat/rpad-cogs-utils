from collections import OrderedDict
import json
from math import ceil, log
from typing import List

from ..data.card import EnemySkillRef, BookCard
from .describe_en import Describe_EN

class DictWithAttributeAccess(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


# TODO: this needs fixing, can't have a global map like this
enemy_skill_map = None


def es_id(skill: EnemySkillRef):
    return skill.enemy_skill_id


def name(skill: EnemySkillRef):
    return enemy_skill_map[skill.enemy_skill_id].name


def params(skill: EnemySkillRef):
    return enemy_skill_map[skill.enemy_skill_id].params


def ai(skill: EnemySkillRef):
    return skill.enemy_ai


def rnd(skill: EnemySkillRef):
    return skill.enemy_rnd


def es_type(skill: EnemySkillRef):
    return enemy_skill_map[skill.enemy_skill_id].type


def attribute_bitmap(bits, inverse=False, bit_len=9):
    if bits is None:
        return None
    if bits == -1:
        return [Describe_EN.RANDOM]
    offset = 0
    atts = []
    while offset < bit_len:
        if inverse:
            if (bits >> offset) & 1 == 0:
                atts.append(Describe_EN.ATTRIBUTE_MAP[offset])
        else:
            if (bits >> offset) & 1 == 1:
                atts.append(Describe_EN.ATTRIBUTE_MAP[offset])
        offset += 1
    return atts


def typing_bitmap(bits):
    if bits is None:
        return None
    if bits == -1:
        return []
    offset = 0
    types = []
    while offset < bits.bit_length():
        if (bits >> offset) & 1 == 1:
            types.append(Describe_EN.TYPING_MAP[offset])
        offset += 1
    return types


def bind_bitmap(bits):
    if bits is None:
        return [Describe_EN.TARGET_MAP[0]]
    targets = []
    if (bits >> 0) & 1 == 1:
        targets.append(Describe_EN.TARGET_MAP[1])
    if (bits >> 1) & 1 == 1:
        if len(targets) > 0:
            targets = [Describe_EN.TARGET_MAP[3]]
        else:
            targets.append(Describe_EN.TARGET_MAP[2])
    if (bits >> 2) & 1 == 1:
        targets.append(Describe_EN.TARGET_MAP[4])
    return targets

def position_bitmap(bits):
    offset = 0
    positions = []
    while offset < bits.bit_length():
        if (bits >> offset) & 1 == 1:
            positions.append(offset + 1)
        offset += 1
    return positions


def positions_2d_bitmap(bits_arr):
    # row check
    rows = []
    for i in range(5):
        if bits_arr[i] is None:
            bits_arr[i] = 0
        is_row = True
        not_row = True
        for j in range(6):
            is_row = is_row and (bits_arr[i] >> j) & 1 == 1
            not_row = not_row and (bits_arr[i] >> j) & 1 != 1
        if is_row:
            rows.append(i + 1)
    if len(rows) == 5:
        return Describe_EN.ALL, None, None
    if len(rows) == 0:
        rows = None
    # column check
    cols = []
    for j in range(6):
        is_col = True
        for i in range(5):
            is_col = is_col and (bits_arr[i] >> j) & 1 == 1
        if is_col:
            cols.append(j + 1)
    if len(cols) == 0:
        cols = None
    positions = []
    for i in range(5):
        row = ''
        for j in range(6):
            if (bits_arr[i] >> j) & 1 == 1:
                row += 'O'
            else:
                row += 'X'
        positions.append(row)
    return positions, rows, cols

# Condition subclass

class ESCondition(object):
    def full_description(self):
        return Describe_EN.condition(max(ai, rnd), self.hp_threshold, self.forced_one_time is not None, self.extra_description)

    def __init__(self, ai, rnd, params_arr):
        # If the monster has a hp_threshold value, the % chance is AI+RND under the threshold.
        self._ai = ai
        # The base % chance is rnd.
        self._rnd = rnd
        self.hp_threshold = None if params_arr[11] is None else params_arr[11]
        self.one_time = params_arr[13]
        self.forced_one_time = None
        self.description = Describe_EN.condition(max(ai, rnd), self.hp_threshold)
        self.extra_description = None

        # Force ignore hp threshold on skill if the monster has no AI.
        if self.hp_threshold and self._ai == 0:
            self.hp_threshold = None

        # If set, this only executes when a specified number of enemies remain.
        self.enemies_remaining = None

    def use_chance(self):
        """Returns the likelyhood that this condition will be used.

        If 100, it means it will always activate.
        Note that this implementation is incorrect; it should take a 'current HP' parameter and
        validate that against the hp_threshold. If under, the result should be ai+rnd.
        """
        return max(self._ai, self._rnd)


class ESAttack(object):
    def __init__(self, atk_multiplier, min_hits=1, max_hits=1):
        self.atk_multiplier = atk_multiplier
        self.min_hits = min_hits
        self.max_hits = max_hits
        self.description = Describe_EN.attack(self.atk_multiplier, self.min_hits, self.max_hits)

    @staticmethod
    def new_instance(atk_multiplier, min_hits=1, max_hits=1):
        if atk_multiplier is None:
            return None
        else:
            return ESAttack(atk_multiplier, min_hits, max_hits)

    def max_damage_pct(self) -> int:
        return self.atk_multiplier * self.max_hits

    def min_damage_pct(self) -> int:
        return self.atk_multiplier * self.min_hits


class ESBehavior(object):
    """Base class for any kind of enemy behavior, including logic, passives, and actions"""

    def __init__(self, skill: EnemySkillRef):
        self.enemy_skill_id = es_id(skill)
        self.name = name(skill)
        self.type = es_type(skill)
        self.description = None
        # This might be filled in during the processing step
        self.extra_description = None

        # Shitty hack to avoid passing CrossServerEsBehavior around
        self.jp_name = None

# Action
class ESAction(ESBehavior):
    def full_description(self):
        output = self.description
        if self.description == Describe_EN.es_default():
            output = self.attack.description
        elif self.attack:
            output += ', {:s}'.format(self.attack.description)

        if self.extra_description:
            output += ', {:s}'.format(self.extra_description)

        return output

    def __eq__(self, other):
        return other and self.enemy_skill_id == other.enemy_skill_id

    def __init__(self, skill: EnemySkillRef, description=Describe_EN.es_default(), attack=None):
        super().__init__(skill)
        self.description = description
        self.condition = None if ai(skill) is None or rnd(skill) is None \
            else ESCondition(ai(skill), rnd(skill), params(skill))
        self.attack = attack if attack is not None else ESAttack.new_instance(params(skill)[14])
        # param 15 controls displaying sprites on screen, used by Gintama

    def ends_battle(self):
        return False

    def is_conditional(self):
        return False

class ESInactivity(ESAction):
    def __init__(self, skill):
        super().__init__(
            skill,
            description=Describe_EN.skip()
        )


class ESDeathCry(ESAction):
    def __init__(self, skill):
        self.message = params(skill)[0]
        super().__init__(
            skill,
            description=Describe_EN.death_cry(self.message)
        )
        if self.condition:
            self.condition.extra_description = 'on death'


class ESAttackSinglehit(ESAction):
    def __init__(self, skill, atk_multiplier=100):
        super().__init__(
            skill,
            attack=ESAttack.new_instance(atk_multiplier)
        )


class ESDefaultAttack(ESAttackSinglehit):
    """Not a real behavior, used in place of a behavior when none is detected.

    Implies that a monster uses its normal attack.
    """

    def __init__(self):
        super().__init__(EnemySkillRef(1, 100, 0))
        self.name = Describe_EN.DEFAULT_ATTACK


class ESAttackMultihit(ESAction):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            attack=ESAttack.new_instance(params(skill)[3], params(skill)[1], params(skill)[2])
        )


class ESAttackPreemptive(ESAction):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            attack=ESAttack.new_instance(params(skill)[2])
        )


class ESBind(ESAction):
    def __init__(self, skill: EnemySkillRef, target_count=None, targets=None, attack=None):
        self.min_turns = params(skill)[2]
        self.max_turns = params(skill)[3]
        if target_count:
            self.target_count = target_count
        super().__init__(
            skill,
            description=Describe_EN.bind(self.min_turns, self.max_turns,
                                      target_count, targets),
            attack=attack
        )


class ESBindAttack(ESBind):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            target_count=params(skill)[5],
            targets=bind_bitmap(params(skill)[4]),
            attack=ESAttack.new_instance(params(skill)[1]))


class ESBindRandom(ESBind):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            target_count=params(skill)[1],
            targets=[Describe_EN.TARGET_MAP[0]]
        )


class ESBindTarget(ESBind):
    def __init__(self, skill: EnemySkillRef):
        targets = bind_bitmap(params(skill)[1])
        super().__init__(
            skill,
            target_count=len(targets),
            targets=targets
        )


class ESBindRandomSub(ESBind):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(skill, targets=[Describe_EN.TARGET_MAP[0] + ' ' + Describe_EN.TARGET_MAP[4]])


class ESBindAttribute(ESBind):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            target_count=None,
            targets=[Describe_EN.ATTRIBUTE_MAP[params(skill)[1]]]
        )
        self.target_attribute = Describe_EN.ATTRIBUTE_MAP[params(skill)[1]]

    def is_conditional(self):
        return True


class ESBindTyping(ESBind):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            target_count=None,
            targets=[Describe_EN.TYPING_MAP[params(skill)[1]]]
        )
        self.target_typing = Describe_EN.TYPING_MAP[params(skill)[1]]

    def is_conditional(self):
        return True


class ESBindSkill(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.min_turns = params(skill)[1]
        self.max_turns = params(skill)[2]
        super().__init__(
            skill,
            description=Describe_EN.bind(self.min_turns, self.max_turns, targets=Describe_EN.ACTIVE)
        )

    def is_conditional(self):
        return True

class ESBindAwoken(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.turns = params(skill)[1]
        super().__init__(
            skill,
            description=Describe_EN.bind(self.turns, None, None, targets=Describe_EN.AWOKEN)
        )

    def is_conditional(self):
        return True

class ESOrbChange(ESAction):
    def __init__(self, skill: EnemySkillRef, orb_from, orb_to):
        self.orb_from = orb_from
        self.orb_to = orb_to
        super().__init__(
            skill,
            description=Describe_EN.orb_change(self.orb_from, self.orb_to)
        )

    def is_conditional(self):
        return self.orb_from.lower() != 'random'


class ESOrbChangeConditional(ESOrbChange):
    """Parent class for orb changes that may not execute."""

    def __init__(self, skill: EnemySkillRef, orb_from, orb_to):
        super().__init__(skill, orb_from, orb_to)

    def is_conditional(self):
        return True


class ESOrbChangeSingle(ESOrbChangeConditional):
    def __init__(self, skill: EnemySkillRef):
        from_attr = Describe_EN.ATTRIBUTE_MAP[params(skill)[1]]
        to_attr = Describe_EN.ATTRIBUTE_MAP[params(skill)[2]]
        super().__init__(skill, from_attr, to_attr)


class ESOrbChangeAttackBits(ESOrbChangeConditional):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            orb_from=attribute_bitmap(params(skill)[2]),
            orb_to=attribute_bitmap(params(skill)[3])
        )
        self.attack = ESAttack.new_instance(params(skill)[1])


class ESJammerChangeSingle(ESOrbChangeConditional):
    def __init__(self, skill: EnemySkillRef):
        from_attr = Describe_EN.ATTRIBUTE_MAP[params(skill)[1]]
        to_attr = Describe_EN.ATTRIBUTE_MAP[6]
        super().__init__(skill, from_attr, to_attr)

    def is_conditional(self):
        return True


class ESJammerChangeRandom(ESOrbChange):
    def __init__(self, skill: EnemySkillRef):
        self.random_count = int(params(skill)[1])
        from_attr = 'Random {:d}'.format(self.random_count)
        to_attr = Describe_EN.ATTRIBUTE_MAP[6]
        super().__init__(skill, from_attr, to_attr)


class ESPoisonChangeSingle(ESOrbChangeConditional):
    def __init__(self, skill: EnemySkillRef):
        from_attr = Describe_EN.ATTRIBUTE_MAP[params(skill)[1]]
        to_attr = Describe_EN.ATTRIBUTE_MAP[7]
        super().__init__(skill, from_attr, to_attr)


class ESPoisonChangeRandom(ESOrbChange):
    def __init__(self, skill: EnemySkillRef):
        self.random_count = int(params(skill)[1])
        from_attr = 'Random {:d}'.format(self.random_count)
        to_attr = Describe_EN.ATTRIBUTE_MAP[7]
        # TODO: This skill (and possibly others) seem to have an 'excludes hearts'
        # clause; either it's innate to this skill, or it's in params[2] (many monsters have
        # a 1 in that slot, not all though).
        super().__init__(skill, from_attr, to_attr)


class ESMortalPoisonChangeRandom(ESOrbChange):
    def __init__(self, skill: EnemySkillRef):
        self.random_count = int(params(skill)[1])
        from_attr = 'Random {:d}'.format(self.random_count)
        to_attr = Describe_EN.ATTRIBUTE_MAP[8]
        super().__init__(skill, from_attr, to_attr)


class ESOrbChangeAttack(ESOrbChange):
    def __init__(self, skill: EnemySkillRef, orb_from=None, orb_to=None):
        from_attr = Describe_EN.ATTRIBUTE_MAP[params(skill)[2]] if orb_from is None else orb_from
        to_attr = Describe_EN.ATTRIBUTE_MAP[params(skill)[3]] if orb_to is None else orb_to
        super().__init__(skill, orb_from=from_attr, orb_to=to_attr)
        self.attack = ESAttack.new_instance(params(skill)[1])


class ESPoisonChangeRandomAttack(ESOrbChangeAttack):
    def __init__(self, skill: EnemySkillRef):
        self.random_count = int(params(skill)[2])
        from_attr = 'Random {:d}'.format(self.random_count)
        to_attr = Describe_EN.ATTRIBUTE_MAP[7]
        super().__init__(skill, orb_from=from_attr, orb_to=to_attr)

    def is_conditional(self):
        return False


class ESBlind(ESAction):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            description=Describe_EN.blind(),
            attack=ESAttack.new_instance(params(skill)[1])
        )


class ESBlindStickyRandom(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.turns = params(skill)[1]
        self.min_count = params(skill)[2]
        self.max_count = params(skill)[3]
        super().__init__(
            skill,
            description=Describe_EN.blind_sticky_random(self.turns, self.min_count, self.max_count)
        )


class ESBlindStickyFixed(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.turns = params(skill)[1]
        self.position_str, self.position_rows, self.position_cols\
            = positions_2d_bitmap(params(skill)[2:7])
        super().__init__(
            skill,
            description=Describe_EN.blind_sticky_fixed(self.turns)
        )


class ESDispel(ESAction):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            description=Describe_EN.dispel()
        )


class ESStatusShield(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.turns = params(skill)[1]
        super().__init__(
            skill,
            description=Describe_EN.status_shield(self.turns)
        )


class ESRecover(ESAction):
    def __init__(self,  skill, target):
        self.min_amount = params(skill)[1]
        self.max_amount = params(skill)[2]
        self.target = target
        super().__init__(
            skill,
            description=Describe_EN.recover(self.min_amount, self.max_amount, self.target)
        )


class ESRecoverEnemy(ESRecover):
    def __init__(self,  skill):
        super().__init__(skill, target=Describe_EN.ENEMY)


class ESRecoverEnemyAlly(ESRecover):
    def __init__(self,  skill):
        super().__init__(skill, target=Describe_EN.ENEMY_ALLY)
        if self.condition:
            self.condition.extra_description = Describe_EN.ally_killed()
            self.condition.enemies_remaining = 1


class ESRecoverPlayer(ESRecover):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(skill, target=Describe_EN.PLAYER)


class ESEnrage(ESAction):
    def __init__(self, skill: EnemySkillRef, multiplier, turns):
        self.multiplier = multiplier
        self.turns = turns
        super().__init__(
            skill,
            description=Describe_EN.enrage(self.multiplier, self.turns)
        )


class ESStorePower(ESEnrage):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            multiplier=100 + params(skill)[1],
            turns=0
        )


class ESAttackUp(ESEnrage):
    def __init__(self, skill: EnemySkillRef, multiplier, turns):
        super().__init__(
            skill,
            multiplier=multiplier,
            turns=turns
        )


class ESAttackUPRemainingEnemies(ESAttackUp):
    def __init__(self, skill: EnemySkillRef):
        self.enemy_count = params(skill)[1]
        super().__init__(
            skill,
            multiplier=params(skill)[3],
            turns=params(skill)[2]
        )
        if self.condition and self.enemy_count:
            self.condition.extra_description = Describe_EN.enemy_remain(self.enemy_count)


class ESAttackUpStatus(ESAttackUp):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            multiplier=params(skill)[2],
            turns=params(skill)[1]
        )
        if self.condition:
            self.condition.extra_description = Describe_EN.post_status_effect()


class ESAttackUPCooldown(ESAttackUp):
    def __init__(self, skill: EnemySkillRef):
        # enrage cannot trigger until this many turns have passed
        cooldown_value = params(skill)[1] or 0
        self.turn_cooldown = cooldown_value if cooldown_value > 1 else None
        super().__init__(
            skill,
            multiplier=params(skill)[3],
            turns=params(skill)[2]
        )
        if self.condition and self.turn_cooldown:
            self.condition.extra_description = Describe_EN.after_some_turns(self.turn_cooldown)


class ESDebuff(ESAction):
    def __init__(self, skill: EnemySkillRef, debuff_type, amount, unit):
        self.turns = params(skill)[1]
        self.type = debuff_type
        self.amount = amount
        self.unit = unit
        super().__init__(
            skill,
            description=Describe_EN.debuff(self.type, self.amount, self.unit, self.turns)
        )


class ESDebuffMovetime(ESDebuff):
    def __init__(self, skill: EnemySkillRef):
        if params(skill)[2] is not None:
            super().__init__(
                skill,
                debuff_type='movetime',
                amount=-params(skill)[2] / 10,
                unit='s'
            )
        elif params(skill)[3] is not None:
            super().__init__(
                skill,
                debuff_type='movetime',
                amount=params(skill)[3],
                unit='%'
            )


class ESDebuffRCV(ESDebuff):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            debuff_type='RCV',
            amount=params(skill)[2],
            unit='%'
        )


class ESEndBattle(ESAction):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            description=Describe_EN.end_battle()
        )
        if self.condition:
            self.condition.chance = 100

    def ends_battle(self):
        return True

class ESChangeAttribute(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.attributes = list(OrderedDict.fromkeys([Describe_EN.ATTRIBUTE_MAP[x] for x in params(skill)[1:6]]))
        super().__init__(
            skill,
            description=Describe_EN.change_attribute(self.attributes)
        )


class ESGravity(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.percent = params(skill)[1]
        super().__init__(
            skill,
            description=Describe_EN.gravity(self.percent)
        )


class ESAbsorb(ESAction):
    def __init__(self, skill: EnemySkillRef, source):
        self.min_turns = params(skill)[1]
        self.max_turns = params(skill)[2]
        super().__init__(
            skill,
            description=Describe_EN.absorb(source, self.min_turns, self.max_turns)
        )


class ESAbsorbAttribute(ESAbsorb):
    def __init__(self, skill: EnemySkillRef):
        self.attributes = attribute_bitmap(params(skill)[3])
        super().__init__(
            skill,
            Describe_EN.join_attr(self.attributes)
        )


class ESAbsorbCombo(ESAbsorb):
    def __init__(self, skill: EnemySkillRef):
        self.combo_threshold = params(skill)[3]
        super().__init__(
            skill,
            Describe_EN.combo_threshold(self.combo_threshold)
        )


class ESAbsorbThreshold(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.turns = params(skill)[1]
        self.absorb_threshold = params(skill)[2]
        super().__init__(
            skill,
            description=Describe_EN.absorb('damage >= {}'.format(self.absorb_threshold), self.turns)
        )


class ESVoidShield(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.turns = params(skill)[1]
        # mysterious params[2], always 1055 except for no.2485 Hakumen no Mono who has 31
        self.void_threshold = params(skill)[3]
        super().__init__(
            skill,
            description=Describe_EN.void(self.void_threshold, self.turns)
        )


class ESDamageShield(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.turns = params(skill)[1]
        self.shield_percent = params(skill)[2]
        super().__init__(
            skill,
            description=Describe_EN.damage_reduction('all sources', self.shield_percent, self.turns)
        )


class ESInvulnerableOn(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.turns = params(skill)[1]
        super().__init__(
            skill,
            description=Describe_EN.damage_reduction('all sources', turns=self.turns)
        )


class ESInvulnerableOff(ESAction):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            description=Describe_EN.invulnerable_off()
        )


class ESSkyfall(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.min_turns = params(skill)[2]
        self.max_turns = params(skill)[3]
        self.attributes = attribute_bitmap(params(skill)[1])
        self.chance = params(skill)[4]
        if es_type(skill) == 68:
            super().__init__(
                skill,
                description=Describe_EN.skyfall(self.attributes, self.chance,
                                             self.min_turns, self.max_turns)
            )
        elif es_type(skill) == 96:
            super().__init__(
                skill,
                description=Describe_EN.skyfall(self.attributes, self.chance,
                                             self.min_turns, self.max_turns, True)
            )


class ESLeaderSwap(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.turns = self.turns = params(skill)[1]
        super().__init__(
            skill,
            description=Describe_EN.leadswap(self.turns)
        )


class ESFixedOrbSpawn(ESAction):
    def __init__(self, skill: EnemySkillRef, position_type, positions, attributes, description, attack=None):
        self.position_type = position_type
        self.positions = positions
        self.attributes = attributes
        super().__init__(
            skill,
            description=description,
            attack=attack
        )


class ESRowColSpawn(ESFixedOrbSpawn):
    def __init__(self, skill: EnemySkillRef, position_type):
        super().__init__(
            skill,
            position_type=position_type,
            positions=position_bitmap(params(skill)[1]),
            attributes=attribute_bitmap(params(skill)[2]),
            description=Describe_EN.row_col_spawn(
                position_type,
                position_bitmap(params(skill)[1]),
                attribute_bitmap(params(skill)[2])
            )
        )


class ESRowColSpawnMulti(ESFixedOrbSpawn):
    RANGE_MAP = {
        76: range(1, 4, 2),
        77: range(1, 6, 2),
        78: range(1, 4, 2),
        79: range(1, 6, 2)
    }

    def __init__(self, skill: EnemySkillRef, position_type):
        positions = []
        attributes = []
        for i in self.RANGE_MAP[es_type(skill)]:
            if params(skill)[i] and params(skill)[i + 1]:
                p = position_bitmap(params(skill)[i])
                a = attribute_bitmap(params(skill)[i + 1])
                positions.append(p)
                attributes.append(a)
        super().__init__(
            skill,
            position_type=position_type,
            positions=positions,
            attributes=attributes,
            description=Describe_EN.row_col_spawn_multi(position_type, positions, attributes),
            attack=ESAttack.new_instance(params(skill)[7]) if es_type(skill) in [77, 79] else None
        )


class ESColumnSpawn(ESRowColSpawn):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            position_type=Describe_EN.COLUMN
        )


class ESColumnSpawnMulti(ESRowColSpawnMulti):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            position_type=Describe_EN.COLUMN
        )


class ESRowSpawn(ESRowColSpawn):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            position_type=Describe_EN.ROW
        )


class ESRowSpawnMulti(ESRowColSpawnMulti):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            position_type=Describe_EN.ROW
        )


class ESRandomSpawn(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.count = params(skill)[1]
        self.attributes = attribute_bitmap(params(skill)[2])
        self.condition_attributes = attribute_bitmap(params(skill)[3], inverse=True)

        super().__init__(
            skill,
            description=Describe_EN.random_orb_spawn(self.count, self.attributes)
        )
        if self.condition and self.condition_attributes:
            self.condition.extra_description = Describe_EN.attribute_exists(self.condition_attributes)

    def is_conditional(self):
        return len(self.condition_attributes or []) < 6

class ESBombRandomSpawn(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.count = params(skill)[2]
        self.locked = params(skill)[8] == 1
        super().__init__(
            skill,
            description=Describe_EN.random_orb_spawn(
                self.count, [Describe_EN.ATTRIBUTE_MAP[10]] if self.locked else [Describe_EN.ATTRIBUTE_MAP[9]])
        )


class ESBombFixedSpawn(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.count = params(skill)[2]
        self.position_str, self.position_rows, self.position_cols = positions_2d_bitmap(params(skill)[2:7])
        self.locked = params(skill)[8] == 1
        bomb_type = [Describe_EN.ATTRIBUTE_MAP[10]] if self.locked else [Describe_EN.ATTRIBUTE_MAP[9]]
        super().__init__(
            skill,
            description=Describe_EN.board_change(bomb_type)
            if self.position_rows is not None and len(self.position_rows) == 6
            and self.position_cols is not None and len(self.position_cols) == 5
            else Describe_EN.fixed_orb_spawn(bomb_type)
        )


class ESBoardChange(ESAction):
    def __init__(self, skill: EnemySkillRef, attributes=None, attack=None):
        if attributes:
            self.attributes = attributes
        else:
            self.attributes = attribute_bitmap(params(skill)[1])
        super().__init__(
            skill,
            description=Describe_EN.board_change(self.attributes),
            attack=attack
        )


class ESBoardChangeAttackFlat(ESBoardChange):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            [Describe_EN.ATTRIBUTE_MAP[x] for x in params(skill)[2:params(skill).index(-1)]],
            ESAttack.new_instance(params(skill)[1])
        )


class ESBoardChangeAttackBits(ESBoardChange):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            attribute_bitmap(params(skill)[2]),
            ESAttack.new_instance(params(skill)[1])
        )


class SubSkill(object):
    def __init__(self, enemy_skill_id):
        self.enemy_skill_id = enemy_skill_id
        self.enemy_skill_info = enemy_skill_map[enemy_skill_id]
        self.enemy_ai = None
        self.enemy_rnd = None


class ESSkillSet(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.skill_list = [] # List[ESAction]
        i = 0
        for s in params(skill)[1:11]:
            if s is not None:
                sub_skill = EnemySkillRef(s, 0, 0)
                if es_type(sub_skill) in BEHAVIOR_MAP:
                    behavior = BEHAVIOR_MAP[es_type(sub_skill)](sub_skill)
                    self.skill_list.append(behavior)
                else:
                    self.skill_list.append(EnemySkillUnknown(sub_skill))
            i += 1
        super().__init__(
            skill,
            description=Describe_EN.skillset()
        )

        self.name = ' + '.join(map(lambda s: s.name, self.skill_list))

    def full_description(self):
        output = ' + '.join(map(lambda s: s.full_description(), self.skill_list))
        if self.extra_description:
            output += ', {:s}'.format(self.extra_description)
        return output

    def ends_battle(self):
        return any([s.ends_battle() for s in self.skill_list])

class ESSkillSetOnDeath(ESSkillSet):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(skill)
        if self.condition:
            self.condition.extra_description = Describe_EN.on_death()

    def has_action(self) -> bool:
        """Helper that determines if the skillset does stuff other than emote."""
        for x in self.skill_list:
            if type(x) == ESSkillSet:
                if any([type(y) != ESInactivity for y in x.skill_list]):
                    return True
            elif type(x) != ESInactivity:
                return True
        return False


class ESSkillDelay(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.min_turns = params(skill)[1]
        self.max_turns = params(skill)[2]
        super().__init__(
            skill,
            description=Describe_EN.skill_delay(self.min_turns, self.max_turns)
        )


class ESOrbLock(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.count = params(skill)[2]
        self.attributes = attribute_bitmap(params(skill)[1])
        super().__init__(
            skill,
            description=Describe_EN.orb_lock(self.count, self.attributes)
        )

    def is_conditional(self):
        return self.attributes != [Describe_EN.RANDOM] and len(self.attributes) != 9


class ESOrbSeal(ESAction):
    def __init__(self, skill: EnemySkillRef, position_type, positions):
        self.turns = params(skill)[2]
        self.position_type = position_type
        self.positions = positions
        super().__init__(
            skill,
            description=Describe_EN.orb_seal(self.turns, self.position_type, self.positions)
        )


class ESOrbSealColumn(ESOrbSeal):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            position_type=Describe_EN.COLUMN,
            positions=position_bitmap(params(skill)[1])
        )


class ESOrbSealRow(ESOrbSeal):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            position_type=Describe_EN.ROW,
            positions=position_bitmap(params(skill)[1])
        )


class ESCloud(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.turns = params(skill)[1]
        self.cloud_width = params(skill)[2]
        self.cloud_height = params(skill)[3]
        self.origin_y = params(skill)[4]
        self.origin_x = params(skill)[5]
        super().__init__(
            skill,
            description=Describe_EN.cloud(
                self.turns, self.cloud_width, self.cloud_height, self.origin_x, self.origin_y)
        )


class ESFixedStart(ESAction):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            description=Describe_EN.fixed_start()
        )


class ESAttributeBlock(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.turns = params(skill)[1]
        self.attributes = attribute_bitmap(params(skill)[2])
        super().__init__(
            skill,
            description=Describe_EN.attribute_block(self.turns, self.attributes)
        )


class ESSpinners(ESAction):
    def __init__(self, skill: EnemySkillRef, position_type, position_description):
        self.turns = params(skill)[1]
        self.speed = params(skill)[2]
        self.position_type = position_type
        super().__init__(
            skill,
            description=Describe_EN.spinners(self.turns, self.speed, position_description)
        )


class ESSpinnersRandom(ESSpinners):
    def __init__(self, skill: EnemySkillRef):
        self.count = params(skill)[3]
        super().__init__(
            skill,
            position_type=Describe_EN.RANDOM,
            position_description=Describe_EN.random_position(self.count)
        )


class ESSpinnersFixed(ESSpinners):
    def __init__(self, skill: EnemySkillRef):
        self.position_str, self.position_rows, self.position_cols = positions_2d_bitmap(params(skill)[3:8])
        super().__init__(
            skill,
            position_type=Describe_EN.FIXED,
            position_description=Describe_EN.SPECIFIC
        )


class ESMaxHPChange(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.turns = params(skill)[3]
        if params(skill)[1] is not None:
            self.max_hp = params(skill)[1]
            self.hp_change_type = Describe_EN.PERCENT
        elif params(skill)[2] is not None:
            self.max_hp = params(skill)[2]
            self.hp_change_type = Describe_EN.FLAT
        super().__init__(
            skill,
            description=Describe_EN.max_hp_change(self.turns, self.max_hp, self.hp_change_type)
        )


class ESFixedTarget(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.target = params(skill)[1]
        super().__init__(
            skill,
            description=Describe_EN.forced_target()
        )


class ESTurnChangeActive(ESAction):
    def __init__(self, skill: EnemySkillRef):
        self.turn_counter = params(skill)[2]
        self.enemy_seq = params(skill)[1]
        super().__init__(
            skill,
            description=Describe_EN.turn_change(self.turn_counter)
        )


# Passive
class ESPassive(ESBehavior):
    def full_description(self):
        return self.description

    def __init__(self, skill: EnemySkillRef, description):
        super().__init__(skill)
        self.description = description


class ESAttributeResist(ESPassive):
    def __init__(self, skill: EnemySkillRef):
        self.attributes = attribute_bitmap(params(skill)[1])
        self.shield_percent = params(skill)[2]
        super().__init__(
            skill,
            description=Describe_EN.damage_reduction(
                ', '.join(self.attributes), percent=self.shield_percent)
        )


class ESResolve(ESPassive):
    def __init__(self, skill: EnemySkillRef):
        self.hp_threshold = params(skill)[1]
        super().__init__(
            skill,
            description=Describe_EN.resolve(self.hp_threshold)
        )


class ESTurnChangePassive(ESPassive):
    def __init__(self, skill: EnemySkillRef):
        self.hp_threshold = params(skill)[1]
        self.turn_counter = params(skill)[2]
        super().__init__(
            skill,
            description=Describe_EN.turn_change(self.turn_counter, self.hp_threshold)
        )


class ESTypeResist(ESPassive):
    def __init__(self, skill: EnemySkillRef):
        self.types = typing_bitmap(params(skill)[1])
        self.shield_percent = params(skill)[2]
        super().__init__(
            skill,
            description=Describe_EN.damage_reduction(
                ', '.join(self.types), percent=self.shield_percent)
        )


# Logic
class ESLogic(ESBehavior):
    def __init__(self, skill: EnemySkillRef, effect=None):
        self.enemy_skill_id = es_id(skill)
        self.effect = effect
        self.type = es_type(skill)

    @property
    def name(self):
        return type(self).__name__

    @property
    def description(self):
        return self.effect

    def full_description(self):
        return self.effect


class ESNone(ESLogic):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(skill, Describe_EN.NOTHING)


class ESFlagOperation(ESLogic):
    FLAG_OPERATION_MAP = {
        22: 'SET',
        24: 'UNSET',
        44: 'OR',
        45: 'XOR'
    }

    def __init__(self, skill: EnemySkillRef):
        super().__init__(skill, effect='flag_operation')
        self.flag = ai(skill)
        self.flag_bin = bin(self.flag)
        self.operation = self.FLAG_OPERATION_MAP[es_type(skill)]

    @property
    def description(self):
        return 'flag {} {}'.format(self.operation, self.flag_bin)


class ESSetCounter(ESLogic):
    COUNTER_SET_MAP = {
        25: '=',
        26: '+',
        27: '-'
    }

    def __init__(self, skill: EnemySkillRef):
        super().__init__(skill, effect='set_counter')
        self.counter = ai(skill) if es_type(skill) == 25 else 1
        self.set = self.COUNTER_SET_MAP[es_type(skill)]

    @property
    def description(self):
        return 'counter {} {}'.format(self.set, self.counter)


class ESSetCounterIf(ESLogic):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(skill, effect='set_counter_if')
        self.effect = 'set_counter_if'
        self.counter_is = ai(skill)
        self.counter = rnd(skill)

    @property
    def description(self):
        return 'set counter = {} if counter == {}'.format(self.counter, self.counter_is)


class ESBranch(ESLogic):
    def __init__(self, skill: EnemySkillRef, branch_condition, compare='='):
        self.branch_condition = branch_condition
        self.branch_value = ai(skill)
        self.target_round = rnd(skill)
        self.compare = compare
        super().__init__(skill, effect='branch')

    @property
    def description(self):
        return 'Branch on {} {} {}, target rnd {}'.format(
            self.branch_condition, self.compare, str(self.branch_value), self.target_round)


class ESBranchFlag(ESBranch):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            branch_condition='flag',
            compare='&'
        )


class ESBranchHP(ESBranch):
    HP_COMPARE_MAP = {
        28: '<',
        29: '>'
    }

    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            branch_condition='hp',
            compare=self.HP_COMPARE_MAP[es_type(skill)]
        )


class ESBranchCounter(ESBranch):
    COUNTER_COMPARE_MAP = {
        30: '<',
        31: '=',
        32: '>'
    }

    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            branch_condition='counter',
            compare=self.COUNTER_COMPARE_MAP[es_type(skill)]
        )


class ESBranchLevel(ESBranch):
    LEVEL_COMPARE_MAP = {
        33: '<',
        34: '=',
        35: '>'
    }

    def __init__(self, skill: EnemySkillRef):
        super().__init__(
            skill,
            branch_condition='level',
            compare=self.LEVEL_COMPARE_MAP[es_type(skill)]
        )


class ESEndPath(ESLogic):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(skill, effect='end_turn')


class ESCountdown(ESLogic):
    def __init__(self, skill: EnemySkillRef):
        # decrement counter and end path
        super().__init__(skill, effect='countdown')


class ESCountdownMessage(ESAction):
    """Dummy action class to represent displaying countdown numbers"""
    def __init__(self, enemy_skill_id, current_counter=0):
        super(ESCountdownMessage, self).__init__(EnemySkillRef(enemy_skill_id, 0, 0))
        self.enemy_skill_id += 1000 * current_counter
        self.current_counter = current_counter
        self.name = 'Countdown Message'
        self.description = Describe_EN.countdown(self.current_counter)


class ESPreemptive(ESLogic):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(skill, effect='preemptive')
        self.level = params(skill)[1]

    @property
    def description(self):
        return 'Enable preempt if level {}'.format(self.level)


class ESBranchCard(ESBranch):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(skill, branch_condition='player_cards', compare='HAS')
        self.branch_value = [x for x in params(skill) if x is not None]


class ESBranchCombo(ESBranch):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(skill, branch_condition='combo', compare='>=')


class ESBranchRemainingEnemies(ESBranch):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(skill, branch_condition='remaining enemies', compare='<=')


# Unknown
class EnemySkillUnknown(ESBehavior):
    def __init__(self, skill: EnemySkillRef):
        super().__init__(skill)
        self.description = 'unknown'

    def full_description(self):
        return self.description

    def ends_battle(self):
        return False

BEHAVIOR_MAP = {
    # SKILLS
    1: ESBindRandom,
    2: ESBindAttribute,
    3: ESBindTyping,
    4: ESOrbChangeSingle,
    5: ESBlind,
    6: ESDispel,
    7: ESRecoverEnemy,
    8: ESStorePower,
    # type 9 skills are unused, but there's 3 and they seem to buff defense
    12: ESJammerChangeSingle,
    13: ESJammerChangeRandom,
    14: ESBindSkill,
    15: ESAttackMultihit,
    16: ESInactivity,
    17: ESAttackUPRemainingEnemies,
    18: ESAttackUpStatus,
    19: ESAttackUPCooldown,
    20: ESStatusShield,
    39: ESDebuffMovetime,
    40: ESEndBattle,
    46: ESChangeAttribute,
    47: ESAttackPreemptive,
    48: ESOrbChangeAttack,
    50: ESGravity,
    52: ESRecoverEnemyAlly,
    53: ESAbsorbAttribute,
    54: ESBindTarget,
    55: ESRecoverPlayer,
    56: ESPoisonChangeSingle,
    60: ESPoisonChangeRandom,
    61: ESMortalPoisonChangeRandom,
    62: ESBlind,
    63: ESBindAttack,
    64: ESPoisonChangeRandomAttack,
    65: ESBindRandomSub,
    66: ESInactivity,
    67: ESAbsorbCombo,
    68: ESSkyfall,
    69: ESDeathCry,
    71: ESVoidShield,
    74: ESDamageShield,
    75: ESLeaderSwap,
    76: ESColumnSpawnMulti,
    77: ESColumnSpawnMulti,
    78: ESRowSpawnMulti,
    79: ESRowSpawnMulti,
    81: ESBoardChangeAttackFlat,
    82: ESAttackSinglehit,  # called "Disable Skill" in EN but "Normal Attack" in JP
    83: ESSkillSet,
    84: ESBoardChange,
    85: ESBoardChangeAttackBits,
    86: ESRecoverEnemy,
    87: ESAbsorbThreshold,
    88: ESBindAwoken,
    89: ESSkillDelay,
    92: ESRandomSpawn,
    93: ESNone,  # FF animation (???)
    94: ESOrbLock,
    95: ESSkillSetOnDeath,
    96: ESSkyfall,
    97: ESBlindStickyRandom,
    98: ESBlindStickyFixed,
    99: ESOrbSealColumn,
    100: ESOrbSealRow,
    101: ESFixedStart,
    102: ESBombRandomSpawn,
    103: ESBombFixedSpawn,
    104: ESCloud,
    105: ESDebuffRCV,
    107: ESAttributeBlock,
    108: ESOrbChangeAttackBits,
    109: ESSpinnersRandom,
    110: ESSpinnersFixed,
    111: ESMaxHPChange,
    112: ESFixedTarget,
    119: ESInvulnerableOn,
    121: ESInvulnerableOff,
    122: ESTurnChangeActive,
    123: ESInvulnerableOn,  # hexa's invulnerable gets special type because reasons

    # LOGIC
    0: ESNone,
    22: ESFlagOperation,
    23: ESBranchFlag,
    24: ESFlagOperation,
    25: ESSetCounter,
    26: ESSetCounter,
    27: ESSetCounter,
    28: ESBranchHP,
    29: ESBranchHP,
    30: ESBranchCounter,
    31: ESBranchCounter,
    32: ESBranchCounter,
    33: ESBranchLevel,
    34: ESBranchLevel,
    35: ESBranchLevel,
    36: ESEndPath,
    37: ESCountdown,
    38: ESSetCounterIf,
    43: ESBranchFlag,
    44: ESFlagOperation,
    45: ESFlagOperation,
    49: ESPreemptive,
    90: ESBranchCard,
    113: ESBranchCombo,
    120: ESBranchRemainingEnemies,

    # PASSIVES
    72: ESAttributeResist,
    73: ESResolve,
    106: ESTurnChangePassive,
    118: ESTypeResist,
}


def apply_es_overrides(es):
    """Apply manually configured overrides to some skills.

    We were able to resolve any issues here so this is no longer necessary.
    """
    pass


def inject_implicit_onetime(card: BookCard, behavior: List[ESAction]):
    """Injects one_time values into specific categories of skills.

    Currently only ESBindRandom but other early skills may need this.
    This seems to fix things like Hera-Is and others, but breaks some like Metatron Tama.

    TODO: Investigate if this has an ai/rnd interaction, like the hp_threshold issue.
    There may be some interaction with slots 52/53/54 to take into account but unclear.
    """
    if card.enemy_skill_counter_increment != 0:
        # This seems unlikely to be correct.
        return
    max_flag = max([0] + [x.condition.one_time for x in behavior if hasattr(x, 'condition') and x.condition.one_time])
    next_flag = pow(2, ceil(log(max_flag + 1)/log(2)))
    for b in behavior:
        if type(b) in [ESBindRandom, ESBindAttribute] and not b.condition.one_time and b.condition.use_chance() == 100:
            b.condition.forced_one_time = next_flag
            next_flag = next_flag << 1


def extract_behavior(card: BookCard, enemy_skillset: List[EnemySkillRef]):
    if enemy_skill_map is None:
        return None
    behavior = []
    for skill in enemy_skillset:
        skill_type = es_type(skill)
        if skill_type in BEHAVIOR_MAP:
            new_es = BEHAVIOR_MAP[skill_type](skill)
        else:  # skills not parsed
            new_es = EnemySkillUnknown(skill)
        apply_es_overrides(new_es)
        behavior.append(new_es)

    inject_implicit_onetime(card, behavior)
    return behavior


def reformat_json(card_data):
    reformatted = []
    for enemy in card_data:
        if len(enemy.enemy_skill_refs) == 0:
            continue

        behavior = {}
        passives = {}
        unknown = {}

        # Sequence of enemy skill is important for logic
        for idx, skill in enumerate(enemy.enemy_skill_refs):
            idx += 1
            if es_type(skill) in BEHAVIOR_MAP:
                b = BEHAVIOR_MAP[es_type(skill)](skill)
                if issubclass(type(b), ESPassive):
                    passives[idx] = b
                else:
                    behavior[idx] = b
            else:
                unknown[idx] = EnemySkillUnknown(skill)
        reformatted.append({
            'MONSTER_NO': enemy.card_id,
            'BEHAVIOR': behavior,
            'PASSIVE': passives,
            'UNKNOWN': unknown
        })

    return reformatted


def reformat(raw_cards_json, enemy_skills_json, output_json, mon_id=None):
    global enemy_skill_map
    print('-- Parsing Enemies --\n')
    with open(enemy_skills_json) as f:
        enemy_skill_map = {x.enemy_skill_id: x for x
                           in json.load(f, object_hook=lambda json_dict: DictWithAttributeAccess(json_dict))}
    if enemy_skill_map is None:
        print('Failed to load enemy skill info\n')
    print('Enemy skill json loaded\n')
    with open(raw_cards_json) as f:
        card_data = json.load(f, object_hook=lambda json_dict: DictWithAttributeAccess(json_dict))
    print('Raw cards json loaded\n')
    if mon_id:
        reformatted = reformat_json([card_data[mon_id]])
    else:
        reformatted = reformat_json(card_data)

    print('Converted {active} enemies\n'.format(active=len(reformatted)))

    with open(output_json, 'w') as f:
        json.dump(reformatted, f, indent=4, sort_keys=True, default=lambda x: x.__dict__)
    print('Result saved\n')
    print('-- End Enemies --\n')
