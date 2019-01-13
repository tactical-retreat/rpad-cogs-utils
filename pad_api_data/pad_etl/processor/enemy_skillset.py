import json

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
    7: (8, 'Poison')
}

TYPING_MAP = {
    4: (1, 'Dragon'),
    5: (6, 'God'),
    7: (10, 'Devil')
}


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
    def attack(min_hit, max_hit, mult):
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


# Action
class ESAction(pad_util.JsonDictEncodable):
    def __init__(self, es_id, name, condition, effect, description):
        self.enemy_skill_id = es_id
        self.name = name
        self.condition = condition
        self.effect = effect
        self.description = description


class ESInactivity(ESAction):
    def __init__(self, es_id, name, ref, params, effect='skip_turn'):
        self.chance = ref[rnd]
        self.hp_threshold = None if params[11] is None else int(params[11])
        self.one_time = ref[ai] == 100
        super(ESInactivity, self).__init__(
            es_id, name,
            Describe.condition(self.chance, self.hp_threshold, self.one_time),
            effect,
            description='Do nothing'
        )


class ESEffect(ESAction):
    def __init__(self, es_id, name, ref, params, effect='status_effect'):
        self.chance = ref[rnd]
        self.hp_threshold = None if params[11] is None else int(params[11])
        self.one_time = ref[ai] == 100
        super(ESEffect, self).__init__(
            es_id, name,
            Describe.condition(self.chance, self.hp_threshold, self.one_time),
            effect,
            description='Not an attack'
        )


class ESAttack(ESAction):
    def __init__(self, es_id, name, ref, params, effect='attack'):
        self.chance = ref[ai] if int(ref[ai]) > 0 else ref[rnd]
        self.hp_threshold = None if params[11] is None else int(params[11])
        super(ESAttack, self).__init__(
            es_id, name,
            condition=Describe.condition(self.chance, self.hp_threshold),
            effect=effect,
            description='An Attack'
        )


class ESAttackMultihit(ESAttack):
    def __init__(self, es_id, name, ref, params):
        super(ESAttackMultihit, self).__init__(
            es_id, name, ref, params
        )
        self.min_hit = params[1]
        self.max_hit = params[2]
        self.multiplier = params[3]
        self.description = Describe.attack(self.min_hit, self.max_hit, self.multiplier)


class ESBind(ESEffect):
    def __init__(self, es_id, name, ref, params, target_count=None, target_type_description='cards'):
        super(ESBind, self).__init__(
            es_id, name, ref, params,
            effect='Bind'
        )
        self.min_turns = params[2]
        self.max_turns = params[3]
        self.description = Describe.bind(self.min_turns, self.max_turns, target_count, target_type_description)


class ESRandomBind(ESBind):
    def __init__(self, es_id, name, ref, params):
        super(ESRandomBind, self).__init__(
            es_id, name, ref, params,
            target_count=params[1],
            target_type_description='random cards')


class ESAttributeBind(ESBind):
    def __init__(self, es_id, name, ref, params):
        super(ESAttributeBind, self).__init__(
            es_id, name, ref, params,
            target_count=None,
            target_type_description='{:s} cards'.format(ATTRIBUTE_MAP[params[1]][1]))
        self.target_attribute = ATTRIBUTE_MAP[params[1]][0]


class ESTypingBind(ESBind):
    def __init__(self, es_id, name, ref, params):
        super(ESTypingBind, self).__init__(
            es_id, name, ref, params,
            target_count=None,
            target_type_description='{:s} cards'.format(TYPING_MAP[params[1]][1]))
        self.target_typing = TYPING_MAP[params[1]][0]


class ESSkillBind(ESBind):
    def __init__(self, es_id, name, ref, params):
        super(ESSkillBind, self).__init__(
            es_id, name, ref, params,
            target_count=None,
            target_type_description='active skill')


class ESOrbChange(ESEffect):
    def __init__(self, es_id, name, ref, params, orb_from, orb_to):
        super(ESOrbChange, self).__init__(es_id, name, ref, params, effect='orb_change')
        self.orb_from = orb_from[0]
        self.orb_to = orb_to[0]
        self.description = Describe.orb_change(ATTRIBUTE_MAP[params[1]][1], ATTRIBUTE_MAP[params[2]][1])


