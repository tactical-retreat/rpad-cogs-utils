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


# generic actions
def condition(chance, hp=None, one_time=False):
    cond = '' if chance == 0 or chance == 100 else '{:d}% chance'.format(chance)
    cond += '' if len(cond) == 0 else ' '
    cond += '' if hp is None else 'when <{:s}% HP'.format(hp)
    cond += '' if len(cond) == 0 else ', '
    cond += '' if not one_time else 'one-time use'
    return cond if len(cond) > 0 else None


def attack(min_hit, max_hit, mult):
    out = 'Deal '
    if min_hit == max_hit:
        out += '{:d}% damage'.format(int(min_hit) * int(mult))
        if int(min_hit) > 1:
            out += '({:s} hits, {:s}% each)'.format(min_hit, mult)
    else:
        out += '{:d}%~{:d}% damage ({:s}~{:s} hits, {:s}% each)'.\
            format(int(min_hit) * int(mult), int(max_hit) * int(mult), min_hit, max_hit, mult)
    return {'min_hit': min_hit, 'max_hit': max_hit, 'multiplier': mult, 'description': out}


def binds(min_turns, max_turns, target_count=None, target_type='cards'):
    if target_count:
        out = 'Bind {:s} {:s} for '.format(target_count, target_type)
    else:
        out = 'Bind {:s} for '.format(target_type)
    if min_turns != max_turns:
        out += '{:s}~{:s} turns'.format(min_turns, max_turns)
    else:
        out += '{:s} turns'.format(min_turns)
    return {'min_turns': min_turns, 'max_turns': max_turns,
            'target_count': target_count, 'target_type': target_type,
            'description': out}


def enrage(mult, turns):
    out = 'Increase damage to {:s}% for the next '.format(mult)
    if turns == 0:
        out += 'attack'
    else:
        out += '{:s} turns'.format(turns)
    return {'multiplier': mult, 'turns': turns, 'description': out}


# skill types
def none(args):
    return {'condition': None,
            'effect': None,
            'description': '<NONE>'}


def random_binds(args):
    ref = args['enemy_skill_ref']
    params = args['enemy_skill_info']['params']
    return {'condition': condition(ref[rnd], params[11], ref[ai] == 100),
            'effect': 'random_bind',
            **binds(params[2], params[3], params[1], 'random cards')}


def attribute_binds(args):
    ref = args['enemy_skill_ref']
    params = args['enemy_skill_info']['params']
    return {'condition': condition(ref[rnd], params[11], ref[ai] == 100),
            'effect': 'attribute_binds',
            **binds(params[2], params[3], None, '{:s} cards'.format(ATTRIBUTE_MAP[params[1]][1]))}


def store_power(args):
    ref = args['enemy_skill_ref']
    params = args['enemy_skill_info']['params']
    return {'condition': condition(ref[rnd], params[11], ref[ai] == 100),
            'effect': 'store_power',
            **enrage(str(100 + int(params[1])), 0)}


def named_attack(args):
    ref = args['enemy_skill_ref']
    params = args['enemy_skill_info']['params']
    return {'condition': condition(ref[ai], params[11]),
            'effect': 'named_attack',
            **attack(params[1], params[2], params[3])}


def skip_turn(args):
    return {'condition': condition(args['enemy_skill_ref'][rnd], None, args['enemy_skill_ref'][ai] == 100),
            'effect': 'skip_turn',
            'description': 'Skip turn'}


LOGIC_MAP = {
    0: none,
}


ACTION_MAP = {
    1: random_binds,
    2: attribute_binds,
    8: store_power,
    15: named_attack,
    16: skip_turn
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
                logics[idx] = LOGIC_MAP[t](skill)
            elif t in ACTION_MAP:
                actions[idx] = ACTION_MAP[t](skill)
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
