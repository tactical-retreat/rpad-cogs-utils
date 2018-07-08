#  Created by CandyNinja
#
#  This script reformats the raw json files from pad to a more usable
#  and readable format. The script accepts a dict with a str key for the
#  mode and the tuple value storing the str of the input and output file
#  locations, modes and examples below. There is an optional parameter
#  for pretty printing the json instead of minimizing the file.
#
#  Modes:
#  'skill' for card skills (active and leader)
#  'dungeon' for dungeon data (list of dungeons and floors, not data within them)
#    -- TODO BELOW --
#  'enemy_skill' for dungeon encounter skills
#  'card' for card data (awakenings, stats, types, etc.)
#
#  Examples:
#  reformatter.reformat({'skill': ('download_skill_data.json','reformat/skills.json'),
#                        'card':  ('download_card_data.json', 'reformat/cards.json' )},
#                       pretty=True)
#
#  reformatter.reformat({'dungeon': ('download_dungeon_data.json','reformat/skills.json')})
#
#

from collections import defaultdict
import csv
import json


# Converts the /almost/ csv text from the dungeon and enemy_skill jsons to a list of lists of strings.
# Almost because gungho did some hideous stuff with strings (denoted with a pair of ' characters) like
# putting new lines and even the ' character inside their strings.
def csv_decoder(s: str):
    stop_lead = ''
    result = []
    line = []
    start = 0
    end = 0
    while end < len(s):
        if start == end:
            if s[start] == "'":
                stop_lead = "'"
            else:
                stop_lead = ''
        if stop_lead == "'":
            if s[end:end + 2] == "',":
                line.append(s[start:end + 1])
                end += 2
                start = end
            elif s[end:end + 2] == "'\n":
                line.append(s[start:end + 1])
                result.append(line)
                line = []
                end += 2
                start = end
            else:
                end += 1
        else:
            if s[end] == ',':
                line.append(s[start:end])
                end += 1
                start = end
            elif s[end] == '\n':
                line.append(s[start:end])
                result.append(line)
                line = []
                end += 1
                start = end
            else:
                end += 1

    line.append(s[start:end])
    result.append(line)
    return result

# base code from https://stackoverflow.com/a/8749640/8150086


class defaultlist(list):
    def __init__(self, fx, initial=[]):
        self._fx = fx
        self.extend(initial)

    def _fill(self, index):
        if type(index) == slice:
            if index.step == None or index.step > 0:
                if index.stop == None:
                    return
                while len(self) <= index.stop:
                    self.append(self._fx())
            else:
                if index.start == None:
                    return
                while len(self) <= index.start:
                    self.append(self._fx())
        else:
            while len(self) <= index:
                self.append(self._fx())

    def __setitem__(self, index, value):
        self._fill(index)
        list.__setitem__(self, index, value)

    def __getitem__(self, index):
        self._fill(index)
        if type(index) == slice:
            return defaultlist(self._fx, list.__getitem__(self, index))
        else:
            return list.__getitem__(self, index)


# this is used to name the skill ids and their arguments

def cc(x): return x


def multi(x): return x / 100


def multi2(x): return x / 100 if x != 0 else 1.0


def listify(x): return [x]


def list_con(x): return list(x)


def list_con_pos(x): return [i for i in x if i > 0]


def binary_con(x): return [i for i, v in enumerate(str(bin(x))[:1:-1]) if v == '1']
# def binary_con(x):
#    result = []
#    print(f'start: {x}, {bin(x)}, {str(bin(x))}, {str(bin(x))[:1:-1]}')
#    for i,v in enumerate(str(bin(x))[2::-1]):
#        if v == '1':
#            result.append(i)
#    return result


def list_binary_con(x): return [b for i in x for b in binary_con(i)]


def atk_from_slice(x): return multi(x[2]) if 1 in x[:2] else 1.0


def rcv_from_slice(x): return multi(x[2]) if 2 in x[:2] else 1.0


all_attr = [0, 1, 2, 3, 4]

ATTRIBUTES = {0: 'Fire',
              1: 'Water',
              2: 'Wood',
              3: 'Light',
              4: 'Dark',
              5: 'Heart',
              6: 'Jammer',
              7: 'Poison',
              8: 'Mortal Poison',
              9: 'Bomb'}

TYPES = {0: 'Evo Material',
         1: 'Balanced',
         2: 'Physical',
         3: 'Healer',
         4: 'Dragon',
         5: 'God',
         6: 'Attacker',
         7: 'Devil',
         8: 'Machine',
         12: 'Awaken Material',
         14: 'Enhance Material',
         15: 'Redeemable Material'}


def convert(type_name, arguments):
    def i(x):
        args = {}
        x = defaultlist(int, x)

        for name, t in arguments.items():
            if type(t) == tuple:
                index, funct = t[0], t[1]
                value = x[index]
                args[name] = funct(value)
            else:
                args[name] = t
        return (type_name, args)
    return i


passive_stats_backups = {'for_attr': [], 'for_type': [], 'hp_multiplier': 1.0, 'atk_multiplier': 1.0,
                         'rcv_multiplier': 1.0, 'reduction_attributes': all_attr, 'damage_reduction': 0.0}


def passive_stats_convert(arguments):
    return convert('passive_stats', {k: (arguments[k] if k in arguments else v) for k, v in passive_stats_backups.items()})


threshold_stats_backups = {'for_attr': [], 'for_type': [], 'threshold': False, 'atk_multiplier': 1.0,
                           'rcv_multiplier': 1.0, 'reduction_attributes': all_attr, 'damage_reduction': 0.0}
ABOVE = True
BELOW = False


def threshold_stats_convert(above, arguments):
    if above:
        return convert('above_threshold_stats', {k: (arguments[k] if k in arguments else v) for k, v in threshold_stats_backups.items()})
    else:
        return convert('below_threshold_stats', {k: (arguments[k] if k in arguments else v) for k, v in threshold_stats_backups.items()})