class ESOrbChangeSingle(ESOrbChange):
    def __init__(self, es_id, name, ref, params):
        super(ESOrbChangeSingle, self).\
            __init__(es_id, name, ref, params, ATTRIBUTE_MAP[params[1]], ATTRIBUTE_MAP[params[2]])


class ESJammerChangeSingle(ESOrbChange):
    def __init__(self, es_id, name, ref, params):
        super(ESJammerChangeSingle, self).\
            __init__(es_id, name, ref, params, ATTRIBUTE_MAP[params[1]], ATTRIBUTE_MAP[6])


class ESJammerChangeRandom(ESOrbChange):
    def __init__(self, es_id, name, ref, params):
        self.random_count = int(params[1])
        super(ESJammerChangeRandom, self).\
            __init__(es_id, name, ref, params, (0, 'Random {:d}'.format(self.random_count)), ATTRIBUTE_MAP[6])


class ESBlind(ESEffect):
    def __init__(self, es_id, name, ref, params):
        super(ESBlind, self).__init__(es_id, name, ref, params)
        self.description = Describe.blind()


class ESDispel(ESEffect):
    def __init__(self, es_id, name, ref, params):
        ref[ai] = 0
        super(ESDispel, self).__init__(es_id, name, ref, params)
        self.description = Describe.dispel()


class ESStatusShield(ESEffect):
    def __init__(self, es_id, name, ref, params):
        super(ESStatusShield, self).__init__(es_id, name, ref, params)
        self.turns = params[1]
        self.description = Describe.status_shield(self.turns)


class ESRecover(ESEffect):
    def __init__(self,  es_id, name, ref, params, target):
        super(ESRecover, self).__init__(es_id, name, ref, params, effect='recover')
        self.min_amount = params[1]
        self.max_amount = params[2]
        self.target = target
        self.description = Describe.recover(self.min_amount, self.max_amount, self.target)


class ESRecoverEnemy(ESRecover):
    def __init__(self,  es_id, name, ref, params):
        super(ESRecoverEnemy, self).__init__(es_id, name, ref, params, target='enemy')


class ESEnrage(ESEffect):
    def __init__(self, es_id, name, ref, params, multiplier, turns, effect='enrage'):
        super(ESEnrage, self).__init__(
            es_id, name, ref, params,
            effect=effect
        )
        self.multiplier = multiplier
        self.turns = turns
        self.description = Describe.enrage(self.multiplier, self.turns)


class ESStorePower(ESEnrage):
    def __init__(self, es_id, name, ref, params):
        super(ESStorePower, self).__init__(
            es_id, name, ref, params,
            multiplier=100 + params[1],
            turns=0
        )


class ESAttackUp(ESEnrage):
    def __init__(self, es_id, name, ref, params):
        if params[3] is None:
            super(ESAttackUp, self).__init__(
                es_id, name, ref, params,
                multiplier=params[2],
                turns=params[1]
            )
        else:
            super(ESAttackUp, self).__init__(
                es_id, name, ref, params,
                multiplier=params[3],
                turns=params[2]
            )


class ESDebuff(ESEffect):
    def __init__(self, es_id, name, ref, params, debuff_type, amount, unit):
        super(ESDebuff, self).__init__(es_id, name, ref, params, effect='debuff')
        self.turns = params[1]
        self.type = debuff_type
        self.amount = amount
        self.unit = unit
        self.description = Describe.debuff(self.type, self.amount, self.unit, self.turns)


class ESDebuffMovetime(ESDebuff):
    def __init__(self, es_id, name, ref, params):
        if params[2] is not None:
            super(ESDebuffMovetime, self).__init__(
                es_id, name, ref, params,
                debuff_type='movetime',
                amount=-params[2]/10,
                unit='s'
            )
        elif params[3] is not None:
            super(ESDebuffMovetime, self).__init__(
                es_id, name, ref, params,
                debuff_type='movetime',
                amount=params[3],
                unit='%'
            )


class ESEndBattle(ESEffect):
    def __init__(self, es_id, name, ref, params):
        super(ESEndBattle, self).__init__(es_id, name, ref, params, effect='end_battle')
        self.description = 'Reduce self HP to 0'
        self.condition = Describe.condition(100, self.hp_threshold, False)


# Logic
class ESLogic(pad_util.JsonDictEncodable):
    def __init__(self, es_id, effect):
        self.enemy_skill_id = es_id
        self.effect = effect


class ESNone(ESLogic):
    def __init__(self, es_id, ref, type):
        super(ESNone, self).__init__(es_id, None)


