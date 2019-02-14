from collections import OrderedDict
import json

from ..common import pad_util


def dump_obj(o):
    if isinstance(o, ESSkillSet):
        msg = 'SkillSet:'
        msg += '\n\tCondition: {}'.format(json.dumps(o.condition,
                                                     sort_keys=True, default=lambda x: x.__dict__))
        for idx, behavior in enumerate(o.skill_list):
            msg += '\n\t{} {} {}'.format(idx, type(behavior).__name__,
                                         json.dumps(behavior, sort_keys=True, default=lambda x: x.__dict__))
        return msg
    else:
        return '{} {}'.format(type(o).__name__, json.dumps(o, sort_keys=True, default=lambda x: x.__dict__))


ATTRIBUTE_MAP = {
    -1: 'Random',
    None: 'Fire',
    0: 'Fire',
    1: 'Water',
    2: 'Wood',
    3: 'Light',
    4: 'Dark',
    5: 'Heal',
    6: 'Jammer',
    7: 'Poison',
    8: 'Mortal Poison',
    9: 'Bomb',
}

TYPING_MAP = {
    1: 'Balanced',
    2: 'Physical',
    3: 'Healer',
    4: 'Dragon',
    5: 'God',
    6: 'Attacker',
    7: 'Devil',
    8: 'Machine',
}


class DictWithAttributeAccess(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


enemy_skill_map = None


def es_id(skill):
    return skill.enemy_skill_id


def name(skill):
    return enemy_skill_map[skill.enemy_skill_id].name


def params(skill):
    return enemy_skill_map[skill.enemy_skill_id].params


def ai(skill):
    return skill.enemy_ai


def rnd(skill):
    return skill.enemy_rnd


def es_type(skill):
    return enemy_skill_map[skill.enemy_skill_id].type


def attribute_bitmap(bits):
    if bits == -1:
        return ['random']
    offset = 0
    atts = []
    while offset < bits.bit_length():
        if (bits >> offset) & 1 == 1:
            atts.append(ATTRIBUTE_MAP[offset])
        offset += 1
    return atts


def typing_bitmap(bits):
    if bits == -1:
        return []
    offset = 0
    types = []
    while offset < bits.bit_length():
        if (bits >> offset) & 1 == 1:
            types.append(TYPING_MAP[offset])
        offset += 1
    return types


def bind_leader_bitmap(bits):
    targets = []
    if (bits >> 0) & 1 == 1:
        targets.append('own leader')
    if (bits >> 1) & 1 == 1:
        targets.append('friend leader')
    if len(targets) == 1:
        return targets[0]
    else:
        return 'both leaders'


def ordinal(n): return "%d%s" % (n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])


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
        return 'all', None, None
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


# description


