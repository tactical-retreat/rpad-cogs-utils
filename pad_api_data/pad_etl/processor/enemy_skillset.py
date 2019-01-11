import json
import sys

ai = 'ai'
rnd = 'rnd'

ATTRIBUTE_MAP = {
    None: (1, 'Fire'),
    '1': (2, 'Water'),
    '2': (3, 'Wood'),
    '3': (4, 'Light'),
    '4': (5, 'Dark')
}


# description
def describe_condition(chance, base_chance=0, hp=None, one_time=False):
    output = []
    if chance < 100:
        output.append('{:d}% chance'.format(chance))
    if base_chance > 0:
        output.append('({:d}% base chance)'.format(chance))
    if hp:
        output.append('when <{:s}% HP'.format(hp))
    if one_time:
        output.append('[one-time]')
    return ' '.join(output)


def describe_attack(min_hit, max_hit, mult):
    output = []
    if min_hit == max_hit:
        output.append('Deal {:d}% damage'.format(int(min_hit) * int(mult)))
        if int(min_hit) > 1:
            output.append('({:s} hits, {:s}% each)'.format(min_hit, mult))
    else:
        output.append('Deal {:d}%~{:d}% damage ({:s}~{:s} hits, {:s}% each)'.\
            format(int(min_hit) * int(mult), int(max_hit) * int(mult), min_hit, max_hit, mult))

    return ''.join(output)


def describe_bind(min_turns, max_turns, target_count=None, target_type='cards'):
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


def describe_enrage(mult, turns):
    output = ['Increase damage to {:s}%'.format(mult)]
    if turns == 0:
        output.append('attack')
    else:
        output.append('{:s} turns'.format(turns))
    return ' for the next '.join(output)


# skill types
class EnemySkillDescription:
    def __init__(self, condition, effect, description):
        self.condition = condition
        self.effect = effect
        self.description = description


class ESNone(EnemySkillDescription):
    def __init__(self, ref, params, effect, description):
        super(ESNone, self).__init__(None, effect, description)


class ESInactivity(EnemySkillDescription):
    def __init__(self, ref, params, effect='skip_turn', description='Do nothings'):
        self.chance = ref[rnd]
        self.hp_threshold = params[11]
        self.one_time = ref[ai] == 100
        super(ESInactivity, self).__init__(
            describe_condition(self.chance, 0, self.hp_threshold, self.one_time),
            effect,
            description
        )


class ESStatusEffect(EnemySkillDescription):
    def __init__(self, ref, params, effect='status_effect', description='Not an attack'):
        self.chance = ref[rnd]
        self.hp_threshold = params[11]
        self.one_time = ref[ai] == 100
        super(ESStatusEffect, self).__init__(
            describe_condition(self.chance, 0, self.hp_threshold, self.one_time),
            effect,
            description
        )


class ESAttack(EnemySkillDescription):
    def __init__(self, ref, params, effect='attack', description='An Attack'):
        self.chance = ref[ai]
        self.base_chance = ref[rnd]
        self.hp_threshold = params[11]
        super(ESAttack, self).__init__(
            condition=describe_condition(self.chance, self.base_chance, self.hp_threshold),
            effect=effect,
            description=description
        )


class ESAttackMultihit(ESAttack):
    def __init__(self, ref, params):
        super(ESAttackMultihit, self).__init__(
            ref, params,
            effect='multihit_attack',
            description=describe_attack(params[1], params[2], params[3])
        )


class ESBind(ESStatusEffect):
    def __init__(self, ref, params, effect='Bind', description='Bind targets'):
        self.min_turns = params[2]
        self.max_turns = params[3]
        super(ESBind, self).__init__(
            ref, params,
            effect=effect,
            description=description
        )


class ESRandomBind(ESBind):
    TARGET_TYPE_MAP = {
        1: 'random cards'
    }

    def __init__(self, ref, params, es_type):
        super(ESRandomBind, self).__init__(
            ref, params, effect='random_bind'
        )
        self.target_type = ESRandomBind.TARGET_TYPE_MAP[es_type]
        self.description = describe_bind(self.min_turns, self.max_turns, params[1], self.target_type)


class ESAttributeBind(ESBind):
    def __init__(self, ref, params):
        super(ESAttributeBind, self).__init__(
            ref, params, effect='attribute_bind'
        )
        self.target_type = '{:s} cards'.format(ATTRIBUTE_MAP[params[1]][1])
        self.description = describe_bind(self.min_turns, self.max_turns, None, self.target_type)


class ESEnrage(ESStatusEffect):
    def __init__(self, ref, params, effect='enrage', description='Boost attack power'):
        super(ESEnrage, self).__init__(
            ref, params, effect=effect, description=description
        )
        self.multiplier = int(params[3])
        self.turns = int(params[2])


class ESStorePower(ESEnrage):
    def __init__(self, ref, params):
        super(ESStorePower, self).__init__(
            ref, params,
            effect='store_power',
            description=describe_enrage(100 + int(params[1]), 0)
        )
        self.multiplier = 100 + int(params[1])
        self.turns = 0


LOGIC_MAP = {}


ACTION_MAP = {
    1: ESRandomBind,
    2: ESAttributeBind,
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
                logics[idx] = LOGIC_MAP[t](skill['enemy_skill_ref'], skill['enemy_skill_info']['params'])
            elif t in ACTION_MAP:
                actions[idx] = LOGIC_MAP[t](skill['enemy_skill_ref'], skill['enemy_skill_info']['params'])
            else: # unparsed skills
                unknown[idx] = (skill['enemy_skill_id'], skill['enemy_skill_info']['name'])
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
        json.dump(reformatted, f, sort_keys=True, indent=4)
    print('Result saved\n')
    print('-- End Enemies --\n')


if __name__ == '__main__':
    # python enemy_skillset.py {server}_enemies.json out.json
    reformat(sys.argv[1], sys.argv[2])
    pass
