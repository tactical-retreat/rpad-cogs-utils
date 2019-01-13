import json

from ..common import pad_util

ai = 'ai'
rnd = 'rnd'

ATTRIBUTE_MAP = {
    '-1': (0, 'random'),
    None: (1, 'Fire'),
    '1': (2, 'Water'),
    '2': (3, 'Wood'),
    '3': (4, 'Light'),
    '4': (5, 'Dark'),
    '5': (6, 'Heal'),
    '6': (6, 'Jammer'),
    '7': (6, 'Poison')
}

TYPING_MAP = {
    '4': (1, 'Dragon'),
    '5': (6, 'God'),
    '7': (10, 'Devil')
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
                output += ' ({:s} hits, {:s}% each)'.format(min_hit, mult)
        else:
            output += 'Deal {:d}%~{:d}% damage ({:s}~{:s} hits, {:s}% each)'.\
                format(int(min_hit) * int(mult), int(max_hit) * int(mult), min_hit, max_hit, mult)
        return output

    @staticmethod
    def bind(min_turns, max_turns, target_count=None, target_type='cards'):
        output = []
        if target_count:
            output.append('Bind {:s} {:s}'.format(target_count, target_type))
        else:
            output.append('Bind {:s}'.format(target_type))
        if min_turns != max_turns:
            output.append('{:s}~{:s} turns'.format(min_turns, max_turns))
        else:
            output.append('{:s} turns'.format(min_turns))
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
    def enrage(mult, turns):
        output = ['Increase damage to {:d}%'.format(mult)]
        if turns == 0:
            output.append('attack')
        else:
            output.append('{:s} turns'.format(turns))
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
    def __init__(self, es_id, name, ref, params, effect='none', description='NONE'):
        super(ESNone, self).__init__(es_id, name, None, effect, description)


class ESInactivity(EnemySkillDescription):
    def __init__(self, es_id, name, ref, params, effect='skip_turn', description='Do nothing'):
        self.chance = ref[rnd]
        self.hp_threshold = None if params[11] is None else int(params[11])
        self.one_time = ref[ai] == 100
        super(ESInactivity, self).__init__(
            es_id, name,
            Describe.condition(self.chance, self.hp_threshold, self.one_time),
            effect,
            description
        )


class ESEffect(EnemySkillDescription):
    def __init__(self, es_id, name, ref, params, effect='status_effect', description='Not an attack'):
        self.chance = ref[rnd]
        self.hp_threshold = None if params[11] is None else int(params[11])
        self.one_time = ref[ai] == 100
        super(ESEffect, self).__init__(
            es_id, name,
            Describe.condition(self.chance, self.hp_threshold, self.one_time),
            effect,
            description
        )


class ESAttack(EnemySkillDescription):
    def __init__(self, es_id, name, ref, params, effect='attack', description='An Attack'):
        self.chance = ref[ai] if int(ref[ai]) > 0 else ref[rnd]
        self.hp_threshold = None if params[11] is None else int(params[11])
        super(ESAttack, self).__init__(
            es_id, name,
            condition=Describe.condition(self.chance, self.hp_threshold),
            effect=effect,
            description=description
        )


class ESAttackMultihit(ESAttack):
    def __init__(self, es_id, name, ref, params):
        super(ESAttackMultihit, self).__init__(
            es_id, name, ref, params,
            effect='multihit_attack',
            description=Describe.attack(params[1], params[2], params[3])
        )


class ESBind(ESEffect):
    def __init__(self, es_id, name, ref, params, effect='Bind', description='Bind targets'):
        self.min_turns = params[2]
        self.max_turns = params[3]
        super(ESBind, self).__init__(
            es_id, name, ref, params,
            effect=effect,
            description=description
        )


class ESRandomBind(ESBind):

    def __init__(self, es_id, name, ref, params):
        super(ESRandomBind, self).__init__(
            es_id, name, ref, params, effect='random_bind'
        )
        self.target_type = 'random cards'
        self.description = Describe.bind(self.min_turns, self.max_turns, params[1], self.target_type)


class ESAttributeBind(ESBind):
    def __init__(self, es_id, name, ref, params):
        super(ESAttributeBind, self).__init__(
            es_id, name, ref, params, effect='attribute_bind'
        )
        self.target_type = '{:s} cards'.format(ATTRIBUTE_MAP[params[1]][1])
        self.description = Describe.bind(self.min_turns, self.max_turns, None, self.target_type)


class ESTypingBind(ESBind):
    def __init__(self, es_id, name, ref, params):
        super(ESTypingBind, self).__init__(
            es_id, name, ref, params, effect='attribute_bind'
        )
        self.target_type = TYPING_MAP[params[1]][0]
        self.description = Describe.bind(self.min_turns, self.max_turns, None, '{:s} cards'.format(TYPING_MAP[params[1]][1]))


class ESOrbChange(ESEffect):
    def __init__(self, es_id, name, ref, params):
        super(ESOrbChange, self).__init__(es_id, name, ref, params)
        self.orb_from = ATTRIBUTE_MAP[params[1]][0]
        self.orb_to = ATTRIBUTE_MAP[params[2]][0]
        self.description = Describe.orbchange(ATTRIBUTE_MAP[params[1]][1], ATTRIBUTE_MAP[params[2]][1])


class ESBlind(ESEffect):
    def __init__(self, es_id, name, ref, params):
        super(ESBlind, self).__init__(es_id, name, ref, params)
        self.description = 'Unable to see Orbs'


class ESDispel(ESEffect):
    def __init__(self, es_id, name, ref, params):
        super(ESDispel, self).__init__(es_id, name, ref, params)
        self.description = 'Voids Skill effects'
        self.condition = self.condition.replace('(one-time)', 'when player buff exists')


class ESEnrage(ESEffect):
    def __init__(self, es_id, name, ref, params, effect='enrage', description='Boost attack power'):
        super(ESEnrage, self).__init__(
            es_id,
            name,
            ref, params, effect=effect, description=description
        )
        self.multiplier = int(params[2])
        self.turns = int(params[1])


class ESStorePower(ESEnrage):
    def __init__(self, es_id, name, ref, params):
        super(ESStorePower, self).__init__(
            es_id,
            name,
            ref, params,
            effect='store_power',
            description=Describe.enrage(100 + int(params[1]), 0)
        )
        self.multiplier = 100 + int(params[1])
        self.turns = 0

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
    4: ESOrbChange,
    5: ESBlind,
    6: ESDispel,
    8: ESStorePower,
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
            else: # unparsed skills
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