class Describe:
    @staticmethod
    def condition(chance, hp=None, one_time=False):
        output = []
        if 0 < chance < 100 and not one_time:
            output.append('{:d}% chance'.format(chance))
        if hp:
            output.append('when <{:d}% HP'.format(hp))
        if one_time:
            if len(output) > 0:
                output.append(',')
            output.append('one-time use')
        return ' '.join(output).capitalize() if len(output) > 0 else None

    @staticmethod
    def attack(mult, min_hit=1, max_hit=1):
        output = ''
        if min_hit == max_hit:
            output += 'Deal {:d}% damage'.format(int(min_hit) * int(mult))
            if int(min_hit) > 1:
                output += ' ({:d} hits, {:d}% each)'.format(min_hit, mult)
        else:
            output += 'Deal {:d}%~{:d}% damage ({:d}~{:d} hits, {:d}% each)'.\
                format(int(min_hit) * int(mult), int(max_hit) * int(mult), min_hit, max_hit, mult)
        return output

    @staticmethod
    def skip():
        return 'Do nothing'

    @staticmethod
    def bind(min_turns, max_turns, target_count=None, target_type='cards'):
        output = []
        if target_count:
            output.append('Bind {:d} {:s}'.format(target_count, target_type))
        else:
            output.append('Bind {:s}'.format(target_type))
        if max_turns is not None and min_turns != max_turns:
            output.append('{:d}~{:d} turns'.format(min_turns, max_turns))
        else:
            output.append('{:d} turns'.format(min_turns))
        return ' for '.join(output)

    @staticmethod
    def orb_change(orb_from, orb_to):
        output = 'Change '
        if type(orb_from) == list:
            output += ', '.join(orb_from)
        else:
            output += orb_from
        output += ' to '
        if type(orb_to) == list:
            output += ', '.join(orb_to)
        else:
            output += orb_to
        return output

    @staticmethod
    def blind():
        return 'Blind all orbs on the board'

    @staticmethod
    def blind_sticky_random(turns, min_count, max_count):
        if min_count == 42:
            return 'Blind all orbs for {:d} turns'.format(turns)
        if min_count == max_count:
            return 'Blind random {:d} orbs for {:d} turns'.format(min_count, turns)
        else:
            return 'Blind random {:d}~{:d} orbs for {:d} turns'.format(min_count, max_count, turns)

    @staticmethod
    def blind_sticky_fixed(turns):
        return 'Blind orbs in specific positions for {:d} turns'.format(turns)

    @staticmethod
    def dispel():
        return 'Voids player buff effects'

    @staticmethod
    def recover(amount, target='enemy'):
        return '{:s} recover {:d}% HP'.format(target, amount).capitalize()

    @staticmethod
    def enrage(mult, turns):
        output = ['Increase damage to {:d}%'.format(mult)]
        if turns == 0:
            output.append('attack')
        else:
            output.append('{:d} turns'.format(turns))
        return ' for the next '.join(output)

    @staticmethod
    def status_shield(turns):
        return 'Voids status ailments for {:d} turns'.format(turns)

    @staticmethod
    def debuff(d_type, amount, unit, turns):
        return '{:s} {:.0f}{:s} for {:d} turns'.format(d_type, amount, unit, turns).capitalize()

    @staticmethod
    def end_battle():
        return 'Reduce self HP to 0'

    @staticmethod
    def change_attribute(attributes):
        if len(attributes) == 1:
            return 'Change own attribute to ' + attributes[0]
        else:
            return 'Change own attribute to random one of ' + ', '.join(attributes)

    @staticmethod
    def gravity(percent):
        return 'Player -{:d}% HP'.format(percent)

    @staticmethod
    def absorb(source, turns):
        return 'Absorb {:s} damage for {:d} turns'.format(source, turns)

    @staticmethod
    def skyfall(orbs, chance, turns):
        return '{:s} skyfall +{:d}% for {:d} turns'.format(', '.join(orbs), chance, turns)

    @staticmethod
    def skyfall_lock(orbs, chance, turns):
        return '{:d}% locked {:s} skyfall for {:d} turns'.format(chance, ', '.join(orbs), turns)

    @staticmethod
    def void(threshold, turns):
        return 'Void damage>{:d} for {:d} turns'.format(threshold, turns)

    @staticmethod
    def damage_reduction(source, percent=None, turns=None):
        if percent is None:
            return 'Immune to damage from {:s} for {:d} turns'.format(source, turns)
        else:
            if turns:
                return 'Reduce damage from {:s} by {:d}% for {:d} turns'.format(source, percent, turns)
            else:
                return 'Reduce damage from {:s} by {:d}%'.format(source, percent)

    @staticmethod
    def resolve(percent):
        return 'Survive attacks with 1 HP when HP>{:d}%'.format(percent)

    @staticmethod
    def leadswap(turns):
        return 'Leader changes to random sub for {:d} turns'.format(turns)

    @staticmethod
    def row_col_spawn(position_type, positions, attributes):
        return 'Change {:s} {:s} to {:s} orbs'.format(
            ', '.join([ordinal(x) for x in positions]), position_type, ', '.join(attributes))

    @staticmethod
    def board_change(attributes):
        return 'Change all orbs to {:s}'.format(', '.join(attributes))

    @staticmethod
    def random_orb_spawn(count, attributes):
        if count == 42:
            return Describe.board_change(attributes)
        else:
            return 'Spawn random {:d} {:s} orbs'.format(count, ', '.join(attributes))

    @staticmethod
    def fixed_orb_spawn(attributes):
        return 'Spawn {:s} orbs in the specified positions'.format(', '.join(attributes))

    @staticmethod
    def skill_delay(turns):
        return 'Delay active skills by {:d} turns'.format(turns)

    @staticmethod
    def orb_lock(count, attributes):
        if count == 42:
            return 'Lock all {:s} orbs'.format(', '.join(attributes))
        else:
            return 'Lock {:d} random {:s} orbs'.format(count, ', '.join(attributes))

    @staticmethod
    def orb_seal(turns, position_type, positions):
        return 'Seal {:s} {:s} for {:d} turns'.format(', '.join([ordinal(x) for x in positions]), position_type, turns)

    @staticmethod
    def fixed_start():
        return 'Fix orb movement starting point to random position on the board'

    @staticmethod
    def cloud(turns, width, height, x, y):
        if width == 6 and height == 1:
            shape = 'Row of'
        elif width == 1 and height == 5:
            shape = 'Column of'
        else:
            shape = '{:d}x{:d}'.format(width, height)
        pos = []
        if x is not None and shape != 'Row of':
            pos.append('{:s} row'.format(ordinal(x)))
        if y is not None and shape != 'Column of':
            pos.append('{:s} column'.format(ordinal(y)))
        if len(pos) == 0:
            pos.append('random location')
        return '{:s} cloud appear for {:d} turns at {:s}'.format(shape, turns, ', '.join(pos))

    @staticmethod
    def turn_change(turn_counter, threshold=None):
        if threshold:
            return 'Enemy turn counter change to {:d} when HP<{:d}%'.format(turn_counter, threshold)
        else:
            return 'Enemy turn counter change to {:d}'.format(turn_counter)

    @staticmethod
    def attribute_block(turns, attributes):
        return 'Unable to {:s} orbs for {:d} turns'.format(', '.join(attributes), turns)

    @staticmethod
    def spinners(turns, speed, position):
        if position == 'random':
            return 'Random orbs change every {:.1f}s for {:d} turns'.format(speed / 100, turns)
        else:
            return 'Specific orbs change every {:.1f}s for {:d} turns'.format(speed / 100, turns)

    @staticmethod
    def max_hp_change(turns, max_hp, change_type):
        if change_type == 'fixed':
            return 'Change player HP to {:d} for {:d} turns'.format(max_hp, turns)
        else:
            return 'Change player HP to {:d}% for {:d} turns'.format(max_hp, turns)


# Condition subclass

class ESCondition(pad_util.JsonDictEncodable):
    def __init__(self, ai, rnd, params_arr, description=None):
        self.ai = ai
        self.rnd = rnd
        self.hp_threshold = None if params_arr[11] is None else params_arr[11]
        self.one_time = params_arr[13]
        self.description = description if description else \
            Describe.condition(max(ai, rnd), self.hp_threshold, self.one_time is not None)


# Action
class ESAction(pad_util.JsonDictEncodable):
    def __init__(self, skill, effect, description):
        self.CATEGORY = 'ACTION'
        self.enemy_skill_id = es_id(skill)
        self.type = es_type(skill)
        self.name = name(skill)
        self.effect = effect
        self.description = description
        if ai(skill) is None or rnd(skill) is None:
            self.condition = None
        else:
            self.condition = ESCondition(ai(skill), rnd(skill), params(skill))


