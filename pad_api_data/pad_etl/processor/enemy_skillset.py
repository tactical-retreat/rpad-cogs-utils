import json
from collections import OrderedDict
from ..common import pad_util

ai = 'ai'
rnd = 'rnd'

ATTRIBUTE_MAP = {
    -1: (0, 'Random'),
    None: (1, 'Fire'),
    1: (2, 'Water'),
    2: (3, 'Wood'),
    3: (4, 'Light'),
    4: (5, 'Dark'),
    5: (6, 'Heal'),
    6: (7, 'Jammer'),
    7: (8, 'Poison'),
    8: (9, 'Mortal Poison')
}

TYPING_MAP = {
    4: (1, 'Dragon'),
    5: (6, 'God'),
    7: (10, 'Devil')
}


def es_id(skill):
    return skill['enemy_skill_id']


def name(skill):
    return skill['enemy_skill_info']['name']


def params(skill):
    return skill['enemy_skill_info']['params']


def ref(skill):
    return skill['enemy_skill_ref']


def es_type(skill):
    return skill['enemy_skill_info']['type']


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
            output.append('(one-time)')
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
        return 'Unable to see Orbs'

    @staticmethod
    def dispel():
        return 'Voids player buff effects'

    @staticmethod
    def recover(min_amount, max_amount, target='enemy'):
        if max_amount is not None and min_amount != max_amount:
            return '{:s} recover {:d}%~{:d}% HP'.format(target, min_amount, max_amount).capitalize()
        else:
            return '{:s} recover {:d}% HP'.format(target, min_amount).capitalize()

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


# Action
class ESAction(pad_util.JsonDictEncodable):
    def __init__(self, skill, condition, effect, description):
        self.enemy_skill_id = es_id(skill)
        self.name = name(skill)
        self.condition = condition
        self.effect = effect
        self.description = description


class ESEffect(ESAction):
    def __init__(self, skill):
        self.chance = ref(skill)[rnd]
        self.hp_threshold = None if params(skill)[11] is None else int(params(skill)[11])
        self.one_time = ref(skill)[ai] == 100
        super(ESEffect, self).__init__(
            skill,
            Describe.condition(self.chance, self.hp_threshold, self.one_time),
            effect='status_effect',
            description='Not an attack'
        )


class ESInactivity(ESEffect):
    def __init__(self, skill):
        super(ESInactivity, self).__init__(skill)
        self.effect = 'skip_turn'
        self.description = Describe.skip()


class ESAttack(ESAction):
    def __init__(self, skill):
        self.chance = ref(skill)[ai] if int(ref(skill)[ai]) > 0 else ref(skill)[rnd]
        self.hp_threshold = None if params(skill)[11] is None else int(params(skill)[11])
        super(ESAttack, self).__init__(
            skill,
            condition=Describe.condition(self.chance, self.hp_threshold),
            effect='attack',
            description='An Attack'
        )


class ESAttackSinglehit(ESAttack):
    def __init__(self, skill, multiplier):
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
        self.effect = 'bind'
        self.description = Describe.bind(self.min_turns, self.max_turns, target_count, target_type_description)


class ESRandomBind(ESBind):
    def __init__(self, skill):
        super(ESRandomBind, self).__init__(
            skill,
            target_count=params(skill)[1],
            target_type_description='random cards')


class ESAttributeBind(ESBind):
    def __init__(self, skill):
        super(ESAttributeBind, self).__init__(
            skill,
            target_count=None,
            target_type_description='{:s} cards'.format(ATTRIBUTE_MAP[params(skill)[1]][1]))
        self.target_attribute = ATTRIBUTE_MAP[params(skill)[1]][0]


class ESTypingBind(ESBind):
    def __init__(self, skill):
        super(ESTypingBind, self).__init__(
            skill,
            target_count=None,
            target_type_description='{:s} cards'.format(TYPING_MAP[params(skill)[1]][1]))
        self.target_typing = TYPING_MAP[params(skill)[1]][0]


