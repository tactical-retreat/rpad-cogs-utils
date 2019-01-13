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
        if chance > 0 and not one_time:
            output.append('{:d}% chance'.format(chance))
        if hp:
            output.append('when <{:d}% HP'.format(hp))
        if one_time:
            output.append('(one-time)')
        return ' '.join(output)

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
    def orbchange(orb_from, orb_to):
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
        return 'Voids Skill effects'

    @staticmethod
    def recover(min_amount, max_amount, target='Enemy'):
        if max_amount is not None and min_amount != max_amount:
            return '{:s} recover {:d}%~{:d}% HP'.format(target, min_amount, max_amount)
        else:
            return '{:s} recover {:d}% HP'.format(target, min_amount)

    @staticmethod
    def enrage(mult, turns):
        output = ['Increase damage to {:d}%'.format(mult)]
        if turns == 0:
            output.append('attack')
        else:
            output.append('{:d} turns'.format(turns))
        return ' for the next '.join(output)


# Action
class EnemySkillDescription(pad_util.JsonDictEncodable):
    def __init__(self, es_id, name, condition, effect, description):
        self.enemy_skill_id = es_id
        self.name = name
        self.condition = condition
        self.effect = effect
        self.description = description


class ESNone(EnemySkillDescription):
    def __init__(self, es_id, name, ref, params, effect='none'):
        super(ESNone, self).__init__(es_id, name, None, effect, description='NONE')


class ESInactivity(EnemySkillDescription):
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


class ESEffect(EnemySkillDescription):
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


class ESAttack(EnemySkillDescription):
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
        self.description = Describe.orbchange(ATTRIBUTE_MAP[params[1]][1], ATTRIBUTE_MAP[params[2]][1])


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
        super(ESDispel, self).__init__(es_id, name, ref, params)
        self.description = Describe.dispel()
        self.condition = self.condition.replace('(one-time)', 'when player buff exists')


class ESRecover(ESEffect):
    def __init__(self,  es_id, name, ref, params, target):
        super(ESRecover, self).__init__(es_id, name, ref, params, effect='recover')
        self.min_amount = params[1]
        self.max_amount = params[2]
        self.target = target
        self.description = Describe.recover(self.min_amount, self.max_amount, self.target)


class ESRecoverEnemy(ESRecover):
    def __init__(self,  es_id, name, ref, params):
        super(ESRecover, self).__init__(es_id, name, ref, params, 'Enemy')


class ESEnrage(ESEffect):
    def __init__(self, es_id, name, ref, params, multiplier, turns, effect='enrage'):
        super(ESEnrage, self).__init__(
            es_id,
            name,
            ref, params, effect=effect
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


# Logic

# Unknown


class EnemySkillUnknown(pad_util.JsonDictEncodable):
    def __init__(self, es_id, name):
        self.es_id = es_id
        self.name = name


LOGIC_MAP = {
    0: ESNone
}


ACTION_MAP = {
    0: ESNone,
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
    16: ESInactivity
}


def reformat_json(enemy_data):
    reformatted = []
    for enemy in enemy_data:
        logics = {}
        actions = {}
        unknown = {}
        for idx, skill in enumerate(enemy['skill_set']):
            print(enemy['monster_no'])
            t = skill['enemy_skill_info']['type']
            if t in LOGIC_MAP:
                logics[idx] = LOGIC_MAP[t](
                    skill['enemy_skill_id'],
                    skill['enemy_skill_info']['name'],
                    skill['enemy_skill_ref'],
                    skill['enemy_skill_info']['params'])
            elif t in ACTION_MAP:
                actions[idx] = ACTION_MAP[t](
                    skill['enemy_skill_id'],
                    skill['enemy_skill_info']['name'],
                    skill['enemy_skill_ref'],
                    skill['enemy_skill_info']['params'])
            else:  # skills not parsed
                unknown[idx] = EnemySkillUnknown(skill['enemy_skill_id'], skill['enemy_skill_info']['name'])
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