class ESEffect(ESAction):
    def __init__(self, skill):
        super(ESEffect, self).__init__(
            skill,
            effect='status_effect',
            description='Not an attack'
        )


class ESInactivity(ESEffect):
    def __init__(self, skill):
        super(ESInactivity, self).__init__(skill)
        self.effect = 'skip_turn'
        self.description = Describe.skip()


class ESDeathCry(ESEffect):
    def __init__(self, skill):
        super(ESDeathCry, self).__init__(skill)
        if self.condition:
            self.condition.description = 'On death'
        self.message = params(skill)[0]


class ESAttack(ESAction):
    def __init__(self, skill):
        super(ESAttack, self).__init__(
            skill,
            effect='attack',
            description='An Attack'
        )


class ESAttackSinglehit(ESAttack):
    def __init__(self, skill, multiplier=100):
        super(ESAttackSinglehit, self).__init__(skill)
        self.effect = 'attack_single'
        self.multiplier = multiplier
        self.description = Describe.attack(self.multiplier)


class ESAttackMultihit(ESAttack):
    def __init__(self, skill):
        super(ESAttackMultihit, self).__init__(skill)
        self.min_hit = params(skill)[1]
        self.max_hit = params(skill)[2]
        self.multiplier = params(skill)[3]
        self.effect = 'attack_multi'
        self.description = Describe.attack(self.multiplier, self.min_hit, self.max_hit)


class ESAttackPreemptive(ESAttackSinglehit):
    def __init__(self, skill):
        super(ESAttackPreemptive, self).__init__(skill, multiplier=params(skill)[2])
        self.effect = 'attack_preemptive'


class ESBind(ESEffect):
    def __init__(self, skill, target_count=None, target_type_description='cards'):
        super(ESBind, self).__init__(skill)
        self.min_turns = params(skill)[2]
        self.max_turns = params(skill)[3]
        if target_count:
            self.target_count = target_count
        self.effect = 'bind'
        self.description = Describe.bind(
            self.min_turns, self.max_turns, target_count, target_type_description)


class ESBindAttack(ESBind):
    def __init__(self, skill):
        super(ESBindAttack, self).__init__(skill, target_count=params(
            skill)[5], target_type_description='cards')
        self.effect = 'bind_attack'
        self.attack_multiplier = params(skill)[1]
        self.description += ' & ' + Describe.attack(self.attack_multiplier)


class ESBindRandom(ESBind):
    def __init__(self, skill, target_type_description='random cards'):
        super(ESBindRandom, self).__init__(
            skill,
            target_count=params(skill)[1],
            target_type_description=target_type_description)


class ESBindLeader(ESBind):
    def __init__(self, skill):
        targets = bind_leader_bitmap(params(skill)[1])
        super(ESBindLeader, self).__init__(
            skill,
            target_count=len(targets),
            target_type_description=targets
        )


class ESBindRandomSub(ESBindRandom):
    def __init__(self, skill):
        super(ESBindRandomSub, self).__init__(skill, target_type_description='random subs')


class ESBindAttribute(ESBind):
    def __init__(self, skill):
        super(ESBindAttribute, self).__init__(
            skill,
            target_count=None,
            target_type_description='{:s} cards'.format(ATTRIBUTE_MAP[params(skill)[1]]))
        self.target_attribute = ATTRIBUTE_MAP[params(skill)[1]]


class ESBindTyping(ESBind):
    def __init__(self, skill):
        super(ESBindTyping, self).__init__(
            skill,
            target_count=None,
            target_type_description='{:s} cards'.format(TYPING_MAP[params(skill)[1]]))
        self.target_typing = TYPING_MAP[params(skill)[1]]


class ESBindSkill(ESBind):
    def __init__(self, skill):
        super(ESBindSkill, self).__init__(
            skill,
            target_count=None,
            target_type_description='active skills')
        self.effect = 'skill_bind'


class ESBindAwoken(ESEffect):
    def __init__(self, skill):
        super(ESBindAwoken, self).__init__(skill)
        self.turns = params(skill)[1]
        self.description = Describe.bind(self.turns, None, None, 'awoken skills')
        self.effect = 'awoken_bind'


class ESOrbChange(ESEffect):
    def __init__(self, skill, orb_from, orb_to):
        super(ESOrbChange, self).__init__(skill)
        self.orb_from = orb_from
        self.orb_to = orb_to
        self.effect = 'orb_change'
        self.description = Describe.orb_change(self.orb_from, self.orb_to)


class ESOrbChangeSingle(ESOrbChange):
    def __init__(self, skill):
        super(ESOrbChangeSingle, self).\
            __init__(skill, ATTRIBUTE_MAP[params(skill)[1]], ATTRIBUTE_MAP[params(skill)[2]])


class ESOrbChangeAttackBits(ESOrbChange):
    def __init__(self, skill):
        super(ESOrbChangeAttackBits, self).__init__(
            skill,
            orb_from=attribute_bitmap(params(skill)[2]),
            orb_to=attribute_bitmap(params(skill)[3])
        )
        self.attack_multiplier = params(skill)[1]
        if self.attack_multiplier:
            self.description += ' & ' + Describe.attack(self.attack_multiplier)


class ESJammerChangeSingle(ESOrbChange):
    def __init__(self, skill):
        super(ESJammerChangeSingle, self).\
            __init__(skill, ATTRIBUTE_MAP[params(skill)[1]], ATTRIBUTE_MAP[6])


class ESJammerChangeRandom(ESOrbChange):
    def __init__(self, skill):
        self.random_count = int(params(skill)[1])
        super(ESJammerChangeRandom, self).\
            __init__(skill, 'Random {:d}'.format(self.random_count), ATTRIBUTE_MAP[6])