combo_match_backups = {'for_attr': [], 'for_type': [], 'minimum_combos': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                                            'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                                       'maximum_combos': 0, 'reduction_attributes': all_attr}


def combo_match_convert(arguments):
    def f(x):
        _, c = convert('combo_match', {
                       k: (arguments[k] if k in arguments else v) for k, v in combo_match_backups.items()})(x)
        if c['maximum_combos'] == 0:
            c['maximum_combos'] = c['minimum_combos']
        return 'combo_match', c
    return f


attribute_match_backups = {'attributes': [], 'minimum_attributes': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                                      'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                             'maximum_attributes': 0, 'reduction_attributes': all_attr}


def attribute_match_convert(arguments):
    def f(x):
        _, c = convert('attribute_match', {
                       k: (arguments[k] if k in arguments else v) for k, v in attribute_match_backups.items()})(x)
        if c['maximum_attributes'] == 0:
            c['maximum_attributes'] = c['minimum_attributes']
        return 'attribute_match', c
    return f


multi_attribute_match_backups = {'attributes': [], 'minimum_match': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                                       'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                                   'reduction_attributes': all_attr}


def multi_attribute_match_convert(arguments):
    return convert('multi-attribute_match', {k: (arguments[k] if k in arguments else v) for k, v in multi_attribute_match_backups.items()})


mass_match_backups = {'attributes': [], 'minimum_count': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                            'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                        'maximum_count': 0, 'reduction_attributes': all_attr}


def mass_match_convert(arguments):
    def f(x):
        _, c = convert('mass_match', {
                       k: (arguments[k] if k in arguments else v) for k, v in mass_match_backups.items()})(x)
        if c['maximum_count'] == 0:
            c['maximum_count'] = c['minimum_count']
        return 'mass_match', c
    return f


SKILL_TRANSFORM = {
    0: lambda x:
    convert('null_skill', {})(x)
    if defaultlist(int, x)[1] == 0 else
    convert('attack_attr_x_atk', {'attribute': (0, cc),
                                  'multiplier': (1, multi), 'mass_attack': True})(x),
    1: convert('attack_attr_damage', {'attribute': (0, cc), 'damage': (1, cc), 'mass_attack': True}),
    2: convert('attack_x_atk', {'multiplier': (0, multi), 'mass_attack': False}),
    3: convert('damage_shield_buff', {'duration': (0, cc), 'reduction': (1, multi)}),
    4: convert('poison', {'multiplier': (0, multi)}),
    5: convert('change_the_world', {'duration': (0, cc)}),
    6: convert('gravity', {'percentage_hp': (0, multi)}),
    7: convert('heal_active', {'rcv_multiplier_as_hp': (0, multi), 'card_bind': 0, 'hp': 0, 'percentage_max_hp': 0.0, 'awoken_bind': 0, 'team_rcv_multiplier_as_hp': 0.0}),
    8: convert('heal_active', {'hp': (0, cc), 'card_bind': 0, 'rcv_multiplier_as_hp': 0.0, 'percentage_max_hp': 0.0, 'awoken_bind': 0, 'team_rcv_multiplier_as_hp': 0.0}),
    9: convert('single_orb_change', {'from': (0, cc), 'to': (0, cc)}),
    10: convert('board_refresh', {}),
    18: convert('delay', {'turns': (0, cc)}),
    19: convert('defense_reduction', {'duration': (0, cc), 'reduction': (1, multi)}),
    20: convert('double_orb_change', {'from_1': (0, cc), 'to_1': (1, cc), 'from_2': (2, cc), 'to_2': (3, cc)}),
    21: convert('elemental_shield_buff', {'duration': (0, cc), 'attribute': (1, cc), 'reduction': (2, multi)}),
    35: convert('drain_attack', {'atk_multiplier': (0, multi), 'recover_multiplier': (1, multi), 'mass_attack': False}),
    37: convert('attack_attr_x_atk', {'attribute': (0, cc), 'multiplier': (1, multi), 'mass_attack': False}),
    42: convert('element_attack_attr_damage', {'enemy_attribute': (0, cc), 'attack_attribute': (1, cc), 'damage': (2, cc)}),
    50: lambda x:
    convert('rcv_boost', {'duration': (0, cc), 'multiplier': (2, multi)})(x)
    if defaultlist(int, x)[1] == 5 else
    convert('attribute_attack_boost', {'duration': (0, cc),
                                       'attributes': (1, listify), 'multiplier': (2, multi)})(x),
    51: convert('force_mass_attack', {'duration': (0, cc)}),
    52: convert('enhance_orbs', {'orbs': (0, listify)}),
    55: convert('laser', {'damage': (0, cc), 'mass_attack': False}),
    56: convert('laser', {'damage': (0, cc), 'mass_attack': True}),
    58: convert('attack_attr_random_x_atk', {'attribute': (0, cc), 'minimum_multiplier': (1, multi), 'maximum_multiplier': (2, multi), 'mass_attack': True}),
    59: convert('attack_attr_random_x_atk', {'attribute': (0, cc), 'minimum_multiplier': (1, multi), 'maximum_multiplier': (2, multi), 'mass_attack': False}),
    60: convert('counter_attack_buff', {'duration': (0, cc), 'multiplier': (1, multi), 'attribute': (2, cc)}),
    71: convert('board_change', {'attributes': (slice(None), lambda x: [v for v in x if v != -1])}),
    84: convert('suicide_attack_attr_random_x_atk', {'attribute': (0, cc), 'minimum_multiplier': (1, multi), 'maximum_multiplier': (2, multi), 'hp_remaining': (3, multi), 'mass_attack': False}),
    85: convert('suicide_attack_attr_random_x_atk', {'attribute': (0, cc), 'minimum_multiplier': (1, multi), 'maximum_multiplier': (2, multi), 'hp_remaining': (3, multi), 'mass_attack': True}),
    86: convert('suicide_attack_attr_damage', {'attribute': (0, cc), 'damage': (1, multi), 'hp_remaining': (3, multi), 'mass_attack': False}),
    87: convert('suicide_attack_attr_damage', {'attribute': (0, cc), 'damage': (1, multi), 'hp_remaining': (3, multi), 'mass_attack': True}),
    88: convert('type_attack_boost', {'duration': (0, cc), 'types': (1, listify), 'multiplier': (2, multi)}),
    90: convert('attribute_attack_boost', {'duration': (0, cc), 'attributes': (slice(1, 3), list_con), 'multiplier': (2, multi)}),
    91: convert('enhance_orbs', {'orbs': (slice(0, 2), list_con)}),
    92: convert('type_attack_boost', {'duration': (0, cc), 'types': (slice(1, 3), list_con), 'multiplier': (2, multi)}),
    93: convert('leader_swap', {}),
    110: convert('grudge_strike', {'mass_attack': (0, lambda x: x == 0), 'attribute': (1, cc), 'high_multiplier': (2, multi), 'low_multiplier': (3, multi)}),
    115: convert('drain_attack_attr', {'attribute': (0, cc), 'atk_multiplier': (1, multi), 'recover_multiplier': (2, multi), 'mass_attack': False}),
    116: convert('combine_active_skills', {'skill_ids': (slice(None), list_con)}),
    117: convert('heal_active', {'card_bind': (0, cc), 'rcv_multiplier_as_hp': (1, multi), 'hp': (2, cc), 'percentage_max_hp': (3, multi), 'awoken_bind': (4, cc), 'team_rcv_multiplier_as_hp': 0.0}),
    118: convert('random_skill', {'skill_ids': (slice(None), list_con)}),
    126: convert('change_skyfall', {'orbs': (0, binary_con), 'duration': (1, cc), 'percentage': (3, multi)}),
    127: convert('column_change', {'columns': (slice(None), lambda x: [{'index': i if i < 3 else i - 5, 'orbs': binary_con(orbs)} for indices, orbs in zip(x[::2], x[1::2]) for i in binary_con(indices)])}),
    128: convert('row_change', {'rows': (slice(None), lambda x: [{'index': i if i < 4 else i - 6, 'orbs': binary_con(orbs)} for indices, orbs in zip(x[::2], x[1::2]) for i in binary_con(indices)])}),
    132: convert('move_time_buff', {'duration': (0, cc), 'static': (1, lambda x: x / 10), 'percentage': (2, multi)}),
    140: convert('enhance_orbs', {'orbs': (0, binary_con)}),
    141: convert('spawn_orbs', {'amount': (0, cc), 'orbs': (1, binary_con), 'excluding_orbs': (2, binary_con)}),
    142: convert('attribute_change', {'duration': (0, cc), 'attribute': (1, cc)}),
    144: convert('attack_attr_x_team_atk', {'team_attributes': (0, binary_con), 'multiplier': (1, multi), 'mass_attack': (2, lambda x: x == 0), 'attack_attribute': (3, cc), }),
    145: convert('heal_active', {'team_rcv_multiplier_as_hp': (0, multi), 'card_bind': 0, 'rcv_multiplier_as_hp': 0.0, 'hp': 0, 'percentage_max_hp': 0.0, 'awoken_bind': 0}),
    146: convert('haste', {'turns': (0, cc)}),
    152: convert('lock_orbs', {'orbs': (0, binary_con)}),
    153: convert('change_enemies_attribute', {'attribute': (0, cc)}),
    154: convert('random_orb_change', {'from': (0, binary_con), 'to': (1, binary_con)}),
    156: lambda x:
    convert('awakening_heal', {'duration': (0, cc), 'awakenings': (
        slice(1, 4), list_con), 'amount_per': (5, cc)})(x)
    if defaultlist(int, x)[4] == 1 else
    (convert('awakening_attack_boost', {'duration': (0, cc), 'awakenings': (slice(1, 4), list_con), 'amount_per': (5, lambda x: (x - 100) / 100)})(x)
        if defaultlist(int, x)[4] == 2 else
     (convert('awakening_shield', {'duration': (0, cc), 'awakenings': (slice(1, 4), list_con), 'amount_per': (5, multi)})(x)
      if defaultlist(int, x)[4] == 3 else
      (156, x))),
    160: convert('extra_combo', {'duration': (0, cc), 'combos': (1, cc)}),
    161: convert('true_gravity', {'percentage_max_hp': (0, multi)}),
    172: convert('unlock', {}),
    173: convert('absorb_mechanic_void', {'duration': (0, cc), 'attribute_absorb': (1, bool), 'damage_absorb': (1, bool)}),
    179: convert('auto_heal_buff', {'duration': (0, cc), 'percentage_max_hp': (2, multi)}),
    180: convert('enhanced_skyfall_buff', {'duration': (0, cc), 'percentage_increase': (1, multi)}),
    184: convert('no_skyfall_buff', {'duration': (0, cc)}),
    188: convert('multihit_laser', {'damage': (0, cc), 'mass_attack': False}),
    11: passive_stats_convert({'for_attr': (0, listify), 'atk_multiplier': (1, multi)}),
    12: convert('after_attack_on_match', {'multiplier': (0, multi)}),
    13: convert('heal_on_match', {'multiplier': (0, multi)}),
    14: convert('resolve', {'threshold': (0, multi)}),
    15: convert('bonus_move_time', {'time': (0, multi), 'for_attr': [], 'for_type': [], 'hp_multiplier': 1.0, 'atk_multiplier': 1.0, 'rcv_multiplier': 1.0}),
    16: passive_stats_convert({'reduction_attributes': all_attr, 'damage_reduction': (0, multi)}),
    17: passive_stats_convert({'reduction_attributes': (0, listify), 'damage_reduction': (1, multi)}),
    22: passive_stats_convert({'for_type': (0, listify), 'atk_multiplier': (1, multi)}),
    23: passive_stats_convert({'for_type': (0, listify), 'hp_multiplier': (1, multi)}),
    24: passive_stats_convert({'for_type': (0, listify), 'rcv_multiplier': (1, multi)}),
    26: passive_stats_convert({'for_attr': all_attr, 'atk_multiplier': (0, multi)}),
    28: passive_stats_convert({'for_attr': (0, listify), 'atk_multiplier': (1, multi), 'rcv_multiplier': (1, multi)}),
    29: passive_stats_convert({'for_attr': (0, listify), 'hp_multiplier': (1, multi), 'atk_multiplier': (1, multi), 'rcv_multiplier': (1, multi)}),
    30: passive_stats_convert({'for_type': (slice(0, 2), list_con), 'hp_multiplier': (2, multi)}),
    31: passive_stats_convert({'for_type': (slice(0, 2), list_con), 'atk_multiplier': (2, multi)}),
    33: convert('drumming_sound', {}),
    36: passive_stats_convert({'reduction_attributes': (slice(0, 2), list_con), 'damage_reduction': (2, multi)}),
    38: threshold_stats_convert(BELOW, {'for_attr': all_attr, 'threshold': (0, multi), 'damage_reduction': (2, multi)}),
    39: threshold_stats_convert(BELOW, {'for_attr': all_attr, 'threshold': (0, multi), 'atk_multiplier': (slice(1, 4), atk_from_slice), 'rcv_multiplier': (slice(1, 4), rcv_from_slice)}),
    40: passive_stats_convert({'for_attr': (slice(0, 2), list_con), 'atk_multiplier': (2, multi)}),
    41: convert('counter_attack', {'chance': (0, multi), 'multiplier': (1, multi), 'attribute': (2, cc)}),
    43: threshold_stats_convert(ABOVE, {'for_attr': all_attr, 'threshold': (0, multi), 'damage_reduction': (2, multi)}),
    44: threshold_stats_convert(ABOVE, {'for_attr': all_attr, 'threshold': (0, multi), 'atk_multiplier': (slice(1, 4), atk_from_slice), 'rcv_multiplier': (slice(1, 4), rcv_from_slice)}),
    45: passive_stats_convert({'for_attr': (0, listify), 'hp_multiplier': (1, multi), 'atk_multiplier': (1, multi)}),
    46: passive_stats_convert({'for_attr': (slice(0, 2), list_con), 'hp_multiplier': (2, multi)}),
    48: passive_stats_convert({'for_attr': (0, listify), 'hp_multiplier': (1, multi)}),
    49: passive_stats_convert({'for_attr': (0, listify), 'rcv_multiplier': (1, multi)}),
    53: convert('egg_drop_rate', {'multiplier': (0, multi)}),
    54: convert('coin_drop_rate', {'multiplier': (0, multi)}),
    61: attribute_match_convert({'attributes': (0, binary_con), 'minimum_attributes': (1, cc), 'minimum_atk_multiplier': (2, multi), 'minimum_rcv_multiplier': (2, multi), 'bonus_atk_multiplier': (3, multi), 'bonus_rcv_multiplier': (3, multi)}),
    62: passive_stats_convert({'for_type': (0, listify), 'hp_multiplier': (1, multi), 'atk_multiplier': (1, multi)}),
    63: passive_stats_convert({'for_type': (0, listify), 'hp_multiplier': (1, multi), 'rcv_multiplier': (1, multi)}),
    64: passive_stats_convert({'for_type': (0, listify), 'atk_multiplier': (1, multi), 'rcv_multiplier': (1, multi)}),
    65: passive_stats_convert({'for_type': (0, listify), 'hp_multiplier': (1, multi), 'atk_multiplier': (1, multi), 'rcv_multiplier': (1, multi)}),
    66: combo_match_convert({'for_attr': all_attr, 'minimum_combos': (0, cc), 'minimum_atk_multiplier': (1, multi)}),
    67: passive_stats_convert({'for_attr': (0, listify), 'hp_multiplier': (1, multi), 'rcv_multiplier': (1, multi)}),
    69: passive_stats_convert({'for_attr': (0, listify), 'for_type': (1, listify), 'atk_multiplier': (2, multi)}),
    73: passive_stats_convert({'for_attr': (0, listify), 'for_type': (1, listify), 'hp_multiplier': (2, multi), 'atk_multiplier': (2, multi)}),
    75: passive_stats_convert({'for_attr': (0, listify), 'for_type': (1, listify), 'atk_multiplier': (2, multi), 'rcv_multiplier': (2, multi)}),
    76: passive_stats_convert({'for_attr': (0, listify), 'for_type': (1, listify), 'hp_multiplier': (2, multi), 'atk_multiplier': (2, multi), 'rcv_multiplier': (2, multi)}),
    77: passive_stats_convert({'for_type': (slice(0, 2), list_con), 'hp_multiplier': (2, multi), 'atk_multiplier': (2, multi)}),
    79: passive_stats_convert({'for_type': (slice(0, 2), list_con), 'atk_multiplier': (2, multi), 'rcv_multiplier': (2, multi)}),
    94: threshold_stats_convert(BELOW, {'for_attr': (1, listify), 'threshold': (0, multi), 'atk_multiplier': (slice(2, 5), atk_from_slice), 'rcv_multiplier': (slice(2, 5), rcv_from_slice)}),
    95: threshold_stats_convert(BELOW, {'for_type': (1, listify), 'threshold': (0, multi), 'atk_multiplier': (slice(2, 5), atk_from_slice), 'rcv_multiplier': (slice(2, 5), rcv_from_slice)}),
    96: threshold_stats_convert(ABOVE, {'for_attr': (1, listify), 'threshold': (0, multi), 'atk_multiplier': (slice(2, 5), atk_from_slice), 'rcv_multiplier': (slice(2, 5), rcv_from_slice)}),
    97: threshold_stats_convert(ABOVE, {'for_type': (1, listify), 'threshold': (0, multi), 'atk_multiplier': (slice(2, 5), atk_from_slice), 'rcv_multiplier': (slice(2, 5), rcv_from_slice)}),
    98: combo_match_convert({'for_attr': all_attr, 'minimum_combos': (0, cc), 'minimum_atk_multiplier': (1, multi), 'bonus_atk_multiplier': (2, multi), 'maximum_combos': (3, cc)}),
    100: convert('skill_used_stats', {'for_attr': all_attr, 'for_type': [], 'atk_multiplier': (slice(0, 4), atk_from_slice), 'rcv_multiplier': (slice(0, 4), rcv_from_slice)}),
    101: convert('exact_combo_match', {'combos': (0, cc), 'atk_multiplier': (1, multi)}),
    103: combo_match_convert({'for_attr': all_attr, 'minimum_combos': (0, cc), 'minimum_atk_multiplier': (slice(1, 4), atk_from_slice), 'minimum_rcv_multiplier': (slice(1, 4), rcv_from_slice), 'maximum_combos': (0, cc)}),
    104: combo_match_convert({'for_attr': (1, binary_con), 'minimum_combos': (0, cc), 'minimum_atk_multiplier': (slice(2, 5), atk_from_slice), 'minimum_rcv_multiplier': (slice(2, 5), rcv_from_slice), 'maximum_combos': (0, cc)}),
    105: passive_stats_convert({'for_attr': all_attr, 'atk_multiplier': (1, multi), 'rcv_multiplier': (0, multi)}),
    106: passive_stats_convert({'for_attr': all_attr, 'hp_multiplier': (0, multi), 'atk_multiplier': (1, multi)}),
    107: passive_stats_convert({'for_attr': all_attr, 'hp_multiplier': (0, multi)}),
    108: convert('passive_stats_type_atk_all_hp', {'for_type': (1, listify), 'atk_multiplier': (2, multi), 'hp_multiplier': (0, multi)}),
    109: mass_match_convert({'attributes': (0, binary_con), 'minimum_count': (1, cc), 'minimum_atk_multiplier': (2, multi)}),
    111: passive_stats_convert({'for_attr': (slice(0, 2), list_con), 'hp_multiplier': (2, multi), 'atk_multiplier': (2, multi)}),
    114: passive_stats_convert({'for_attr': (slice(0, 2), list_con), 'hp_multiplier': (2, multi), 'atk_multiplier': (2, multi), 'rcv_multiplier': (2, multi)}),
    119: mass_match_convert({'attributes': (0, binary_con), 'minimum_count': (1, cc), 'minimum_atk_multiplier': (2, multi), 'bonus_atk_multiplier': (3, multi), 'maximum_count': (4, cc)}),
    121: passive_stats_convert({'for_attr': (0, binary_con), 'for_type': (1, binary_con), 'hp_multiplier': (2, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2)}),
    122: threshold_stats_convert(BELOW, {'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'threshold': (0, multi), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2)}),
    123: threshold_stats_convert(ABOVE, {'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'threshold': (0, multi), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2)}),
    124: multi_attribute_match_convert({'attributes': (slice(0, 5), list_binary_con), 'minimum_match': (5, cc), 'minimum_atk_multiplier': (6, multi), 'bonus_atk_multiplier': (7, multi)}),
    125: convert('team_build_bonus', {'monster_ids': (slice(0, 5), list_con_pos), 'hp_multiplier': (5, multi2), 'atk_multiplier': (6, multi2), 'rcv_multiplier': (7, multi2)}),
    129: passive_stats_convert({'for_attr': (0, binary_con), 'for_type': (1, binary_con), 'hp_multiplier': (2, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2), 'reduction_attributes': (5, binary_con), 'damage_reduction': (6, multi)}),
    130: threshold_stats_convert(BELOW, {'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'threshold': (0, multi), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2), 'reduction_attributes': (5, binary_con), 'damage_reduction': (6, multi)}),
    131: threshold_stats_convert(ABOVE, {'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'threshold': (0, multi), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2), 'reduction_attributes': (5, binary_con), 'damage_reduction': (6, multi)}),
    133: convert('skill_used_stats', {'for_attr': (0, binary_con), 'for_type': (1, binary_con), 'atk_multiplier': (2, multi2), 'rcv_multiplier': (3, multi2)}),
    136: convert('dual_passive_stats', {'for_attr_1': (0, binary_con), 'for_type_1': [], 'hp_multiplier_1': (1, multi2), 'atk_multiplier_1': (2, multi2), 'rcv_multiplier_1': (3, multi2), 'for_attr_2': (4, binary_con), 'for_type_2': [], 'hp_multiplier_2': (5, multi2), 'atk_multiplier_2': (6, multi2), 'rcv_multiplier_2': (7, multi2)}),
    137: convert('dual_passive_stats', {'for_attr_1': [], 'for_type_1': (0, binary_con), 'hp_multiplier_1': (1, multi2), 'atk_multiplier_1': (2, multi2), 'rcv_multiplier_1': (3, multi2), 'for_attr_2': [], 'for_type_2': (4, binary_con), 'hp_multiplier_2': (5, multi2), 'atk_multiplier_2': (6, multi2), 'rcv_multiplier_2': (7, multi2)}),
    138: convert('combine_leader_skills', {'skill_ids': (slice(None), list_con)}),
    139: convert('dual_threshold_stats', {'for_attr': (0, binary_con), 'for_type': (1, binary_con),
                                          'threshold_1': (2, multi), 'above_1': (3, lambda x: not bool(x)), 'atk_multiplier_1': (4, multi), 'rcv_multiplier_1': 1.0, 'damage_reduction_1': 0.0,
                                          'threshold_2': (5, multi), 'above_2': (6, lambda x: not bool(x)), 'atk_multiplier_2': (7, multi), 'rcv_multiplier_2': 1.0, 'damage_reduction_2': 0.0}),
    148: convert('rank_experience_rate', {'multiplier': (0, multi)}),
    149: convert('heath_tpa_stats', {'rcv_multiplier': (0, multi)}),
    150: convert('five_orb_one_enhance', {'atk_multiplier': (1, multi)}),
    151: convert('heart_cross', {'atk_multiplier': (0, multi2), 'rcv_multiplier': (1, multi2), 'damage_reduction': (2, multi)}),
    155: convert('multiplayer_stats', {'for_attr': (0, binary_con), 'for_type': (1, binary_con), 'hp_multiplier': (2, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2)}),
    157: convert('color_cross', {'crosses': (slice(None), lambda x: [{'attribute': a, 'atk_multiplier': multi(d)} for a, d in zip(x[::2], x[1::2])])}),
    158: convert('minimum_match', {'minimum_match': (0, cc), 'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'hp_multiplier': (4, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (5, multi2)}),
    159: mass_match_convert({'attributes': (0, binary_con), 'minimum_count': (1, cc), 'minimum_atk_multiplier': (2, multi), 'bonus_atk_multiplier': (3, multi), 'maximum_count': (4, cc)}),
    162: convert('large_board', {'for_attr': [], 'for_type': [], 'hp_multiplier': 1.0, 'atk_multiplier': 1.0, 'rcv_multiplier': 1.0}),
    163: convert('no_skyfall', {}),
    164: multi_attribute_match_convert({'attributes': (slice(0, 4), list_binary_con), 'minimum_match': (4, cc), 'minimum_atk_multiplier': (5, multi), 'minimum_rcv_multiplier': (6, multi), 'bonus_atk_multiplier': (7, multi), 'bonus_rcv_multiplier': (7, multi)}),
    165: attribute_match_convert({'attributes': (0, binary_con), 'minimum_attributes': (1, cc), 'minimum_atk_multiplier': (2, multi), 'minimum_rcv_multiplier': (3, multi), 'bonus_atk_multiplier': (4, multi), 'bonus_rcv_multiplier': (5, multi), 'maximum_attributes': (slice(1, 7, 6), lambda x: x[0] + x[1])}),
    166: combo_match_convert({'for_attr': all_attr, 'minimum_combos': (0, cc), 'minimum_atk_multiplier': (1, multi), 'minimum_rcv_multiplier': (2, multi), 'bonus_atk_multiplier': (3, multi), 'bonus_rcv_multiplier': (4, multi), 'maximum_combos': (5, cc)}),
    167: mass_match_convert({'attributes': (0, binary_con), 'minimum_count': (1, cc), 'minimum_atk_multiplier': (2, multi), 'minimum_rcv_multiplier': (3, multi), 'bonus_atk_multiplier': (4, multi), 'bonus_atk_multiplier': (5, multi), 'maximum_count': (6, cc)}),
    169: combo_match_convert({'for_attr': all_attr, 'minimum_combos': (0, cc), 'minimum_atk_multiplier': (1, multi), 'minimum_damage_reduction': (2, multi)}),
    170: attribute_match_convert({'attributes': (0, binary_con), 'minimum_attributes': (1, cc), 'minimum_atk_multiplier': (2, multi), 'minimum_damage_reduction': (3, multi)}),
    171: multi_attribute_match_convert({'attributes': (slice(0, 4), list_binary_con), 'minimum_match': (4, cc), 'minimum_atk_multiplier': (5, multi), 'minimum_damage_reduction': (6, multi)}),
    175: convert('collab_bonus', {'collab_id': (0, cc), 'hp_multiplier': (3, multi2), 'atk_multiplier': (4, multi2), 'rcv_multiplier': (5, multi2)}),
    177: convert('orbs_remaining', {'orb_count': (5, cc), 'atk_multiplier': (6, multi)}),
    178: convert('fixed_move_time', {'time': (0, cc), 'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'hp_multiplier': (3, multi2), 'atk_multiplier': (4, multi2), 'rcv_multiplier': (5, multi2)}),
    182: mass_match_convert({'attributes': (0, binary_con), 'minimum_count': (1, cc), 'minimum_atk_multiplier': (2, multi), 'minimum_damage_reduction': (3, multi)}),
    183: convert('dual_threshold_stats', {'for_attr': (0, binary_con), 'for_type': (1, binary_con),
                                          'threshold_1': (2, multi), 'above_1': True, 'atk_multiplier_1': (3, multi), 'rcv_multiplier_1': 1.0, 'damage_reduction_1': (4, multi),
                                          'threshold_2': (5, multi), 'above_2': False, 'atk_multiplier_2': (6, multi2), 'rcv_multiplier_2': (7, multi2), 'damage_reduction_2': 0.0}),
    185: convert('bonus_move_time', {'time': (0, multi), 'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'hp_multiplier': (3, multi2), 'atk_multiplier': (4, multi2), 'rcv_multiplier': (5, multi2)}),
    186: convert('large_board', {'for_attr': (0, binary_con), 'for_type': (1, binary_con), 'hp_multiplier': (2, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2)}), }


def reformat(d: {str: (str, str)}, pretty=False):
    if 'skill' in d:
        print('-- Parsing skills --\n')
        skill_data = json.load(open(d['skill'][0]))
        print('Raw skills json loaded\n')
        reformatted = {}
        reformatted['res'] = skill_data['res']
        reformatted['version'] = skill_data['v']
        reformatted['ckey'] = skill_data['ckey']
        reformatted['active_skills'] = {}
        reformatted['leader_skills'] = {}

        print(f'Starting skill conversion of {len(skill_data["skill"])} skills')
        for i, c in enumerate(skill_data['skill']):
            if c[3] == 0 and c[4] == 0:  # this distinguishes leader skills from active skills
                reformatted['leader_skills'][i] = {}
                reformatted['leader_skills'][i]['id'] = i
                reformatted['leader_skills'][i]['name'] = c[0]
                reformatted['leader_skills'][i]['card_description'] = c[1]
                if c[2] in SKILL_TRANSFORM:
                    reformatted['leader_skills'][i]['type'], reformatted['leader_skills'][i]['args'] = SKILL_TRANSFORM[c[2]](
                        c[6:])
                    if type(reformatted['leader_skills'][i]['args']) == list:
                        print(f'Unhandled leader skill type: {c[2]} (skill id: {i})')
                        del reformatted['leader_skills'][i]
                else:
                    print(f'Unexpected leader skill type: {c[2]} (skill id: {i})')
                    del reformatted['leader_skills'][i]
                    #reformatted['leader_skills'][i]['type'] = f'_{c[2]}'
                    #reformatted['leader_skills'][i]['args'] = {f'_{i}':v for i,v in enumerate(c[6:])}
            else:
                reformatted['active_skills'][i] = {}
                reformatted['active_skills'][i]['id'] = i
                reformatted['active_skills'][i]['name'] = c[0]
                reformatted['active_skills'][i]['card_description'] = c[1]
                reformatted['active_skills'][i]['max_skill'] = c[3]
                reformatted['active_skills'][i]['base_cooldown'] = c[4]
                if c[2] in SKILL_TRANSFORM:
                    reformatted['active_skills'][i]['type'], reformatted['active_skills'][i]['args'] = SKILL_TRANSFORM[c[2]](
                        c[6:])
                    if type(reformatted['active_skills'][i]['args']) != dict:
                        print(f'Unhandled active skill type: {c[2]} (skill id: {i})')
                        del reformatted['active_skills'][i]
                else:
                    print(f'Unexpected active skill type: {c[2]} (skill id: {i})')
                    del reformatted['active_skills'][i]
                    #reformatted['active_skills'][i]['type'] = f'_{c[2]}'
                    #reformatted['active_skills'][i]['args'] = {f'_{i}':v for i,v in enumerate(c[6:])}

        print(f"Converted {len(reformatted['active_skills'])} active skills and {len(reformatted['leader_skills'])} leader skills ({len(reformatted['active_skills']) + len(reformatted['leader_skills'])} total)\n")

        def verify(skills):
            ls_verification = defaultdict(lambda: defaultdict(set))
            for name, data in skills.items():
                ls_verification[data['type']]['_arg_names'].add(frozenset(data['args'].keys()))
                for a_name, a_value in data['args'].items():
                    ls_verification[data['type']][a_name].add(type(a_value))
            for name, value in ls_verification.items():
                for a, p in value.items():
                    if len(p) != 1:
                        print(f'INCONSISTENT name:{name} difference in {repr(a)}: {repr(p)}\n')

        print('Checking active skill consistency\n-------start-------\n')
        verify(reformatted['active_skills'])
        print('--------end--------\n')

        print('Checking leader skill consistency\n-------start-------\n')
        verify(reformatted['leader_skills'])
        print('--------end--------\n')

        out_file = open(d['skill'][1], 'w')
        out_file.write(json.dumps(reformatted, indent=4, sort_keys=True)
                       if pretty else json.dumps(reformatted, sort_keys=True))
        out_file.close()
        print(f'Result saved\n')
        print(f'-- End skills --\n')

    if 'dungeon' in d:
        dungeon_data = json.load(open(d['dungeon'][0]))
        reformatted = {}
        reformatted['res'] = dungeon_data['res']
        reformatted['version'] = dungeon_data['v']
        reformatted['dungeons'] = []

        def dungeon_floor_parameters(s):
            parameters = s.split('|')
            result = {}

            if '7*6' in parameters:
                result['board'] = 'large'
            elif '5*4' in parameters:
                result['board'] = 'small'
            else:
                result['board'] = 'normal'

            result['skyfalls'] = 'ndf' not in parameters

            parameter_dict = {t[0]: t[1]
                              for p in parameters for t in tuple(p.split(':')) if len(t) > 1}

            result['fixed_move_time'] = parameter_dict['ft'] / 10 if 'ft' in parameter_dict else -1

            def param_to_card(c):
                re = {}
                re['id'] = int(c[0]) if len(c) > 0 else 0
                re['level'] = int(c[1]) if len(c) > 1 else 99  # max
                re['plus_hp'] = int(c[2]) if len(c) > 2 else 0
                re['plus_atk'] = int(c[3]) if len(c) > 3 else 0
                re['plus_rcv'] = int(c[4]) if len(c) > 4 else 0
                re['awakenings'] = int(c[5]) if len(c) > 5 else 99  # max
                re['skill_level'] = int(c[6]) if len(c) > 6 else 99  # max
                return re

            result['fixed_team'] = [param_to_card(parameter_dict['fc' + i].split(';') if 'fc' + i in parameter_dict else [
            ]) for i in range(1, 7)] if any('fc' + i in parameter_dict for i in range(1, 7)) else []

            result['dungeon_messages'] = [parameter_dict['dmsg' + i]
                                          for i in range(1, 5) if 'dmsg' + i in parameter_dict]
            result['small_messages'] = [parameter_dict['smsg' + i]
                                        for i in range(1, 5) if 'smsg' + i in parameter_dict]

            def get_bonuses(data, name):
                re = {}
                re[name] = binary_con(int(c[0])) if len(c) > 0 else []
                re['hp_multiplier'] = int(c[1]) if len(c) > 1 else 1.0
                re['atk_multiplier'] = int(c[2]) if len(c) > 2 else 1.0
                re['rcv_multiplier'] = int(c[3]) if len(c) > 3 else 1.0
                return re

            result['type_bonus'] = get_bonuses(parameter_dict['btype'].split(
                ';') if 'btype' in parameter_dict else [], 'types')
            result['attribute_bonus'] = get_bonuses(parameter_dict['battr'].split(
                ';') if 'battr' in parameter_dict else [], 'attributes')
            result['rarity_bonus'] = get_bonuses(parameter_dict['btype'].split(
                ';') if 'btype' in parameter_dict else [], 'rarities')

            # these arguments have an unknown purpose
            result['hp'] = parameter_dict['hp'] if 'hp' in parameter_dict else 0  # hp? enemy? team?
            result['at'] = parameter_dict['at'] if 'hp' in parameter_dict else 0  # attack? enemy? team?
            result['df'] = parameter_dict['df'] if 'hp' in parameter_dict else 0  # defense?
            result['dg'] = parameter_dict['dg'] if 'hp' in parameter_dict else 0  # damage? enemy? team?
            # never seen this mechanic
            result['hpfix'] = parameter_dict['hpfix'] if 'hp' in parameter_dict else 0

            return result

        data = iter(csv_decoder(dungeon_data['dungeons']))
        curr = next(data)
        counters = {'floor_length': set(), 'floor_data': {k: {r: set() for r in range(k)}
                                                          for k in [11, 12, 13, 14, 15, 16, 17, 18, 19]}}
        try:
            while True:
                if curr[0].startswith('d;'):
                    dungeon = {}
                    dungeon['id'] = curr[0][2:]
                    dungeon['name'] = curr[1]
                    dungeon['floors'] = []
                    dungeon['flags'] = binary_con(int(curr[2]))
                    dungeon['category'] = {7: '3_player', 5: 'coop',  4: 'ranking_dungeon', 3: 'gift_dungeon',
                                           2: 'technical_dungeon', 1: 'special_dungeon', 0: 'normal_dungeon'}[int(curr[3])]
                    dungeon['weekday'] = {8: 'weekend', 5: 'friday', 4: 'thursday',
                                          3: 'wednesday', 2: 'tuesday', 1: 'monday', 0: 'non_weekday'}[int(curr[4])]
                    dungeon['category_2'] = int(curr[5])

                    curr = next(data)
                    while curr[0].startswith('f;'):
                        floor = {}
                        floor['id'] = curr[0][2:]
                        floor['name'] = curr[1]
                        floor['floor_count'] = curr[4]
                        floor['stamina_cost'] = curr[4]
                        floor['unknown_data'] = {k: curr[k] for k in {
                            2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19} if k < len(curr)}
                        dungeon['floors'].append(floor)
                        counters['floor_length'].add(len(curr))
                        for i in range(len(curr)):
                            if i not in {0, 1}:
                                counters['floor_data'][len(curr)][i].add(curr[i])
                        curr = next(data)

                    reformatted['dungeons'].append(dungeon)

                elif curr[0].startswith('c;'):
                    reformatted['c'] = curr[0][2:]
                    curr = next(data)

                else:
                    print(
                        f'Something went wrong while reading this line of dungeon data, skipping:\n{curr}')
                    curr = next(data)
        except StopIteration:
            pass
        except:
            print('A CRITICAL ERROR OCCURED, SAVING SUCCESSFUL DATA')

        #################
        ## DEBUG START ##
        #################

##        print(f"floor_length: {counters['floor_length']}")
# def print_floor_info():
# for l in [11, 12, 13, 14, 15, 16, 17, 18, 19]:
##                print(f"----- floor_data for len {l}: -----")
# for a,v in counters['floor_data'][l].items():
# try:
##                        print(f">> {a}:\n{sorted(int(vv) for vv in v)}")
# except:
##                        print(f">> {a}:\n{sorted(v)}")
##        nl = '\n'
##
# print_floor_info()
##
# def pd(du):
##            print(f"-----------\n{du['id']}\n{du['name']}\n{nl.join('  ' +f['name'] for f in du['floors'])}")
##
# def dungeon_search(p):
##            print(' -- start search --')
# for dd in [du for du in reformatted['dungeons'] if p(du)]:
# pd(dd)
# print(f"{int(dd['id']):4d} {dd['name']}")
# print('-----------\n\n')

        #dungeon_search(lambda d: int(d['category']) == 0)
        #dungeon_search(lambda d: any('smsg2' in f['unknown_data'][9] for f in d['floors']))

        #print(f"dungeon_data_5: \n{sorted(int(x) for x in counters['dungeon_data'][5])}\n")
        #dungeon_search(lambda d: print(d))

        #print(f"dungeon_data_2: \n{nl.join(str(binary_con(x)) for x in sorted(int(xx) for xx in counters['dungeon_data'][2]))}\n")
        #print(f"dungeon_data_3: {sorted(int(x) for x in counters['dungeon_data'][3])}\n")
        # notes on dungeon_data_3
        # 7 3player dungeons
        # 5 coop, some upper technicals?
        # 4 ranking dungeons
        # 3 gift dungeons (eg. 'Egg-Cellent Blessings')
        # 2 technical dungeons (full list, nothing else)
        # 1 special dungeons - includes daily descendeds, weekly dungeons, LTD, some gifts, one-shot and descended challenges, and challenge dungeons
        # 0 normal dungeons - including tutorial stages

        #print(f"dungeon_data_4: {sorted(int(x) for x in counters['dungeon_data'][4])}\n")
        # notes on dungeon_data_4
        # 8 Weekend Dungeon
        # 5 Friday and Gold dragons
        # 4 Thursday and emerald
        # 3 Wednesday and Sapphire
        # 2 Tuesday and ruby
        # 1 Monday and metal
        # 0 Everything else

        #print(f"dungeon_data_5: \n{sorted(int(x) for x in counters['dungeon_data'][5])}\n")
        # notes on dungeon_data_5
        # 600011 - 3p - collab dungeons
        # 600003 - 3p - dragon rush and cosmic trinity
        # 600002 - 3p - arena and evo rush
        # 600001 - 3p - endless
        # 500011 - Special - event - mp reward
        # 500001 ?lots of data? - Special - event - one-shot challenges, monthly rush rewards, +297/99 dungeons, gift dungeons (py, snowglobe, jewel, etc.)
        # 490001 - Special - REMdragon, one-shot challenge 3 (only)
        # 400001 - Special - limited time dungeons (tamas, predras, sstd, awoken mats)
        # 300001 - Special - weekday evo mats (new and old)
        # 299911 - Special - weekday metal dragons
        # 299902 - Special - Tues-Wed-Thurs-Fri Dungeon
        # 290001 - Special? - JP!! only contains machine quest challenge (マシンクエストチャレンジ)
        # 220001 - Special/Technical - team challenge descendeds (team of x or less), colosseum
        # 210051 - Special - Revo challenge dungeons (white-snek, verse, etc)
        # 210011 - Special/Coin - Collab dungeons
        # 210006 - Special - time limit dungeons (eg. Titania 90 seconds), and 'Awakening Materials Selection!'
        # 210004 - Special - PAD academy
        # 210002 - Special - 'Descended Challenge!' #15 only, four unknown 'Challenge Dungeons!'s, and 'Ultimate Survey Rush!'
        # 210001 - Special - Weekly dungeons (eg. insect dragons), seasonal dungeons (eg. new year, pad island, halloween), some old challenge dungeons, 'Evo Material Party' 1/2, 'Alt. Challenge Dungeons!'
        # 202002 - Special? - 'Super Ultimate Devil Rush! α'
        # 201902 - Special? - 'Ultimate Yamato Rush! α'
        # 200601 - Technical - Machine Zeus, Machine Hera
        # 200305 - Special/Coin - Linthia, Gainaut
        # 200304 - Special/Coin - Volsung
        # 200303 - Special/Coin - Scarlet
        # 200302 - Special/Coin - Nordis
        # 200301 - Special/Coin - Zaerog∞
        # 200207 - Special - 'Super-Ultimate Dragon Rush!'
        # 200205 - Special - 'Ultimate Yamato Rush!'
        # 200204 - Special - 'Ultimate Dragon Rush!'
        # 200203 - Special - 'Ultimate Devil Rush!'
        # 200202 - Special - 'Ultimate Hera Rush!'
        # 200201 - Special - 'Ultimate God Rush!'
        # 200110 - Technical - 'Alt. Talos's Abyss'
        # 200109 - Technical - 'Alt. Aither Desert'
        # 200108 - Technical - 'Alt. Hemera Volcanic Belt'
        # 200107 - Technical - 'Alt. Creek of Neleus'
        # 200106 - Technical - 'Alt. Hypno Forest'
        # 200105 - Technical - 'Alt. Temple of Trailokya'
        # 200104 - Technical - 'Alt. Shrine of Blazing Woods'
        # 200103 - Technical - 'Alt. Shrine of Liquid Flame'
        # 200102 - Technical - 'Alt. Shrine of Green Water'
        # 200101 - Technical - 'Alt. Castle of Satan in Abyss'
        # 200056 - Technical - 'Pirate Dragon's Hidden Grotto'
        # 200055 - Technical - 'Mystic Dragon Historic Site'
        # 200054 - Technical - 'Dragon Knight Sanctuary'
        # 200053 - Technical - 'Domain of the War Dragons'
        # 200052 - Technical - 'Ancient Dragons' Mystic Realm'
        # 200051 - Technical - 'Mechdragons' Massive Fortress'
        # 200025 - Technical - 'Temple of Trailokya'
        # 200024 - Technical - 'Shrine of Blazing Woods'
        # 200023 - Technical - 'Shrine of Liquid Flame'
        # 200022 - Technical - 'Shrine of Green Water'
        # 200021 - Technical/Normal? - 'Castle of Satan in the Abyss'
        # 200011 - Special? - 'Mythical Endless Corridors'
        # 150001 - Special - King Carnival
        # 60102 - Special - gold, ruby, sapphire, emerald dragon LTD (no metal), SKC, tamas
        # 60002 - Special - two one-shot challenges
        # 60001 - Special - most descended dungeons, multiple 'Descended Challenge!' and 'Challenge Dungeons!', rikuu and some other misc dungeons
        # 38911 - Special - 'Hera Descended'
        # 38910 - Special - 'Hero Descended'
        # 38909 - Special - 'The Goddess Descended!'
        # 38908 - Special - 'The Thief Descended!'
        # 38907 - Special - 'Hera-Is Descended!'
        # 38906 - Special - 'Hera-Ur Descended!'
        # 38905 - Special - 'Takeminakata Descended!'
        # 38904 - Special - 'Izanami Descended!'
        # 38903 - Special - 'Heracles Descended!'
        # 38902 - Special - 'Zeus Descended!'
        # 32001 - Special - 'Endless Corridors'
        # 31002 - Special - ultimate hera, zeus, devil, yamato rush; super ultimate dragon rush, special descended rush
        # 31001 - Coop - 'Score Attack Dungeon'
        # 30012 - Special - 'Super Ultimate Colosseum-Special'
        # 30011 - Special - Arena and Alt. Arena
        # 23111 - Special - 'The God-King's Floating Garden'
        # 23101 - Special - All alt. technicals (eg. Alt. Castle of Satan in Abyss)
        # 21617 - Special - 'Pirate Dragon's Hidden Grotto'
        # 21616 - Special - 'Mystic Dragon Historic Site'
        # 21615 - Special - 'Dragon Knight Sanctuary'
        # 21614 - Special - 'Domain of the War Dragons'
        # 21613 - Special - 'Ancient Dragons' Mystic Realm'
        # 21612 - Special - 'Mechdragons' Massive Fortress'
        # 5614 - Special - 'The Heroes' Hideout'
        # 5613 - Special - 'Divine Queen's Sleepless Castle'
        # 5612 - Special - 'Sky Dragons' Domain'
        # 5611 - Special - 'Legendary Dragons' Footprints'
        # 2 - Special - 'True Endless Corridors'
        # 1 - Special - rougelikes (not myr), ultimate god, hera, devil, dragon, yamato rush, super ulti dragon rush
        # 0 - Normal/Tehcnial/Special... - Basically everything else

        #################
        ##  DEBUG END  ##
        #################

        out_file = open(d['dungeon'][1], 'w')
        out_file.write(json.dumps(reformatted, indent=4, sort_keys=True)
                       if pretty else json.dumps(reformatted, sort_keys=True))
        out_file.close()

    if 'enemy_skill' in d:
        skill_data = json.load(open(d['enemy_skill'][0]))
        reformatted = {}
        reformatted['res'] = skill_data['res']
        reformatted['version'] = skill_data['v']
        reformatted['skills'] = []

        r = csv_decoder(skill_data['enemy_skills'])
        reader = csv.reader(csv.reader([skill_data['enemy_skills']], delimiter='\n'))
        for skill in r:
            if skill[0] == 'c':
                reformatted['c'] = skill[1]
            else:
                reformatted['skills'].append(skill)

        out_file = open(d['enemy_skill'][1], 'w')
        out_file.write(json.dumps(reformatted, indent=4, sort_keys=True)
                       if pretty else json.dumps(reformatted, sort_keys=True))
        out_file.close()

    if 'card' in d:
        cards_data = json.load(open(d['card'][0]))
        reformatted = {}
        reformatted['res'] = cards_data['res']
        reformatted['version'] = cards_data['v']
        reformatted['ckey'] = cards_data['ckey']
        reformatted['cards'] = {}
        reformatted['evolutions'] = defaultdict(list)
        for card_data in cards_data['card']:
            card = {}
            card['id'] = card_data[0]
            card['name'] = card_data[1]
            card['attribute'] = card_data[2]
            card['subattribute'] = card_data[3]
            card['ultimate_evolution'] = card_data[4] == 1
            card['types'] = [card_data[t] for t in [5, 6] if card_data[t] != -1]  # add type 3 later
            card['rarity'] = card_data[7]
            card['cost'] = card_data[8]
            # 9, unsure of purpose
            card['max_level'] = card_data[10]
            card['feed_experience'] = card_data[11] / 4  # per level
            card['released'] = card_data[12] == 100
            card['sell_value_coin'] = card_data[13] / 10  # per level
            card['hp_minimum'] = card_data[14]
            card['hp_maximum'] = card_data[15]
            card['hp_curve'] = card_data[16]
            card['atk_minimum'] = card_data[17]
            card['ark_maximum'] = card_data[18]
            card['atk_curve'] = card_data[19]
            card['rcv_minimum'] = card_data[20]
            card['rcv_maximum'] = card_data[21]
            card['rcv_curve'] = card_data[22]
            card['max_experience'] = card_data[23]
            card['experience_curve'] = card_data[24]
            card['active_skill_id'] = card_data[25]
            card['leader_skill_id'] = card_data[26]
            # 27 - 36 enemy encounter stats
            # 37
            # 38 - 39 dungeon drop info
            if card_data[40] != 0:
                evo = {}
                evo['base'] = card_data[40]
                evo['materials'] = [card_data[t] for t in range(41, 46) if card_data[t] != 0]
                evo['is_ultimate'] = card['ultimate_evolution']
                evo['result'] = card['id']
                reformatted['evolutions'][evo['base']].append(evo)
            card['devo_materials'] = [card_data[t]
                                      for t in range(46, 51) if card_data[t] != 0]  # mats to devolve
            # next amount varries in length, depends on bitmaps 51 - 56
            # enemy skill data goes here
            card['awakenings'] = []  # variable index length
            card['superawakenings'] = []
            card['base_evo_id'] = 0  # the base evo of the card
            card['group'] = 0
            # add type 3, where [3] is [card_data[index]]
            card['types'].extend([3] if -1 != -1 else [])
            card['sell_value_mp'] = 0
            card['latent_on_fuse'] = 0  # which latent awakening is granted upon fusing this card away
            card['collab'] = 0  # collab id, also includes dbdc as a special collab id
            card['inheritable'] = 2 == 3  # where 2 is card_group[index]
            card['furigana'] = ''
            card['limitbreakable'] = 0 > 0  # where 0 is card_data[index]
            # percentage increase, where 0 is card_data[index], same index as last
            card['limitbreak_stat_increase'] = 0
            reformatted['cards'][card['id']] = card

        out_file = open(d['card'][1], 'w')
        out_file.write(json.dumps(reformatted, indent=4, sort_keys=True)
                       if pretty else json.dumps(reformatted, sort_keys=True))
        out_file.close()


if __name__ == '__main__':
    pass