class ESSkillBind(ESBind):
    def __init__(self, skill):
        super(ESSkillBind, self).__init__(
            skill,
            target_count=None,
            target_type_description='active skill')


class ESOrbChange(ESEffect):
    def __init__(self, skill, orb_from, orb_to):
        super(ESOrbChange, self).__init__(skill)
        self.orb_from = orb_from[0]
        self.orb_to = orb_to[0]
        self.effect = 'orb_change'
        self.description = Describe.orb_change(orb_from[1], orb_to[1])


class ESOrbChangeSingle(ESOrbChange):
    def __init__(self, skill):
        super(ESOrbChangeSingle, self).\
            __init__(skill, ATTRIBUTE_MAP[params(skill)[1]], ATTRIBUTE_MAP[params(skill)[2]])


class ESJammerChangeSingle(ESOrbChange):
    def __init__(self, skill):
        super(ESJammerChangeSingle, self).\
            __init__(skill, ATTRIBUTE_MAP[params(skill)[1]], ATTRIBUTE_MAP[6])


class ESJammerChangeRandom(ESOrbChange):
    def __init__(self, skill):
        self.random_count = int(params(skill)[1])
        super(ESJammerChangeRandom, self).\
            __init__(skill, (0, 'Random {:d}'.format(self.random_count)), ATTRIBUTE_MAP[6])


class ESOrbChangeAttack(ESAttackSinglehit):
    def __init__(self, skill):
        super(ESOrbChangeAttack, self).__init__(
            skill,
            multiplier=params(skill)[1]
        )
        self.orb_from = ATTRIBUTE_MAP[params(skill)[2]][0]
        self.orb_to = ATTRIBUTE_MAP[params(skill)[3]][0]
        self.effect = 'orb_change_attack'
        self.description = Describe.orb_change(ATTRIBUTE_MAP[params(skill)[2]][1], ATTRIBUTE_MAP[params(skill)[3]][1])\
                           + ' & ' + Describe.attack(self.multiplier)


class ESBlind(ESEffect):
    def __init__(self, skill):
        super(ESBlind, self).__init__(skill)
        self.description = Describe.blind()


class ESDispel(ESEffect):
    def __init__(self, skill):
        ref(skill)[ai] = 0
        super(ESDispel, self).__init__(skill)
        self.description = Describe.dispel()


class ESStatusShield(ESEffect):
    def __init__(self, skill):
        super(ESStatusShield, self).__init__(skill)
        self.turns = params(skill)[1]
        self.description = Describe.status_shield(self.turns)


class ESRecover(ESEffect):
    def __init__(self,  skill, target):
        super(ESRecover, self).__init__(skill)
        self.min_amount = params(skill)[1]
        self.max_amount = params(skill)[2]
        self.target = target
        self.effect = 'recover'
        self.description = Describe.recover(self.min_amount, self.max_amount, self.target)


class ESRecoverEnemy(ESRecover):
    def __init__(self,  skill):
        super(ESRecoverEnemy, self).__init__(skill, target='enemy')


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
                amount=-params(skill)[2]/10,
                unit='s'
            )
        elif params(skill)[3] is not None:
            super(ESDebuffMovetime, self).__init__(
                skill,
                debuff_type='movetime',
                amount=params(skill)[3],
                unit='%'
            )


class ESEndBattle(ESEffect):
    def __init__(self, skill):
        super(ESEndBattle, self).__init__(skill)
        self.description = Describe.end_battle()
        self.effect = 'end_battle'
        self.condition = Describe.condition(100, self.hp_threshold, False)


class ESChangeAttribute(ESEffect):
    def __init__(self, skill):
        super(ESChangeAttribute, self).__init__(skill)
        atts = list(OrderedDict.fromkeys([ATTRIBUTE_MAP[x] for x in params(skill)[1:6]]))
        self.attributes = [x[0] for x in atts]
        self.effect = 'change_attribute'
        self.description = Describe.change_attribute([x[1] for x in atts])