class ESPoisonChangeSingle(ESOrbChange):
    def __init__(self, skill):
        super(ESPoisonChangeSingle, self).__init__(
            skill, ATTRIBUTE_MAP[params(skill)[1]], ATTRIBUTE_MAP[7])


class ESPoisonChangeRandom(ESOrbChange):
    def __init__(self, skill):
        self.random_count = int(params(skill)[1])
        super(ESPoisonChangeRandom, self).\
            __init__(skill, 'Random {:d}'.format(self.random_count), ATTRIBUTE_MAP[7])


class ESMortalPoisonChangeRandom(ESOrbChange):
    def __init__(self, skill):
        self.random_count = int(params(skill)[1])
        super(ESMortalPoisonChangeRandom, self).\
            __init__(skill, 'Random {:d}'.format(self.random_count), ATTRIBUTE_MAP[8])


class ESOrbChangeAttack(ESOrbChange):
    def __init__(self, skill, orb_from=None, orb_to=None):
        super(ESOrbChangeAttack, self).__init__(
            skill,
            orb_from=ATTRIBUTE_MAP[params(skill)[2]] if orb_from is None else orb_from,
            orb_to=ATTRIBUTE_MAP[params(skill)[3]] if orb_to is None else orb_to
        )
        self.attack_multiplier = params(skill)[1]
        self.effect = 'orb_change_attack'
        self.description += ' & ' + Describe.attack(self.attack_multiplier)


class ESPoisonChangeRandomAttack(ESOrbChangeAttack):
    def __init__(self, skill):
        self.random_count = int(params(skill)[2])
        super(ESPoisonChangeRandomAttack, self).__init__(
            skill, orb_from='Random {:d}'.format(self.random_count), orb_to=ATTRIBUTE_MAP[7])


class ESBlind(ESEffect):
    def __init__(self, skill):
        super(ESBlind, self).__init__(skill)
        self.description = Describe.blind()
        self.effect = 'blind'


class ESBlindAttack(ESBlind):
    def __init__(self, skill):
        super(ESBlindAttack, self).__init__(skill)
        self.attack_multiplier = params(skill)[1]
        self.description += ' & ' + Describe.attack(self.attack_multiplier)
        self.effect = 'blind_attack'


class ESBlindSticky(ESEffect):
    def __init__(self, skill):
        super(ESBlindSticky, self).__init__(skill)
        self.turns = params(skill)[1]
        self.effect = 'blind_sticky'


class ESBlindStickyRandom(ESBlindSticky):
    def __init__(self, skill):
        super(ESBlindStickyRandom, self).__init__(skill)
        self.min_count = params(skill)[2]
        self.max_count = params(skill)[3]
        self.target = 'random'
        self.effect = 'blind_sticky'
        self.description = Describe.blind_sticky_random(self.turns, self.min_count, self.max_count)


class ESBlindStickyFixed(ESBlindSticky):
    def __init__(self, skill):
        super(ESBlindStickyFixed, self).__init__(skill)
        self.position_str, self.position_rows, self.position_cols = positions_2d_bitmap(params(skill)[
                                                                                        2:7])
        self.description = Describe.blind_sticky_fixed(self.turns)


class ESDispel(ESEffect):
    def __init__(self, skill):
        super(ESDispel, self).__init__(skill)
        self.description = Describe.dispel()
        self.effect = 'dispel'


class ESStatusShield(ESEffect):
    def __init__(self, skill):
        super(ESStatusShield, self).__init__(skill)
        self.turns = params(skill)[1]
        self.description = Describe.status_shield(self.turns)


class ESRecover(ESEffect):
    def __init__(self,  skill, target):
        super(ESRecover, self).__init__(skill)
        self.amount = params(skill)[1]
        self.target = target
        self.effect = 'recover'
        self.description = Describe.recover(self.amount, self.target)


class ESRecoverEnemy(ESRecover):
    def __init__(self,  skill):
        super(ESRecoverEnemy, self).__init__(skill, target='enemy')


class ESRecoverEnemyAlly(ESRecover):
    def __init__(self,  skill):
        super(ESRecoverEnemyAlly, self).__init__(skill, target='enemy ally')
        if self.condition:
            self.condition.description = 'When enemy ally is killed'


class ESRecoverPlayer(ESRecover):
    def __init__(self, skill):
        super(ESRecoverPlayer, self).__init__(skill, target='player')


class ESEnrage(ESEffect):
    def __init__(self, skill, multiplier, turns):
        super(ESEnrage, self).__init__(skill)
        self.multiplier = multiplier
        self.turns = turns
        self.effect = 'enrage'
        self.description = Describe.enrage(self.multiplier, self.turns)


class ESStorePower(ESEnrage):
    def __init__(self, skill):
        super(ESStorePower, self).__init__(
            skill,
            multiplier=100 + params(skill)[1],
            turns=0
        )


class ESAttackUp(ESEnrage):
    def __init__(self, skill):
        if params(skill)[3] is None:
            super(ESAttackUp, self).__init__(
                skill,
                multiplier=params(skill)[2],
                turns=params(skill)[1]
            )
        else:
            super(ESAttackUp, self).__init__(
                skill,
                multiplier=params(skill)[3],
                turns=params(skill)[2]
            )


class ESDebuff(ESEffect):
    def __init__(self, skill, debuff_type, amount, unit):
        super(ESDebuff, self).__init__(skill)
        self.turns = params(skill)[1]
        self.type = debuff_type
        self.amount = amount
        self.unit = unit
        self.effect = 'debuff'
        self.description = Describe.debuff(self.type, self.amount, self.unit, self.turns)


class ESDebuffMovetime(ESDebuff):
    def __init__(self, skill):
        if params(skill)[2] is not None:
            super(ESDebuffMovetime, self).__init__(
                skill,
                debuff_type='movetime',
                amount=-params(skill)[2] / 10,
                unit='s'
            )
        elif params(skill)[3] is not None:
            super(ESDebuffMovetime, self).__init__(
                skill,
                debuff_type='movetime',
                amount=params(skill)[3],
                unit='%'
            )