class ESSetFlag(ESLogic):
    FLAG_SET_MAP = {
        22: True,
        24: False
    }

    def __init__(self, es_id, ref, es_type):
        super(ESSetFlag, self).__init__(es_id, effect='set_flag')
        # flag is a bitmap
        self.flag = ref[ai] + 1
        self.set = self.FLAG_SET_MAP[es_type]


class ESSetCounter(ESLogic):
    COUNTER_SET_MAP = {
        25: '=',
        26: '+',
        27: '-'
    }

    def __init__(self, es_id, ref, es_type):
        super(ESSetCounter, self).__init__(es_id, effect='set_counter')
        self.counter = ref[ai] if es_type == 25 else 1
        self.set = self.COUNTER_SET_MAP[es_type]


class ESSetCounterIf(ESLogic):
    def __init__(self, es_id, ref, es_type):
        super(ESSetCounterIf, self).__init__(es_id, effect='set_counter_if')
        self.effect = 'set_counter_if'
        self.counter_is = ref[ai]
        self.counter = ref[rnd]


class ESBranch(ESLogic):
    def __init__(self, es_id, ref, branch_condition):
        self.branch_condition = branch_condition
        self.branch_value = ref[ai]
        self.target_round = ref[rnd]
        super(ESBranch, self).__init__(es_id, effect='branch')


class ESBranchFlag(ESBranch):
    def __init__(self, es_id, ref, es_type):
        super(ESBranchFlag, self).__init__(
            es_id, ref,
            branch_condition='flag'
        )


class ESBranchHP(ESBranch):
    HP_COMPARE_MAP = {
        28: '<',
        29: '>'
    }

    def __init__(self, es_id, ref, es_type):
        self.compare = self.HP_COMPARE_MAP[es_type]
        super(ESBranchHP, self).__init__(
            es_id, ref,
            branch_condition='hp'
        )


class ESBranchCounter(ESBranch):
    COUNTER_COMPARE_MAP = {
        30: '<',
        31: '=',
        32: '>'
    }

    def __init__(self, es_id, ref, es_type):
        self.compare = self.COUNTER_COMPARE_MAP[es_type]
        super(ESBranchCounter, self).__init__(
            es_id, ref,
            branch_condition='counter'
        )


class ESBranchLevel(ESBranch):
    LEVEL_COMPARE_MAP = {
        33: '<',
        34: '=',
        35: '>'
    }

    def __init__(self, es_id, ref, es_type):
        self.compare = self.LEVEL_COMPARE_MAP[es_type]
        super(ESBranchLevel, self).__init__(
            es_id, ref,
            branch_condition='level'
        )


class ESEndPath(ESLogic):
    def __init__(self, es_id, ref, es_type):
        super(ESEndPath, self).__init__(es_id, effect='end_turn')


class ESCountdown(ESLogic):
    def __init__(self, es_id, ref, es_type):
        # decrement counter at the end of every turn, including this turn
        super(ESCountdown, self).__init__(es_id, effect='start_countdown')


# Unknown
class EnemySkillUnknown(pad_util.JsonDictEncodable):
    def __init__(self, es_id, name, es_type):
        self.es_id = es_id
        self.name = name
        self.type = es_type


LOGIC_MAP = {
    0: ESNone,
    22: ESSetFlag,
    23: ESBranchFlag,
    24: ESSetFlag,
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
    38: ESSetCounterIf
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
    # type 10 skills don't exist
    # type 11 skills don't exist
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
    40: ESEndBattle
}


def reformat_json(enemy_data):
    reformatted = []
    for enemy in enemy_data:
        logics = {}
        actions = {}
        unknown = {}
        for idx, skill in enumerate(enemy['skill_set']):
            idx += 1
            t = skill['enemy_skill_info']['type']
            if t in LOGIC_MAP:
                logics[idx] = LOGIC_MAP[t](
                    skill['enemy_skill_id'],
                    skill['enemy_skill_ref'],
                    t)
            elif t in ACTION_MAP:
                actions[idx] = ACTION_MAP[t](
                    skill['enemy_skill_id'],
                    skill['enemy_skill_info']['name'],
                    skill['enemy_skill_ref'],
                    skill['enemy_skill_info']['params'])
            else:  # skills not parsed
                unknown[idx] = EnemySkillUnknown(
                    skill['enemy_skill_id'],
                    skill['enemy_skill_info']['name'],
                    t)
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