class ESGravity(ESEffect):
    def __init__(self, skill):
        super(ESGravity, self).__init__(skill)
        self.percent = params(skill)[1]
        self.effect = 'gravity'
        self.description = Describe.gravity(self.percent)


# Logic
class ESLogic(pad_util.JsonDictEncodable):
    def __init__(self, skill, effect=None):
        self.enemy_skill_id = es_id(skill)
        self.effect = effect


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
        self.flag = ref(skill)[ai]
        self.flag_bin = bin(ref(skill)[ai])
        self.operation = self.FLAG_OPERATION_MAP[es_type(skill)]


class ESSetCounter(ESLogic):
    COUNTER_SET_MAP = {
        25: '=',
        26: '+',
        27: '-'
    }

    def __init__(self, skill):
        super(ESSetCounter, self).__init__(skill, effect='set_counter')
        self.counter = ref(skill)[ai] if es_type(skill) == 25 else 1
        self.set = self.COUNTER_SET_MAP[es_type(skill)]


class ESSetCounterIf(ESLogic):
    def __init__(self, skill):
        super(ESSetCounterIf, self).__init__(skill, effect='set_counter_if')
        self.effect = 'set_counter_if'
        self.counter_is = ref(skill)[ai]
        self.counter = ref(skill)[rnd]


class ESBranch(ESLogic):
    def __init__(self, skill, branch_condition):
        self.branch_condition = branch_condition
        self.branch_value = ref(skill)[ai]
        self.target_round = ref(skill)[rnd]
        super(ESBranch, self).__init__(skill, effect='branch')


class ESBranchFlag(ESBranch):
    def __init__(self, skill):
        super(ESBranchFlag, self).__init__(
            skill,
            branch_condition='flag'
        )
        self.branch_value_bin = bin(ref(skill)[ai])


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


# Unknown
class EnemySkillUnknown(pad_util.JsonDictEncodable):
    def __init__(self, skill):
        self.es_id = es_id(skill)
        self.name = name(skill)
        self.type = es_type(skill)


LOGIC_MAP = {
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
    49: ESPreemptive
}


ACTION_MAP = {
    1: ESRandomBind,
    2: ESAttributeBind,
    3: ESTypingBind,
    4: ESOrbChangeSingle,
    5: ESBlind,
    6: ESDispel,
    7: ESRecoverEnemy,
    8: ESStorePower,
    # type 9 skills are unused, there's only 3 and they seem to buff defense
    12: ESJammerChangeSingle,
    13: ESJammerChangeRandom,
    14: ESSkillBind,
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
    50: ESGravity
}


def reformat_json(enemy_data):
    reformatted = []
    for enemy in enemy_data:
        logics = {}
        actions = {}
        unknown = {}
        for idx, skill in enumerate(enemy['skill_set']):
            idx += 1
            # print(str(enemy['monster_no']) + ':' + str(es_type(skill)))
            if es_type(skill) in LOGIC_MAP:
                logics[idx] = LOGIC_MAP[es_type(skill)](skill)
            elif es_type(skill) in ACTION_MAP:
                actions[idx] = ACTION_MAP[es_type(skill)](skill)
            else:  # skills not parsed
                unknown[idx] = EnemySkillUnknown(skill)
        reformatted.append({
            'MONSTER_NO': enemy['monster_no'],
            'LOGIC': logics,
            'ACTION': actions,
            'UNKNOWN': unknown
        })

    return reformatted


def reformat(in_file_name, out_file_name):
    print('-- Parsing Enemies --\n')
    with open(in_file_name) as f:
        enemy_data = json.load(f)
    print('Merged skill set json loaded\n')
    reformatted = reformat_json(enemy_data)

    print('Converted {active} enemies\n'.format(active=len(reformatted)))

    with open(out_file_name, 'w') as f:
        json.dump(reformatted, f, indent=4, sort_keys=True, default=lambda x: x.__dict__)
    print('Result saved\n')
    print('-- End Enemies --\n')