class ESDebuffRCV(ESDebuff):
    def __init__(self, skill):
        super(ESDebuffRCV, self).__init__(
            skill,
            debuff_type='RCV',
            amount=params(skill)[2],
            unit='%'
        )


class ESEndBattle(ESEffect):
    def __init__(self, skill):
        super(ESEndBattle, self).__init__(skill)
        self.description = Describe.end_battle()
        self.effect = 'end_battle'
        if self.condition:
            self.condition.chance = 100


class ESChangeAttribute(ESEffect):
    def __init__(self, skill):
        super(ESChangeAttribute, self).__init__(skill)
        self.attributes = list(OrderedDict.fromkeys([ATTRIBUTE_MAP[x] for x in params(skill)[1:6]]))
        self.effect = 'change_attribute'
        self.description = Describe.change_attribute(self.attributes)


class ESGravity(ESEffect):
    def __init__(self, skill):
        super(ESGravity, self).__init__(skill)
        self.percent = params(skill)[1]
        self.effect = 'gravity'
        self.description = Describe.gravity(self.percent)


class ESAbsorbAttribute(ESEffect):
    def __init__(self, skill):
        super(ESAbsorbAttribute, self).__init__(skill)
        self.turns = params(skill)[1]
        self.attributes = attribute_bitmap(params(skill)[3])
        self.description = Describe.absorb(', '.join(self.attributes), self.turns)


class ESAbsorbCombo(ESEffect):
    def __init__(self, skill):
        super(ESAbsorbCombo, self).__init__(skill)
        self.turns = params(skill)[1]
        self.combo_threshold = params(skill)[3]
        self.description = Describe.absorb(
            'combo <= {:,d}'.format(self.combo_threshold), self.turns)


class ESAbsorbThreshold(ESEffect):
    def __init__(self, skill):
        super(ESAbsorbThreshold, self).__init__(skill)
        self.turns = params(skill)[1]
        self.absorb_threshold = params(skill)[2]
        self.description = Describe.absorb('damage >= {}'.format(self.absorb_threshold), self.turns)


class ESVoidShield(ESEffect):
    def __init__(self, skill):
        super(ESVoidShield, self).__init__(skill)
        self.turns = params(skill)[1]
        # mysterious params[2], always 1055 except for no.2485 Hakumen no Mono who has 31
        self.void_threshold = params(skill)[3]
        self.description = Describe.void(self.void_threshold, self.turns)


class ESDamageShield(ESEffect):
    def __init__(self, skill):
        super(ESDamageShield, self).__init__(skill)
        self.turns = params(skill)[1]
        self.shield_percent = params(skill)[2]
        self.description = Describe.damage_reduction('all sources', self.shield_percent, self.turns)


class ESInvulnerableOn(ESEffect):
    def __init__(self, skill):
        super(ESInvulnerableOn, self).__init__(skill)
        self.turns = params(skill)[1]
        self.effect = 'invulnerability_on'
        self.description = Describe.damage_reduction('all sources', turns=self.turns)


class ESInvulnerableOff(ESEffect):
    def __init__(self, skill):
        super(ESInvulnerableOff, self).__init__(skill)
        self.effect = 'invulnerability_off'
        self.description = 'Remove damage immunity effect'


class ESSkyfall(ESEffect):
    def __init__(self, skill):
        super(ESSkyfall, self).__init__(skill)
        self.turns = params(skill)[2]
        self.attributes = attribute_bitmap(params(skill)[1])
        self.chance = params(skill)[4]
        self.effect = 'skyfall_increase'
        self.description = Describe.skyfall(self.attributes, self.chance, self.turns)


class ESSkyfallLocks(ESSkyfall):
    def __init__(self, skill):
        super(ESSkyfallLocks, self).__init__(skill)
        self.effect = 'skyfall_lock'
        self.description = Describe.skyfall_lock(self.attributes, self.chance, self.turns)


class ESLeaderSwap(ESEffect):
    def __init__(self, skill):
        super(ESLeaderSwap, self).__init__(skill)
        self.turns = self.turns = params(skill)[1]
        self.description = Describe.leadswap(self.turns)


class ESFixedOrbSpawn(ESEffect):
    def __init__(self, skill, position_type, positions, attributes):
        super(ESFixedOrbSpawn, self).__init__(skill)
        self.position_type = position_type
        self.positions = positions
        self.attributes = attributes
        self.effect = 'row_col_spawn'


class ESRowColSpawn(ESFixedOrbSpawn):
    def __init__(self, skill, position_type):
        super(ESRowColSpawn, self).__init__(
            skill,
            position_type=position_type,
            positions=position_bitmap(params(skill)[1]),
            attributes=attribute_bitmap(params(skill)[2])
        )
        self.description = Describe.row_col_spawn(
            self.position_type,
            self.positions,
            self.attributes
        )


class ESRowColSpawnMulti(ESFixedOrbSpawn):
    def __init__(self, skill, position_type):
        super(ESRowColSpawnMulti, self).__init__(
            skill,
            position_type=position_type,
            positions=[],
            attributes=[]
        )
        desc_arr = []
        for i in range(1, 6, 2):
            if params(skill)[i] and params(skill)[i + 1]:
                p = position_bitmap(params(skill)[i])
                a = attribute_bitmap(params(skill)[i + 1])
                desc_arr.append(Describe.row_col_spawn(self.position_type, p, a)[7:])
                self.positions += p
                self.attributes += a
        self.description = 'Change ' + ', '.join(desc_arr)
        if params(skill)[7]:
            self.attack_multiplier = params(skill)[7]
            self.description += ' & ' + Describe.attack(self.attack_multiplier)


class ESColumnSpawn(ESRowColSpawn):
    def __init__(self, skill):
        super(ESColumnSpawn, self).__init__(
            skill,
            position_type='column'
        )


class ESColumnSpawnMulti(ESRowColSpawnMulti):
    def __init__(self, skill):
        super(ESColumnSpawnMulti, self).__init__(
            skill,
            position_type='column'
        )


class ESRowSpawn(ESRowColSpawn):
    def __init__(self, skill):
        super(ESRowSpawn, self).__init__(
            skill,
            position_type='row'
        )


class ESRowSpawnMulti(ESRowColSpawnMulti):
    def __init__(self, skill):
        super(ESRowSpawnMulti, self).__init__(
            skill,
            position_type='row'
        )


class ESRandomSpawn(ESEffect):
    def __init__(self, skill):
        super(ESRandomSpawn, self).__init__(skill)
        self.count = params(skill)[1]
        self.attributes = attribute_bitmap(params(skill)[2])
        self.effect = 'random_orb_spawn'
        self.description = Describe.random_orb_spawn(self.count, self.attributes)


class ESBombRandomSpawn(ESEffect):
    def __init__(self, skill):
        super(ESBombRandomSpawn, self).__init__(skill)
        self.count = params(skill)[2]
        self.attack_multiplier = params(skill)[14]
        self.effect = 'random_bomb_spawn'
        self.description = Describe.random_orb_spawn(self.count, ['Bomb'])
        if self.attack_multiplier is not None:
            self.description += ' & ' + Describe.attack(self.attack_multiplier)


class ESBombFixedSpawn(ESEffect):
    def __init__(self, skill):
        super(ESBombFixedSpawn, self).__init__(skill)
        self.count = params(skill)[2]
        self.attack_multiplier = params(skill)[14]
        self.effect = 'fixed_bomb_spawn'
        self.position_str, self.position_rows, self.position_cols = positions_2d_bitmap(params(skill)[
                                                                                        2:7])
        if self.position_rows is not None and len(self.position_rows) == 6 \
                and self.position_cols is not None and len(self.position_cols) == 5:
            self.description = Describe.board_change(['Bomb'])
        self.description = Describe.fixed_orb_spawn(['Bomb'])
        if self.attack_multiplier is not None:
            self.description += ' & ' + Describe.attack(self.attack_multiplier)


class ESBoardChange(ESEffect):
    def __init__(self, skill, attributes=None):
        super(ESBoardChange, self).__init__(skill)
        if attributes:
            self.attributes = attributes
        else:
            self.attributes = attribute_bitmap(params(skill)[1])
        self.effect = 'board_change'


class ESBoardChangeAttackFlat(ESBoardChange):
    def __init__(self, skill):
        super(ESBoardChangeAttackFlat, self).__init__(
            skill,
            [ATTRIBUTE_MAP[x] for x in params(skill)[2:params(skill).index(-1)]]
        )
        self.attack_multiplier = params(skill)[1]
        self.description = Describe.board_change(
            self.attributes) + ' & ' + Describe.attack(self.attack_multiplier)


class ESBoardChangeAttackBits(ESBoardChange):
    def __init__(self, skill):
        super(ESBoardChangeAttackBits, self).__init__(
            skill,
            attribute_bitmap(params(skill)[2])
        )
        self.attack_multiplier = params(skill)[1]
        self.description = Describe.board_change(
            self.attributes) + ' & ' + Describe.attack(self.attack_multiplier)


class SubSkill(pad_util.JsonDictEncodable):
    def __init__(self, enemy_skill_id):
        self.enemy_skill_id = enemy_skill_id
        self.enemy_skill_info = enemy_skill_map[enemy_skill_id]
        self.enemy_ai = None
        self.enemy_rnd = None


class ESSkillSet(ESEffect):
    def __init__(self, skill):
        super(ESSkillSet, self).__init__(skill)
        self.effect = 'skill_set'
        self.description = 'Perform multiple skills'
        self.skill_list = []
        i = 0
        for s in params(skill)[1:11]:
            if s is not None:
                sub_skill = SubSkill(s)
                if es_type(sub_skill) in BEHAVIOR_MAP:
                    behavior = BEHAVIOR_MAP[es_type(sub_skill)](sub_skill)
                    self.skill_list.append(behavior)
                else:
                    self.skill_list.append(EnemySkillUnknown(sub_skill))
            i += 1


class ESSkillSetOnDeath(ESSkillSet):
    def __init__(self, skill):
        super(ESSkillSetOnDeath, self).__init__(skill)
        if self.condition:
            self.condition.description = 'On death'


class ESSkillDelay(ESEffect):
    def __init__(self, skill):
        super(ESSkillDelay, self).__init__(skill)
        self.turns = params(skill)[2]
        self.effect = 'skill_delay'
        self.description = Describe.skill_delay(self.turns)


class ESOrbLock(ESEffect):
    def __init__(self, skill):
        super(ESOrbLock, self).__init__(skill)
        self.count = params(skill)[2]
        self.attributes = attribute_bitmap(params(skill)[1])
        self.effect = 'orb_lock'
        self.description = Describe.orb_lock(self.count, self.attributes)


class ESOrbSeal(ESEffect):
    def __init__(self, skill, position_type, positions):
        super(ESOrbSeal, self).__init__(skill)
        self.turns = params(skill)[2]
        self.position_type = position_type
        self.positions = positions
        self.effect = 'orb_seal'
        self.description = Describe.orb_seal(self.turns, self.position_type, self.positions)


class ESOrbSealColumn(ESOrbSeal):
    def __init__(self, skill):
        super(ESOrbSealColumn, self).__init__(
            skill,
            position_type='column',
            positions=position_bitmap(params(skill)[1])
        )


class ESOrbSealRow(ESOrbSeal):
    def __init__(self, skill):
        super(ESOrbSealRow, self).__init__(
            skill,
            position_type='row',
            positions=position_bitmap(params(skill)[1])
        )


class ESCloud(ESEffect):
    def __init__(self, skill):
        super(ESCloud, self).__init__(skill)
        self.turns = params(skill)[1]
        self.cloud_width = params(skill)[2]
        self.cloud_height = params(skill)[3]
        self.origin_y = params(skill)[4]
        self.origin_x = params(skill)[5]
        self.attack_multiplier = params(skill)[14]
        self.description = Describe.cloud(
            self.turns, self.cloud_width, self.cloud_height, self.origin_x, self.origin_y)
        if self.attack_multiplier is not None:
            self.description += ' & ' + Describe.attack(self.attack_multiplier)


class ESFixedStart(ESEffect):
    def __init__(self, skill):
        super(ESFixedStart, self).__init__(skill)
        self.effect = 'fixed_start'
        self.description = Describe.fixed_start()


class ESAttributeBlock(ESEffect):
    def __init__(self, skill):
        super(ESAttributeBlock, self).__init__(skill)
        self.turns = params(skill)[1]
        self.attributes = attribute_bitmap(params(skill)[2])
        self.effect = 'attribute_block'
        self.description = Describe.attribute_block(self.turns, self.attributes)


class ESSpinners(ESEffect):
    def __init__(self, skill, position_type):
        super(ESSpinners, self).__init__(skill)
        self.turns = params(skill)[1]
        self.speed = params(skill)[2]
        self.position_type = position_type
        self.effect = 'orb_spinners'
        self.description = Describe.spinners(self.turns, self.speed, self.position_type)


class ESSpinnersRandom(ESSpinners):
    def __init__(self, skill):
        super(ESSpinnersRandom, self).__init__(
            skill,
            position_type='random'
        )


class ESSpinnersFixed(ESSpinners):
    def __init__(self, skill):
        super(ESSpinnersFixed, self).__init__(
            skill,
            position_type='fixed'
        )
        self.position_str, self.position_rows, self.position_cols = positions_2d_bitmap(params(skill)[
                                                                                        3:8])


class ESMaxHPChange(ESEffect):
    def __init__(self, skill):
        super(ESMaxHPChange, self).__init__(skill)
        self.turns = params(skill)[3]
        self.effect = 'max_hp_change'
        if params(skill)[2] is not None:
            self.max_hp = params(skill)[2]
            self.hp_change_type = 'percent'
        else:
            self.max_hp = params(skill)[3]
            self.hp_change_type = 'flat'
        self.description = Describe.max_hp_change(self.turns, self.max_hp, self.hp_change_type)


class ESFixedTarget(ESEffect):
    def __init__(self, skill):
        super(ESFixedTarget, self).__init__(skill)
        # self.target = params(skill)[1]
        self.effect = 'fixed_target'
        self.description = 'Forces attacks to hit this enemy'


# Passive
class ESPassive(pad_util.JsonDictEncodable):
    def __init__(self, skill):
        self.CATEGORY = 'PASSIVE'
        self.enemy_skill_id = es_id(skill)
        self.type = es_type(skill)
        self.name = name(skill)
        self.effect = 'passive_effect'
        self.description = 'A passive trait'


class ESAttributeResist(ESPassive):
    def __init__(self, skill):
        super(ESAttributeResist, self).__init__(skill)
        self.attributes = attribute_bitmap(params(skill)[1])
        self.shield_percent = params(skill)[2]
        self.effect = 'resist_attribute'
        self.description = Describe.damage_reduction(
            ', '.join(self.attributes), percent=self.shield_percent)


class ESResolve(ESPassive):
    def __init__(self, skill):
        super(ESResolve, self).__init__(skill)
        self.hp_threshold = params(skill)[1]
        self.effect = 'resolve'
        self.description = Describe.resolve(self.hp_threshold)


class ESTurnChangePassive(ESPassive):
    def __init__(self, skill):
        super(ESTurnChangePassive, self).__init__(skill)
        self.hp_threshold = params(skill)[1]
        self.turn_counter = params(skill)[2]
        self.effect = 'turn_change_passive'
        self.description = Describe.turn_change(self.turn_counter, self.hp_threshold)


class ESTypeResist(ESPassive):
    def __init__(self, skill):
        super(ESTypeResist, self).__init__(skill)
        self.types = typing_bitmap(params(skill)[1])
        self.shield_percent = params(skill)[2]
        self.effect = 'resist_type'
        self.description = Describe.damage_reduction(
            ', '.join(self.types), percent=self.shield_percent)


class ESTurnChangeActive(ESEffect):
    def __init__(self, skill):
        super(ESTurnChangeActive, self).__init__(skill)
        self.effect = 'turn_change_active'
        self.turn_counter = params(skill)[2]
        self.description = Describe.turn_change(self.turn_counter)


# Logic
class ESLogic(pad_util.JsonDictEncodable):
    def __init__(self, skill, effect=None):
        self.CATEGORY = 'LOGIC'
        self.enemy_skill_id = es_id(skill)
        self.effect = effect
        self.type = es_type(skill)


class ESNone(ESLogic):
    def __init__(self, skill):
        super(ESNone, self).__init__(skill)


class ESFlagOperation(ESLogic):
    FLAG_OPERATION_MAP = {
        22: 'SET',
        24: 'UNSET',
        44: 'OR',
        45: 'XOR'
    }

    def __init__(self, skill):
        super(ESFlagOperation, self).__init__(skill, effect='flag_operation')
        self.flag = ai(skill)
        self.flag_bin = bin(self.flag)
        self.operation = self.FLAG_OPERATION_MAP[es_type(skill)]


class ESSetCounter(ESLogic):
    COUNTER_SET_MAP = {
        25: '=',
        26: '+',
        27: '-'
    }

    def __init__(self, skill):
        super(ESSetCounter, self).__init__(skill, effect='set_counter')
        self.counter = ai(skill) if es_type(skill) == 25 else 1
        self.set = self.COUNTER_SET_MAP[es_type(skill)]


class ESSetCounterIf(ESLogic):
    def __init__(self, skill):
        super(ESSetCounterIf, self).__init__(skill, effect='set_counter_if')
        self.effect = 'set_counter_if'
        self.counter_is = ai(skill)
        self.counter = rnd(skill)


class ESBranch(ESLogic):
    def __init__(self, skill, branch_condition):
        self.branch_condition = branch_condition
        self.branch_value = ai(skill)
        self.target_round = rnd(skill)
        super(ESBranch, self).__init__(skill, effect='branch')


class ESBranchFlag(ESBranch):
    def __init__(self, skill):
        super(ESBranchFlag, self).__init__(
            skill,
            branch_condition='flag'
        )
        self.branch_value_bin = bin(ai(skill))


class ESBranchHP(ESBranch):
    HP_COMPARE_MAP = {
        28: '<',
        29: '>'
    }

    def __init__(self, skill):
        self.compare = self.HP_COMPARE_MAP[es_type(skill)]
        super(ESBranchHP, self).__init__(
            skill,
            branch_condition='hp'
        )


class ESBranchCounter(ESBranch):
    COUNTER_COMPARE_MAP = {
        30: '<',
        31: '=',
        32: '>'
    }

    def __init__(self, skill):
        self.compare = self.COUNTER_COMPARE_MAP[es_type(skill)]
        super(ESBranchCounter, self).__init__(
            skill,
            branch_condition='counter'
        )


class ESBranchLevel(ESBranch):
    LEVEL_COMPARE_MAP = {
        33: '<',
        34: '=',
        35: '>'
    }

    def __init__(self, skill):
        self.compare = self.LEVEL_COMPARE_MAP[es_type(skill)]
        super(ESBranchLevel, self).__init__(
            skill,
            branch_condition='level'
        )


class ESEndPath(ESLogic):
    def __init__(self, skill):
        super(ESEndPath, self).__init__(skill, effect='end_turn')


class ESCountdown(ESLogic):
    def __init__(self, skill):
        # decrement counter at the end of every turn, including this turn
        super(ESCountdown, self).__init__(skill, effect='start_countdown')


class ESPreemptive(ESLogic):
    def __init__(self, skill):
        super(ESPreemptive, self).__init__(skill, effect='preemptive')
        self.level = params(skill)[1]


class ESBranchCard(ESBranch):
    def __init__(self, skill):
        super(ESBranchCard, self).__init__(skill, branch_condition='player_cards')
        self.branch_value = [x for x in params(skill) if x is not None]
        self.compare = 'HAS'


class ESBranchCombo(ESBranch):
    def __init__(self, skill):
        super(ESBranchCombo, self).__init__(skill, branch_condition='combo')
        self.compare = '>'


class ESBranchRemainingEnemies(ESBranch):
    def __init__(self, skill):
        super(ESBranchRemainingEnemies, self).__init__(skill, branch_condition='remaining enemies')
        self.compare = '='


# Unknown
class EnemySkillUnknown(pad_util.JsonDictEncodable):
    def __init__(self, skill):
        self.es_id = es_id(skill)
        self.name = name(skill)
        self.type = es_type(skill)


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
    17: ESAttackUp,
    18: ESAttackUp,
    19: ESAttackUp,
    20: ESStatusShield,
    39: ESDebuffMovetime,
    40: ESEndBattle,
    46: ESChangeAttribute,
    47: ESAttackPreemptive,
    48: ESOrbChangeAttack,
    50: ESGravity,
    52: ESRecoverEnemyAlly,
    53: ESAbsorbAttribute,
    54: ESBindLeader,
    55: ESRecoverPlayer,
    56: ESPoisonChangeSingle,
    60: ESPoisonChangeRandom,
    61: ESMortalPoisonChangeRandom,
    62: ESBlindAttack,
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
    76: ESColumnSpawn,
    77: ESColumnSpawnMulti,
    78: ESRowSpawn,
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
    # 93: FF animation (???)
    94: ESOrbLock,
    95: ESSkillSetOnDeath,
    96: ESSkyfallLocks,
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
}

PASSIVE_MAP = {
    72: ESAttributeResist,
    73: ESResolve,
    106: ESTurnChangePassive,
    118: ESTypeResist,
}


def extract_behavior(enemy_skillset):
    if enemy_skill_map is None:
        return None
    behavior = []
    for skill in enemy_skillset:
        skill_type = es_type(skill)
        if skill_type in BEHAVIOR_MAP:
            behavior.append(BEHAVIOR_MAP[skill_type](skill))
        elif skill_type in PASSIVE_MAP:
            behavior.append(PASSIVE_MAP[skill_type](skill))
        else:  # skills not parsed
            behavior.append(EnemySkillUnknown(skill))
    return behavior


def reformat_json(card_data):
    reformatted = []
    for enemy in card_data:
        behavior = {}
        passives = {}
        unknown = {}
        # Sequence of enemy skill is important for logic
        for idx, skill in enumerate(enemy.enemy_skill_refs):
            idx += 1
            # print(str(enemy['monster_no']) + ':' + str(es_type(skill)))
            if es_type(skill) in BEHAVIOR_MAP:
                behavior[idx] = BEHAVIOR_MAP[es_type(skill)](skill)
            elif es_type(skill) in PASSIVE_MAP:
                passives[idx] = PASSIVE_MAP[es_type(skill)](skill)
            else:  # skills not parsed
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
