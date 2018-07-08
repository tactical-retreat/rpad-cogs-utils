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
                         'rcv_multiplier': 1.0, 'reduction_attributes': all_attr, 'damage_reduction': 0.0, 'skill_text': ''}


def passive_stats_convert(arguments):
    def f(x):
        _, c = convert('passive_stats', {
                       k: (arguments[k] if k in arguments else v) for k, v in passive_stats_backups.items()})(x)
        if not c['for_type']:
            if c['hp_multiplier'] != 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] != 1:
                if c['hp_multiplier'] == c['atk_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x all stats for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
                elif c['hp_multiplier'] == c['atk_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP & ATK and ' + str(
                        c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
                elif c['hp_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP & RCV and ' + str(
                        c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
                elif c['atk_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip(
                        '.') + 'x ATK & RCV and ' + str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
            elif c['hp_multiplier'] == 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] != 1:
                if c['atk_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['atk_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x ATK & RCV for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
                else:
                    c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + \
                        'x ATK and ' + str(c['rcv_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x RCV for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
            elif c['hp_multiplier'] != 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] != 1:
                if c['hp_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x HP & RCV for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
                else:
                    c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP and ' + \
                        str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
            elif c['hp_multiplier'] != 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] == 1:
                if c['atk_multiplier'] == c['hp_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x HP & ATK for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
                else:
                    c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP and ' + \
                        str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
            elif c['hp_multiplier'] == 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] != 1:
                c['skill_text'] += str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                if c['for_attr'] == [0, 1, 2, 3, 4]:
                    c['skill_text'] += 'all Att.'
                else:
                    for i in c['for_attr'][:-1]:
                        c['skill_text'] += ATTRIBUTES[i] + ', '
                    c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
            elif c['hp_multiplier'] == 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] == 1:
                c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK for '
                if c['for_attr'] == [0, 1, 2, 3, 4]:
                    c['skill_text'] += 'all Att.'
                else:
                    for i in c['for_attr'][:-1]:
                        c['skill_text'] += ATTRIBUTES[i] + ', '
                    c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
            elif c['hp_multiplier'] != 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] == 1:
                c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP for '
                if c['for_attr'] == [0, 1, 2, 3, 4]:
                    c['skill_text'] += 'all Att.'
                else:
                    for i in c['for_attr'][:-1]:
                        c['skill_text'] += ATTRIBUTES[i] + ', '
                    c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
        else:
            if c['hp_multiplier'] != 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] != 1:
                if c['hp_multiplier'] == c['atk_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x all stats for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
                elif c['hp_multiplier'] == c['atk_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP & ATK and ' + str(
                        c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
                elif c['hp_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP & RCV and ' + str(
                        c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
                elif c['atk_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip(
                        '.') + 'x ATK & RCV and ' + str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
            elif c['hp_multiplier'] == 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] != 1:
                if c['atk_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['atk_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x ATK & RCV for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
                else:
                    c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + \
                        'x ATK and ' + str(c['rcv_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x RCV for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
            elif c['hp_multiplier'] != 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] != 1:
                if c['hp_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x HP & RCV for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
                else:
                    c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP and ' + \
                        str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
            elif c['hp_multiplier'] != 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] == 1:
                if c['atk_multiplier'] == c['hp_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x HP & ATK for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
                else:
                    c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP and ' + \
                        str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
            elif c['hp_multiplier'] == 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] != 1:
                c['skill_text'] += str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                for i in c['for_type'][:-1]:
                    c['skill_text'] += TYPES[i] + ', '
                c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
            elif c['hp_multiplier'] == 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] == 1:
                c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK for '
                for i in c['for_type'][:-1]:
                    c['skill_text'] += TYPES[i] + ', '
                c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
            elif c['hp_multiplier'] != 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] == 1:
                c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP for '
                for i in c['for_type'][:-1]:
                    c['skill_text'] += TYPES[i] + ', '
                c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
        if c['damage_reduction'] != 0.0:
            c['skill_text'] += '; Reduce damage taken by ' + \
                str(c['damage_reduction'] * 100).rstrip('0').rstrip('.') + '%'
        return 'passive_stats', c
    return f


threshold_stats_backups = {'for_attr': [], 'for_type': [], 'threshold': False, 'atk_multiplier': 1.0,
                           'rcv_multiplier': 1.0, 'reduction_attributes': all_attr, 'damage_reduction': 0.0, 'skill_text': ''}
ABOVE = True
BELOW = False


def threshold_stats_convert(above, arguments):
    def f(x):
        if above:
            _, c = convert('above_threshold_stats', {
                           k: (arguments[k] if k in arguments else v) for k, v in threshold_stats_backups.items()})(x)
            if c['damage_reduction'] == 0:
                if c['rcv_multiplier'] == 1.0:
                    if not c['for_type']:
                        c['skill_text'] += str(c['atk_multiplier']
                                               ).rstrip('0').rstrip('.') + 'x ATK '
                        if c['for_attr'] == [0, 1, 2, 3, 4]:
                            c['skill_text'] += 'when above ' + \
                                str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                        else:
                            c['skill_text'] += 'for '
                            for i in c['for_attr'][:-1]:
                                c['skill_text'] += ATTRIBUTES[i] + ', '
                            c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att. when above ' + str(
                                c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                        return 'above_threshold_stats', c
                    else:
                        c['skill_text'] += str(c['atk_multiplier']
                                               ).rstrip('0').rstrip('.') + 'x ATK for '
                        for i in c['for_type'][:-1]:
                            c['skill_text'] += TYPES[i] + ', '
                        c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type when above ' + str(
                            c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                        return 'above_threshold_stats', c
                else:
                    if c['rcv_multiplier'] == c['atk_multiplier']:
                        if not c['for_type']:
                            c['skill_text'] += str(c['atk_multiplier']
                                                   ).rstrip('0').rstrip('.') + 'x ATK & RCV '
                            if c['for_attr'] == [0, 1, 2, 3, 4]:
                                c['skill_text'] += 'when above ' + \
                                    str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                            else:
                                c['skill_text'] += 'for '
                                for i in c['for_attr'][:-1]:
                                    c['skill_text'] += ATTRIBUTES[i] + ', '
                                c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att. when above ' + str(
                                    c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                            return 'above_threshold_stats', c
                        else:
                            c['skill_text'] += str(c['atk_multiplier']
                                                   ).rstrip('0').rstrip('.') + 'x ATK & RCV for '
                            for i in c['for_type'][:-1]:
                                c['skill_text'] += TYPES[i] + ', '
                            c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type when above ' + str(
                                c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                            return 'above_threshold_stats', c
                    else:
                        if not c['for_type']:
                            c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip(
                                '.') + 'x ATK and ' + str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV '
                            if c['for_attr'] == [0, 1, 2, 3, 4]:
                                c['skill_text'] += 'when above ' + \
                                    str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                            else:
                                c['skill_text'] += 'for '
                                for i in c['for_attr'][:-1]:
                                    c['skill_text'] += ATTRIBUTES[i] + ', '
                                c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att. when above ' + str(
                                    c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                            return 'above_threshold_stats', c
                        else:
                            c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip(
                                '.') + 'x ATK and ' + str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                            for i in c['for_type'][:-1]:
                                c['skill_text'] += TYPES[i] + ', '
                            c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type when above ' + str(
                                c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                            return 'above_threshold_stats', c
            elif c['atk_multiplier'] == 1.0:
                c['skill_text'] += 'Reduce damage taken by ' + str(c['damage_reduction'] * 100).rstrip(
                    '0').rstrip('.') + '% when above ' + str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                return 'above_threshold_stats', c
            else:
                if not c['for_type']:
                    c['skill_text'] += str(c['atk_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x ATK for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att. and reduce damage taken by ' + str(c['damage_reduction'] * 100).rstrip(
                            '0').rstrip('.') + '% when above ' + str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' and reduce damage taken by ' + str(c['damage_reduction'] * 100).rstrip(
                            '0').rstrip('.') + '% when above ' + str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                    return 'above_threshold_stats', c
                else:
                    c['skill_text'] += str(c['atk_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x ATK for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type when above ' + \
                        str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                    return 'above_threshold_stats', c
        else:
            _, c = convert('below_threshold_stats', {
                           k: (arguments[k] if k in arguments else v) for k, v in threshold_stats_backups.items()})(x)
            if c['damage_reduction'] == 0:
                if c['rcv_multiplier'] == 1.0:
                    if not c['for_type']:
                        c['skill_text'] += str(c['atk_multiplier']
                                               ).rstrip('0').rstrip('.') + 'x ATK '
                        if c['for_attr'] == [0, 1, 2, 3, 4]:
                            c['skill_text'] += 'when below ' + \
                                str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                        else:
                            c['skill_text'] += 'for '
                            for i in c['for_attr'][:-1]:
                                c['skill_text'] += ATTRIBUTES[i] + ', '
                            c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att. when below ' + str(
                                c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                        return 'below_threshold_stats', c
                    else:
                        c['skill_text'] += str(c['atk_multiplier']
                                               ).rstrip('0').rstrip('.') + 'x ATK for '
                        for i in c['for_type'][:-1]:
                            c['skill_text'] += TYPES[i] + ', '
                        c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type when below ' + str(
                            c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                        return 'below_threshold_stats', c
                else:
                    if c['rcv_multiplier'] == c['atk_multiplier']:
                        if not c['for_type']:
                            c['skill_text'] += str(c['atk_multiplier']
                                                   ).rstrip('0').rstrip('.') + 'x ATK & RCV '
                            if c['for_attr'] == [0, 1, 2, 3, 4]:
                                c['skill_text'] += 'when below ' + \
                                    str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                            else:
                                c['skill_text'] += 'for '
                                for i in c['for_attr'][:-1]:
                                    c['skill_text'] += ATTRIBUTES[i] + ', '
                                c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att. when below ' + str(
                                    c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                            return 'below_threshold_stats', c
                        else:
                            c['skill_text'] += str(c['atk_multiplier']
                                                   ).rstrip('0').rstrip('.') + 'x ATK & RCV for '
                            for i in c['for_type'][:-1]:
                                c['skill_text'] += TYPES[i] + ', '
                            c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type when below ' + str(
                                c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                            return 'below_threshold_stats', c
                    else:
                        if not c['for_type']:
                            c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip(
                                '.') + 'x ATK and ' + str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV '
                            if c['for_attr'] == [0, 1, 2, 3, 4]:
                                c['skill_text'] += 'when below ' + \
                                    str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                            else:
                                c['skill_text'] += 'for '
                                for i in c['for_attr'][:-1]:
                                    c['skill_text'] += ATTRIBUTES[i] + ', '
                                c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att. when below ' + str(
                                    c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                            return 'below_threshold_stats', c
                        else:
                            c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip(
                                '.') + 'x ATK and ' + str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                            for i in c['for_type'][:-1]:
                                c['skill_text'] += TYPES[i] + ', '
                            c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type when below ' + str(
                                c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                            return 'below_threshold_stats', c
            elif c['atk_multiplier'] == 1.0:
                c['skill_text'] += 'Reduce damage taken by ' + str(c['damage_reduction'] * 100).rstrip(
                    '0').rstrip('.') + '% when below ' + str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                return 'below_threshold_stats', c
            else:
                if not c['for_type']:
                    c['skill_text'] += str(c['atk_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x ATK for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att. and reduce damage taken by ' + str(c['damage_reduction'] * 100).rstrip(
                            '0').rstrip('.') + '% when below ' + str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' and reduce damage taken by ' + str(c['damage_reduction'] * 100).rstrip(
                            '0').rstrip('.') + '% when below ' + str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                    return 'below_threshold_stats', c
                else:
                    c['skill_text'] += str(c['atk_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x ATK for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type when below ' + \
                        str(c['threshold'] * 100).rstrip('0').rstrip('.') + '% HP'
                    return 'below_threshold_stats', c
    return f


combo_match_backups = {'for_attr': [], 'for_type': [], 'minimum_combos': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                                            'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                                       'maximum_combos': 0, 'reduction_attributes': all_attr, 'skill_text': ''}


def combo_match_convert(arguments):
    def f(x):
        _, c = convert('combo_match', {
                       k: (arguments[k] if k in arguments else v) for k, v in combo_match_backups.items()})(x)
        if c['maximum_combos'] == 0:
            c['maximum_combos'] = c['minimum_combos']
        if c['minimum_atk_multiplier'] == c['minimum_rcv_multiplier'] and c['bonus_atk_multiplier'] == c['bonus_rcv_multiplier']:
            c['skill_text'] = str(c['minimum_atk_multiplier']).rstrip('0').rstrip(
                '.') + 'x ATK & RCV when ' + str(c['minimum_combos']) + ' or more combos'
            if c['maximum_combos'] != c['minimum_combos']:
                c['skill_text'] += ' up to ' + str(c['minimum_atk_multiplier'] + (c['maximum_combos'] - c['minimum_combos'])
                                                   * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x at ' + str(c['maximum_combos']) + ' combos'
        elif c['minimum_damage_reduction'] != 0:
            c['skill_text'] = str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and reduce damage taken by ' + str(
                c['minimum_damage_reduction'] * 100).rstrip('0').rstrip('.') + '% when ' + str(c['minimum_combos']) + ' or more combos'
        else:
            c['skill_text'] = str(c['minimum_atk_multiplier']).rstrip('0').rstrip(
                '.') + 'x ATK when ' + str(c['minimum_combos']) + ' or more combos'
            if c['maximum_combos'] != c['minimum_combos']:
                c['skill_text'] += ' up to ' + str(c['minimum_atk_multiplier'] + (c['maximum_combos'] - c['minimum_combos'])
                                                   * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x at ' + str(c['maximum_combos']) + ' combos'
        return 'combo_match', c
    return f


attribute_match_backups = {'attributes': [], 'minimum_attributes': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                                      'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                             'maximum_attributes': 0, 'reduction_attributes': all_attr, 'skill_text': ''}


def attribute_match_convert(arguments):
    def f(x):
        _, c = convert('attribute_match', {
                       k: (arguments[k] if k in arguments else v) for k, v in attribute_match_backups.items()})(x)
        if c['maximum_attributes'] == 0:
            c['maximum_attributes'] = c['minimum_attributes']
        if c['attributes'] == [0, 1, 2, 3, 4]:
            if c['minimum_atk_multiplier'] == c['minimum_rcv_multiplier'] and c['bonus_atk_multiplier'] == c['bonus_rcv_multiplier']:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + \
                    'x ATK & RCV when matching ' + str(c['minimum_attributes']) + ' or more colors'
                if c['bonus_atk_multiplier'] != 0:
                    c['skill_text'] += ' up to ' + str(c['minimum_atk_multiplier'] + (
                        5 - c['minimum_attributes']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x at 5 colors'
            elif c['minimum_damage_reduction'] != 0:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and reduce damage taken by ' + str(
                    c['minimum_damage_reduction'] * 100).rstrip('0').rstrip('.') + '% when matching ' + str(c['minimum_attributes']) + ' or more colors'
            else:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + \
                    'x ATK when matching ' + str(c['minimum_attributes']) + ' or more colors'
                if c['bonus_atk_multiplier'] != 0:
                    c['skill_text'] += ' up to ' + str(c['minimum_atk_multiplier'] + (
                        5 - c['minimum_attributes']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x at 5 colors'
        elif c['attributes'] == [0, 1, 2, 3, 4, 5]:
            if c['minimum_atk_multiplier'] == c['minimum_rcv_multiplier'] and c['bonus_atk_multiplier'] == c['bonus_rcv_multiplier']:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK & RCV when matching ' + str(
                    c['minimum_attributes']) + ' or more colors (' + str(c['minimum_attributes'] - 1) + '+heal)'
                if c['bonus_atk_multiplier'] != 0:
                    c['skill_text'] += ' up to ' + str(c['minimum_atk_multiplier'] + (
                        5 - c['minimum_attributes']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x at 5 colors'
            elif c['minimum_damage_reduction'] != 0:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and reduce damage taken by ' + str(c['minimum_damage_reduction'] * 100).rstrip(
                    '0').rstrip('.') + '% when matching ' + str(c['minimum_attributes']) + ' or more colors (' + str(c['minimum_attributes'] - 1) + '+heal)'
            else:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK when matching ' + str(
                    c['minimum_attributes']) + ' or more colors (' + str(c['minimum_attributes'] - 1) + '+heal)'
                if c['bonus_atk_multiplier'] != 0:
                    c['skill_text'] += ' up to ' + str(c['minimum_atk_multiplier'] + (
                        5 - c['minimum_attributes']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x at 5 colors'
        elif c['attributes'] != []:
            if c['minimum_atk_multiplier'] == c['minimum_rcv_multiplier']:
                c['skill_text'] += str(c['minimum_atk_multiplier']
                                       ).rstrip('0').rstrip('.') + 'x ATK & RCV when matching '
                for i in c['attributes'][:-1]:
                    c['skill_text'] += ATTRIBUTES[i] + ', '
                c['skill_text'] += ATTRIBUTES[int(c['attributes'][-1])] + ' at once'
            else:
                c['skill_text'] += str(c['minimum_atk_multiplier']
                                       ).rstrip('0').rstrip('.') + 'x ATK when matching '
                for i in c['attributes'][:-1]:
                    c['skill_text'] += ATTRIBUTES[i] + ', '
                c['skill_text'] += ATTRIBUTES[int(c['attributes'][-1])] + ' at once'
        return 'attribute_match', c
    return f


multi_attribute_match_backups = {'attributes': [], 'minimum_match': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                                       'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                                   'reduction_attributes': all_attr, 'skill_text': ''}


def multi_attribute_match_convert(arguments):
    def f(x):
        _, c = convert('multi-attribute_match',
                       {k: (arguments[k] if k in arguments else v) for k, v in multi_attribute_match_backups.items()})(x)
        if all(x == c['attributes'][0] for x in c['attributes']):
            if c['minimum_damage_reduction'] != 0 and c['minimum_rcv_multiplier'] == 1:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and reduce damage taken by ' + str(c['minimum_damage_reduction']
                                                                                                                                        * 100).rstrip('0').rstrip('.') + '% when matching ' + str(c['minimum_match']) + '+ ' + ATTRIBUTES[c['attributes'][0]] + ' combos'
            elif len(c['attributes']) != c['minimum_match'] and c['minimum_rcv_multiplier'] == 1:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK when matching ' + str(c['minimum_match']) + ' ' + ATTRIBUTES[c['attributes'][0]] + ' combos, up to ' + str(
                    c['minimum_atk_multiplier'] + (len(c['attributes']) - c['minimum_match']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x at ' + str(len(c['attributes'])) + ' ' + ATTRIBUTES[c['attributes'][0]] + ' combos'
            elif c['attributes'] != [] and c['minimum_rcv_multiplier'] == 1:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK when matching ' + str(
                    c['minimum_match']) + '+ ' + ATTRIBUTES[c['attributes'][0]] + ' combos'
            elif len(c['attributes']) != c['minimum_match'] and c['minimum_rcv_multiplier'] != 1 and c['minimum_rcv_multiplier'] == c['minimum_atk_multiplier'] and c['minimum_damage_reduction'] != 0:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK & RCV and reduce damage taken by ' + str(
                    c['minimum_damage_reduction'] * 100).rstrip('0').rstrip('.') + '% when matching ' + str(c['minimum_match']) + '+ ' + ATTRIBUTES[c['attributes'][0]] + ' combos'
            elif c['attributes'] != [] and c['minimum_rcv_multiplier'] != 1 and c['minimum_rcv_multiplier'] == c['minimum_atk_multiplier']:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK & RCV when matching ' + str(
                    c['minimum_match']) + '+ ' + ATTRIBUTES[c['attributes'][0]] + ' combos'
                if len(c['attributes']) != c['minimum_match']:
                    c['skill_text'] += ' up to ' + str(c['minimum_atk_multiplier'] + (len(c['attributes']) - c['minimum_match']) * c['bonus_atk_multiplier']).rstrip(
                        '0').rstrip('.') + 'x at ' + str(len(c['attributes'])) + ' ' + ATTRIBUTES[c['attributes'][0]] + ' combos'
        else:
            if c['minimum_damage_reduction'] != 0 and c['minimum_rcv_multiplier'] == 1:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and reduce damage taken by ' + str(
                    c['minimum_damage_reduction'] * 100).rstrip('0').rstrip('.') + '% when matching '
                z = False
                for i in range(0, len(c['attributes']) - int(c['minimum_match']) + 1):
                    if i == len(c['attributes']) - int(c['minimum_match']) and i != 0:
                        c['skill_text'] += '('
                        z = True
                    for j in range(0, int(c['minimum_match'])):
                        c['skill_text'] += ATTRIBUTES[int(c['attributes'][j + i])]
                        if j != int(c['minimum_match']) - 1:
                            c['skill_text'] += ', '
                if z == True:
                    c['skill_text'] += ')'
                if c['bonus_atk_multiplier'] != 0:
                    c['skill_text'] += ' up to ' + str(c['minimum_atk_multiplier'] + (len(
                        c['attributes']) - c['minimum_match']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x when matching '
                    for i in c['attributes']:
                        c['skill_text'] += ATTRIBUTES[i]
                        if i != len(c['attributes']):
                            c['skill_text'] += ', '
            elif c['minimum_damage_reduction'] != 0 and c['minimum_rcv_multiplier'] != 1 and c['minimum_rcv_multiplier'] == c['minimum_atk_multiplier']:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK & RCV and reduce damage taken by ' + str(
                    c['minimum_damage_reduction'] * 100).rstrip('0').rstrip('.') + '% when matching '
                z = False
                for i in range(0, len(c['attributes']) - int(c['minimum_match']) + 1):
                    if i == len(c['attributes']) - int(c['minimum_match']) and i != 0:
                        c['skill_text'] += '('
                        z = True
                    for j in range(0, int(c['minimum_match'])):
                        c['skill_text'] += ATTRIBUTES[int(c['attributes'][j + i])]
                        if j != int(c['minimum_match']) - 1:
                            c['skill_text'] += ', '
                if z == True:
                    c['skill_text'] += ')'
                if c['bonus_atk_multiplier'] != 0:
                    c['skill_text'] += ' up to ' + str(c['minimum_atk_multiplier'] + (len(
                        c['attributes']) - c['minimum_match']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x when matching '
                    for i in c['attributes']:
                        c['skill_text'] += ATTRIBUTES[i]
                        if i != len(c['attributes']):
                            c['skill_text'] += ', '
            elif c['minimum_damage_reduction'] == 0 and c['minimum_rcv_multiplier'] != 1 and c['minimum_rcv_multiplier'] == c['minimum_atk_multiplier']:
                c['skill_text'] += str(c['minimum_atk_multiplier']
                                       ).rstrip('0').rstrip('.') + 'x ATK & RCV when matching '
                z = False
                for i in range(0, len(c['attributes']) - int(c['minimum_match']) + 1):
                    if i == len(c['attributes']) - int(c['minimum_match']) and i != 0:
                        c['skill_text'] += '('
                        z = True
                    for j in range(0, int(c['minimum_match'])):
                        c['skill_text'] += ATTRIBUTES[int(c['attributes'][j + i])]
                        if j != int(c['minimum_match']) - 1:
                            c['skill_text'] += ', '
                if z == True:
                    c['skill_text'] += ')'
                if c['bonus_atk_multiplier'] != 0:
                    c['skill_text'] += ' up to ' + str(c['minimum_atk_multiplier'] + (len(
                        c['attributes']) - c['minimum_match']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x when matching '
                    for i in c['attributes']:
                        c['skill_text'] += ATTRIBUTES[i]
                        if i != len(c['attributes']):
                            c['skill_text'] += ', '
            elif c['minimum_damage_reduction'] == 0 and c['minimum_rcv_multiplier'] != 1 and c['minimum_rcv_multiplier'] != c['minimum_atk_multiplier']:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and ' + str(
                    c['minimum_rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV when matching '
                z = False
                for i in range(0, len(c['attributes']) - int(c['minimum_match']) + 1):
                    if i == len(c['attributes']) - int(c['minimum_match']) and i != 0:
                        c['skill_text'] += '('
                        z = True
                    for j in range(0, int(c['minimum_match'])):
                        c['skill_text'] += ATTRIBUTES[int(c['attributes'][j + i])]
                        if j != int(c['minimum_match']) - 1:
                            c['skill_text'] += ', '
                if z == True:
                    c['skill_text'] += ')'
                if c['bonus_atk_multiplier'] != 0:
                    c['skill_text'] += ' up to ' + str(c['minimum_atk_multiplier'] + (len(
                        c['attributes']) - c['minimum_match']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x when matching '
                    for i in c['attributes']:
                        c['skill_text'] += ATTRIBUTES[i]
                        if i != len(c['attributes']):
                            c['skill_text'] += ', '
            elif c['minimum_damage_reduction'] == 0 and c['minimum_rcv_multiplier'] == 1:
                c['skill_text'] += str(c['minimum_atk_multiplier']
                                       ).rstrip('0').rstrip('.') + 'x ATK when matching '
                z = False
                for i in range(0, len(c['attributes']) - int(c['minimum_match']) + 1):
                    if i == len(c['attributes']) - int(c['minimum_match']) and i != 0:
                        c['skill_text'] += '('
                        z = True
                    for j in range(0, int(c['minimum_match'])):
                        c['skill_text'] += ATTRIBUTES[int(c['attributes'][j + i])]
                        if j != int(c['minimum_match']) - 1:
                            c['skill_text'] += ', '
                if z == True:
                    c['skill_text'] += ')'
                if c['bonus_atk_multiplier'] != 0:
                    c['skill_text'] += ' up to ' + str(c['minimum_atk_multiplier'] + (len(
                        c['attributes']) - c['minimum_match']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x when matching '
                    for i in c['attributes']:
                        c['skill_text'] += ATTRIBUTES[i]
                        if i != len(c['attributes']):
                            c['skill_text'] += ', '
        return 'multi-attribute_match', c
    return f


mass_match_backups = {'attributes': [], 'minimum_count': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                            'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                        'maximum_count': 0, 'reduction_attributes': all_attr, 'skill_text': ''}


def mass_match_convert(arguments):
    def f(x):
        _, c = convert('mass_match', {
                       k: (arguments[k] if k in arguments else v) for k, v in mass_match_backups.items()})(x)
        if c['maximum_count'] == 0:
            c['maximum_count'] = c['minimum_count']
        if c['maximum_count'] == c['minimum_count']:
            if c['minimum_damage_reduction'] != 0:
                if c['minimum_rcv_multiplier'] != 1.0 and c['minimum_rcv_multiplier'] == 'minimum_atk_multiplier':
                    c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and RCV and reduce damage taken by ' + str(
                        c['minimum_damage_reduction'] * 100).rstrip('0').rstrip('.') + '% when matching ' + str(c['minimum_count']) + '+ ' + ATTRIBUTES[c['attributes'][0]] + ' orbs'
                elif c['minimum_rcv_multiplier'] != 1.0:
                    c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and ' + str(c['minimum_rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV and reduce damage taken by ' + str(
                        c['minimum_damage_reduction'] * 100).rstrip('0').rstrip('.') + '% when matching ' + str(c['minimum_count']) + '+ ' + ATTRIBUTES[c['attributes'][0]] + ' orbs'
                else:
                    c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and reduce damage taken by ' + str(
                        c['minimum_damage_reduction'] * 100).rstrip('0').rstrip('.') + '% when matching ' + str(c['minimum_count']) + '+ ' + ATTRIBUTES[c['attributes'][0]] + ' orbs'

            else:
                if c['minimum_rcv_multiplier'] != 1.0 and c['minimum_rcv_multiplier'] == 'minimum_atk_multiplier':
                    c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip(
                        '.') + 'x ATK and RCV when matching ' + str(c['minimum_count']) + '+ ' + ATTRIBUTES[c['attributes'][0]] + ' orbs'
                elif c['attributes'] != []:
                    c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and ' + str(c['minimum_rcv_multiplier']).rstrip(
                        '0').rstrip('.') + 'x RCV when matching ' + str(c['minimum_count']) + '+ ' + ATTRIBUTES[c['attributes'][0]] + ' orbs'
        else:
            if c['minimum_rcv_multiplier'] != 1.0 and c['minimum_rcv_multiplier'] == 'minimum_atk_multiplier':
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and RCV when matching ' + str(c['minimum_count']) + '+ ' + ATTRIBUTES[c['attributes'][0]] + \
                    ' orbs up to ' + str((c['maximum_count'] - c['minimum_count']) * c['bonus_atk_multiplier'] +
                                         c['minimum_atk_multiplier']) + 'x at ' + str(c['maximum_count']) + ' orbs'
            elif c['minimum_rcv_multiplier'] != 1.0:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and ' + str(c['minimum_rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV when matching ' + str(c['minimum_count']) + \
                    '+ ' + ATTRIBUTES[c['attributes'][0]] + ' orbs up to ' + str(
                        (c['maximum_count'] - c['minimum_count']) * c['bonus_atk_multiplier'] + c['minimum_atk_multiplier']) + 'x at ' + str(c['maximum_count']) + ' orbs'
            else:
                c['skill_text'] += str(c['minimum_atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK when matching ' + str(c['minimum_count']) + '+ ' + ATTRIBUTES[c['attributes'][0]] + \
                    ' orbs up to ' + str((c['maximum_count'] - c['minimum_count']) * c['bonus_atk_multiplier'] +
                                         c['minimum_atk_multiplier']) + 'x at ' + str(c['maximum_count']) + ' orbs'
        return 'mass_match', c
    return f


after_attack_on_match_backups = {'multiplier': 0, 'skill_text': ''}


def after_attack_convert(arguments):
    def f(x):
        _, c = convert('after_attack_on_match', {
                       k: (arguments[k] if k in arguments else v) for k, v in after_attack_on_match_backups.items()})(x)
        c['skill_text'] += str(c['multiplier']).rstrip('0').rstrip('.') + \
            'x ATK additional damage when matching orbs'
        return 'after_attack_on_match', c
    return f


heal_on_match_backups = {'multiplier': 0, 'skill_text': ''}


def heal_on_convert(arguments):
    def f(x):
        _, c = convert('heal on match', {
                       k: (arguments[k] if k in arguments else v) for k, v in heal_on_match_backups.items()})(x)
        c['skill_text'] += str(c['multiplier']).rstrip('0').rstrip('.') + \
            'x RCV additional heal when matching orbs'
        return 'heal on match', c
    return f


resolve_backups = {'threshold': 0, 'skill_text': ''}


def resolve_convert(arguments):
    def f(x):
        _, c = convert('resolve', {k: (arguments[k] if k in arguments else v)
                                   for k, v in resolve_backups.items()})(x)
        c['skill_text'] += 'May survive when HP is reduced to 0 (HP>' + str(
            c['threshold'] * 100).rstrip('0').rstrip('.') + '%)'
        return 'resolve', c
    return f


bonus_move_time_backups = {'time': 0.0, 'for_attr': [], 'for_type': [
], 'hp_multiplier': 1.0, 'atk_multiplier': 1.0, 'rcv_multiplier': 1.0, 'skill_text': ''}


def bonus_time_convert(arguments):
    def f(x):
        _, c = convert('bonus_move_time', {
                       k: (arguments[k] if k in arguments else v) for k, v in bonus_move_time_backups.items()})(x)
        if not c['for_type']:
            if c['hp_multiplier'] != 1 and c['hp_multiplier'] == c['atk_multiplier'] == c['rcv_multiplier']:
                c['skill_text'] += str(c['hp_multiplier']
                                       ).rstrip('0').rstrip('.') + 'x all stats for '
                if c['for_attr'] == [0, 1, 2, 3, 4]:
                    c['skill_text'] += 'all Att.'
                else:
                    for i in c['for_attr'][:-1]:
                        c['skill_text'] += ATTRIBUTES[i] + ', '
                    c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
            elif c['hp_multiplier'] == 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] != 1:
                if c['atk_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['atk_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x ATK & RCV for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
                else:
                    c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + \
                        'x ATK and ' + str(c['rcv_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x RCV for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
            elif c['hp_multiplier'] != 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] != 1:
                if c['hp_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x HP & RCV for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
                else:
                    c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP and ' + \
                        str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
            elif c['hp_multiplier'] != 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] == 1:
                if c['atk_multiplier'] == c['hp_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x HP & ATK for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
                else:
                    c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP and ' + \
                        str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK for '
                    if c['for_attr'] == [0, 1, 2, 3, 4]:
                        c['skill_text'] += 'all Att.'
                    else:
                        for i in c['for_attr'][:-1]:
                            c['skill_text'] += ATTRIBUTES[i] + ', '
                        c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
            elif c['hp_multiplier'] == 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] != 1:
                c['skill_text'] += str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                if c['for_attr'] == [0, 1, 2, 3, 4]:
                    c['skill_text'] += 'all Att.'
                else:
                    for i in c['for_attr'][:-1]:
                        c['skill_text'] += ATTRIBUTES[i] + ', '
                    c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
            elif c['hp_multiplier'] == 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] == 1:
                c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK for '
                if c['for_attr'] == [0, 1, 2, 3, 4]:
                    c['skill_text'] += 'all Att.'
                else:
                    for i in c['for_attr'][:-1]:
                        c['skill_text'] += ATTRIBUTES[i] + ', '
                    c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
            elif c['hp_multiplier'] != 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] == 1:
                c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP for '
                if c['for_attr'] == [0, 1, 2, 3, 4]:
                    c['skill_text'] += 'all Att.'
                else:
                    for i in c['for_attr'][:-1]:
                        c['skill_text'] += ATTRIBUTES[i] + ', '
                    c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + ' Att.'
        else:
            if c['hp_multiplier'] != 1 and c['hp_multiplier'] == c['atk_multiplier'] == c['rcv_multiplier']:
                c['skill_text'] += str(c['hp_multiplier']
                                       ).rstrip('0').rstrip('.') + 'x all stats for '
                for i in c['for_type'][:-1]:
                    c['skill_text'] += TYPES[i] + ', '
                c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
            elif c['hp_multiplier'] == 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] != 1:
                if c['atk_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['atk_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x ATK & RCV for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
                else:
                    c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + \
                        'x ATK and ' + str(c['rcv_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x RCV for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
            elif c['hp_multiplier'] != 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] != 1:
                if c['hp_multiplier'] == c['rcv_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x HP & RCV for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
                else:
                    c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP and ' + \
                        str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
            elif c['hp_multiplier'] != 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] == 1:
                if c['atk_multiplier'] == c['hp_multiplier']:
                    c['skill_text'] += str(c['hp_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x HP & ATK for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
                else:
                    c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP and ' + \
                        str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK for '
                    for i in c['for_type'][:-1]:
                        c['skill_text'] += TYPES[i] + ', '
                    c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
            elif c['hp_multiplier'] == 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] != 1:
                c['skill_text'] += str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                for i in c['for_type'][:-1]:
                    c['skill_text'] += TYPES[i] + ', '
                c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
            elif c['hp_multiplier'] == 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] == 1:
                c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK for '
                for i in c['for_type'][:-1]:
                    c['skill_text'] += TYPES[i] + ', '
                c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
            elif c['hp_multiplier'] != 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] == 1:
                c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP for '
                for i in c['for_type'][:-1]:
                    c['skill_text'] += TYPES[i] + ', '
                c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
        if c['time'] != 0 and c['skill_text'] != '':
            c['skill_text'] += '; Increase orb movement time by ' + \
                str(c['time']).rstrip('0').rstrip('.') + ' seconds'
        elif c['skill_text'] == '':
            c['skill_text'] += 'Increase orb movement time by ' + \
                str(c['time']).rstrip('0').rstrip('.') + ' seconds'
        return 'bonus_move_time', c
    return f


counter_attack_backups = {'chance': 0, 'multiplier': 0, 'attribute': [], 'skill_text': ''}


def counter_attack_convert(arguments):
    def f(x):
        _, c = convert('counter_attack', {
                       k: (arguments[k] if k in arguments else v) for k, v in counter_attack_backups.items()})(x)
        if c['chance'] == 1:
            c['skill_text'] += str(c['multiplier']).rstrip('0').rstrip('.') + \
                'x ' + ATTRIBUTES[int(c['attribute'])] + ' counterattack'
        else:
            c['skill_text'] += str(c['chance'] * 100).rstrip('0').rstrip('.') + '% chance to counterattack with ' + str(
                c['multiplier']).rstrip('0').rstrip('.') + 'x ' + ATTRIBUTES[int(c['attribute'])] + ' damage'

        return 'counter_attack', c
    return f


egg_drop_backups = {'multiplier': 1.0, 'skill_text': ''}


def egg_drop_convert(arguments):
    def f(x):
        _, c = convert('egg_drop_rate', {
                       k: (arguments[k] if k in arguments else v) for k, v in egg_drop_backups.items()})(x)
        c['skill_text'] += str(c['multiplier']).rstrip('0').rstrip('.') + 'x Egg Drop rate'
        return 'egg_drop_rate', c
    return f


coin_drop_backups = {'multiplier': 1.0, 'skill_text': ''}


def coin_drop_convert(arguments):
    def f(x):
        _, c = convert('coin_drop_rate', {
                       k: (arguments[k] if k in arguments else v) for k, v in coin_drop_backups.items()})(x)
        c['skill_text'] += str(c['multiplier']).rstrip('0').rstrip('.') + 'x Coin Drop rate'
        return 'coin_drop_rate', c
    return f


skill_used_backups = {'for_attr': [], 'for_type': [],
                      'atk_multiplier': 1, 'rcv_multiplier': 1, 'skill_text': ''}


def skill_used_convert(arguments):
    def f(x):
        _, c = convert('skill_used_stats', {
                       k: (arguments[k] if k in arguments else v) for k, v in skill_used_backups.items()})(x)
        if c['for_attr'] != []:
            if c['for_attr'] == [0, 1, 2, 3, 4]:
                if c['rcv_multiplier'] != 1 and c['rcv_multiplier'] == c['atk_multiplier']:
                    c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + \
                        'x ATK & RCV on the turn a skill is used'
                elif c['rcv_multiplier'] != 1 and c['rcv_multiplier'] != c['atk_multiplier'] and c['atk_multiplier'] != 1:
                    c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and ' + str(
                        c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV on the turn a skill is used'
                elif c['rcv_multiplier'] == 1 and c['rcv_multiplier'] != c['atk_multiplier']:
                    c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + \
                        'x ATK on the turn a skill is used'
                elif c['atk_multiplier'] == 1 and c['rcv_multiplier'] != c['atk_multiplier']:
                    c['skill_text'] += str(c['rcv_multiplier']).rstrip('0').rstrip('.') + \
                        'x RCV on the turn a skill is used'
            else:
                if c['rcv_multiplier'] != 1 and c['rcv_multiplier'] == c['atk_multiplier']:
                    c['skill_text'] += str(c['atk_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x ATK & RCV for '
                    for i in c['for_attr'][:-1]:
                        c['skill_text'] += ATTRIBUTES[i] + ', '
                    c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + \
                        ' Att. on the turn a skill is used'
                elif c['rcv_multiplier'] != 1 and c['rcv_multiplier'] != c['atk_multiplier']:
                    c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + \
                        'x ATK and ' + str(c['rcv_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x RCV for '
                    for i in c['for_attr'][:-1]:
                        c['skill_text'] += ATTRIBUTES[i] + ', '
                    c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + \
                        ' Att. on the turn a skill is used'
                elif c['rcv_multiplier'] == 1 and c['rcv_multiplier'] != c['atk_multiplier']:
                    c['skill_text'] += str(c['atk_multiplier']
                                           ).rstrip('0').rstrip('.') + 'x ATK for '
                    for i in c['for_attr'][:-1]:
                        c['skill_text'] += ATTRIBUTES[i] + ', '
                    c['skill_text'] += ATTRIBUTES[int(c['for_attr'][-1])] + \
                        ' Att. on the turn a skill is used'
        elif c['for_type'] != []:
            if c['rcv_multiplier'] != 1 and c['rcv_multiplier'] == c['atk_multiplier']:
                c['skill_text'] += str(c['atk_multiplier']
                                       ).rstrip('0').rstrip('.') + 'x ATK & RCV for '
                for i in c['for_type'][:-1]:
                    c['skill_text'] += TYPES[i] + ', '
                c['skill_text'] += TYPES[int(c['for_type'][-1])] + \
                    ' type on the turn a skill is used'
            elif c['rcv_multiplier'] != 1 and c['rcv_multiplier'] != c['atk_multiplier']:
                c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + \
                    'x ATK and ' + str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                for i in c['for_type'][:-1]:
                    c['skill_text'] += TYPES[i] + ', '
                c['skill_text'] += TYPES[int(c['for_type'][-1])] + \
                    ' type on the turn a skill is used'
            elif c['rcv_multiplier'] == 1 and c['rcv_multiplier'] != c['atk_multiplier']:
                c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK for '
                for i in c['for_type'][:-1]:
                    c['skill_text'] += TYPES[i] + ', '
                c['skill_text'] += TYPES[int(c['for_type'][-1])] + \
                    ' type on the turn a skill is used'
            elif c['atk_multiplier'] == 1 and c['rcv_multiplier'] != c['atk_multiplier']:
                c['skill_text'] += str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV for '
                for i in c['for_type'][:-1]:
                    c['skill_text'] += TYPES[i] + ', '
                c['skill_text'] += TYPES[int(c['for_type'][-1])] + \
                    ' type on the turn a skill is used'
        return 'skill_used_stats', c
    return f


exact_combo_backups = {'combos': 0, 'atk_multiplier': 1, 'skill_text': ''}


def exact_combo_convert(arguments):
    def f(x):
        _, c = convert('exact_combo_match', {
                       k: (arguments[k] if k in arguments else v) for k, v in exact_combo_backups.items()})(x)
        c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + \
            'x ATK when exactly ' + str(c['combos']) + ' combos'
        return 'exact_combo_match', c
    return f


passive_stats_type_atk_all_hp_backups = {'for_type': [],
                                         'atk_multiplier': 1, 'hp_multiplier': 1, 'skill_text': ''}


def passive_stats_type_atk_all_hp_convert(arguments):
    def f(x):
        _, c = convert('passive_stats_type_atk_all_hp', {k: (
            arguments[k] if k in arguments else v) for k, v in passive_stats_type_atk_all_hp_backups.items()})(x)
        c['skill_text'] += 'Reduce total HP by ' + str((1 - c['hp_multiplier']) * 100).rstrip(
            '0').rstrip('.') + '%; ' + str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK for '
        for i in c['for_type'][:-1]:
            c['skill_text'] += TYPES[i] + ', '
        c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'
        return 'passive_stats_type_atk_all_hp', c
    return f


team_build_bonus_backups = {'monster_ids': 0, 'hp_multiplier': 1,
                            'atk_multiplier': 1, 'rcv_multiplier': 1, 'skill_text': ''}


def team_build_bonus_convert(arguments):
    def f(x):
        _, c = convert('team_build_bonus', {
                       k: (arguments[k] if k in arguments else v) for k, v in team_build_bonus_backups.items()})(x)
        if c['hp_multiplier'] != 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] != 1:
            if c['hp_multiplier'] == c['atk_multiplier'] == c['rcv_multiplier']:
                c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + \
                    'x all stats if ' + str(c['monster_ids']) + ' is on the team'
            elif c['hp_multiplier'] == c['atk_multiplier']:
                c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP & ATK and ' + str(
                    c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV if ' + str(c['monster_ids']) + ' is on the team'
            elif c['hp_multiplier'] == c['rcv_multiplier']:
                c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP & RCV and ' + str(
                    c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK if ' + str(c['monster_ids']) + ' is on the team'
            elif c['atk_multiplier'] == c['rcv_multiplier']:
                c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK & RCV and ' + str(
                    c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP if ' + str(c['monster_ids']) + ' is on the team'
        elif c['hp_multiplier'] == 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] != 1:
            if c['atk_multiplier'] == c['rcv_multiplier']:
                c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + \
                    'x ATK & RCV if ' + str(c['monster_ids']) + ' is on the team'
            else:
                c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and ' + str(
                    c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV if ' + str(c['monster_ids']) + ' is on the team'
        elif c['hp_multiplier'] != 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] != 1:
            if c['hp_multiplier'] == c['rcv_multiplier']:
                c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + \
                    'x HP & RCV if ' + str(c['monster_ids']) + ' is on the team'
            else:
                c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP and ' + str(
                    c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV if ' + str(c['monster_ids']) + ' is on the team'
        elif c['hp_multiplier'] != 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] == 1:
            if c['atk_multiplier'] == c['hp_multiplier']:
                c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + \
                    'x HP & ATK if ' + str(c['monster_ids']) + ' is on the team'
            else:
                c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + 'x HP and ' + str(
                    c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK if ' + str(c['monster_ids']) + ' is on the team'
        elif c['hp_multiplier'] == 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] != 1:
            c['skill_text'] += str(c['rcv_multiplier']).rstrip('0').rstrip('.') + \
                'x RCV if ' + str(c['monster_ids']) + ' is on the team'
        elif c['hp_multiplier'] == 1 and c['atk_multiplier'] != 1 and c['rcv_multiplier'] == 1:
            c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + \
                'x ATK if ' + str(c['monster_ids']) + ' is on the team'
        elif c['hp_multiplier'] != 1 and c['atk_multiplier'] == 1 and c['rcv_multiplier'] == 1:
            c['skill_text'] += str(c['hp_multiplier']).rstrip('0').rstrip('.') + \
                'x HP if ' + str(c['monster_ids']) + ' is on the team'
        return 'team_build_bonus', c
    return f


rank_exp_rate_backups = {'multiplier': 1, 'skill_text': ''}


def rank_exp_rate_convert(arguments):
    def f(x):
        _, c = convert('rank_exp_rate', {
                       k: (arguments[k] if k in arguments else v) for k, v in rank_exp_rate_backups.items()})(x)
        c['skill_text'] += str(c['multiplier']).rstrip('0').rstrip('.') + 'x rank EXP'
        return 'rank_exp_rate', c
    return f


heart_tpa_stats_backups = {'rcv_multiplier': 1, 'skill_text': ''}


def heart_tpa_stats_convert(arguments):
    def f(x):
        _, c = convert('heart_tpa_stats', {
                       k: (arguments[k] if k in arguments else v) for k, v in heart_tpa_stats_backups.items()})(x)
        c['skill_text'] += str(c['rcv_multiplier']).rstrip('0').rstrip('.') + \
            'x RCV when matching 4 Heal orbs'
        return 'heart_tpa_stats', c
    return f


five_orb_one_enhance_backups = {'atk_multiplier': 1, 'skill_text': ''}


def five_orb_one_enhance_convert(arguments):
    def f(x):
        _, c = convert('five_orb_one_enhance', {
                       k: (arguments[k] if k in arguments else v) for k, v in five_orb_one_enhance_backups.items()})(x)
        c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + \
            'x ATK for matched Att. when matching 5 Orbs with 1+ enhanced'
        return 'five_orb_one_enhance', c
    return f


heart_cross_backups = {'atk_multiplier': 1, 'rcv_multiplier': 1,
                       'damage_reduction': 0, 'skill_text': ''}


def heart_cross_convert(arguments):
    def f(x):
        _, c = convert('heart_cross', {
                       k: (arguments[k] if k in arguments else v) for k, v in heart_cross_backups.items()})(x)
        if c['atk_multiplier'] != 1 and c['rcv_multiplier'] != 1 and c['damage_reduction'] != 0:
            if c['atk_multiplier'] == c['rcv_multiplier']:
                c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK & RCV and reduce damage taken by ' + str(
                    c['damage_reduction'] * 100).rstrip('0').rstrip('.') + '% when matching 5 Heal orbs in a cross fromation'
            else:
                c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK, ' + str(c['rcv_multiplier']).rstrip('0').rstrip(
                    '.') + 'x RCV and reduce damage taken by ' + str(c['damage_reduction'] * 100).rstrip('0').rstrip('.') + '% when matching 5 Heal orbs in a cross fromation'
        elif c['atk_multiplier'] != 1 and c['rcv_multiplier'] == 1 and c['damage_reduction'] != 0:
            c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK and reduce damage taken by ' + str(
                c['damage_reduction'] * 100).rstrip('0').rstrip('.') + '% when matching 5 Heal orbs in a cross fromation'
        elif c['atk_multiplier'] == 1 and c['rcv_multiplier'] != 1 and c['damage_reduction'] != 0:
            c['skill_text'] += str(c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV and reduce damage taken by ' + str(
                c['damage_reduction'] * 100).rstrip('0').rstrip('.') + '% when matching 5 Heal orbs in a cross fromation'
        elif c['atk_multiplier'] != 1 and c['rcv_multiplier'] != 1 and c['damage_reduction'] == 0:
            c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + 'x ATK, ' + str(
                c['rcv_multiplier']).rstrip('0').rstrip('.') + 'x RCV when matching 5 Heal orbs in a cross fromation'
        elif c['atk_multiplier'] != 1 and c['rcv_multiplier'] == 1 and c['damage_reduction'] == 0:
            c['skill_text'] += str(c['atk_multiplier']).rstrip('0').rstrip('.') + \
                'x ATK when matching 5 Heal orbs in a cross fromation'
        elif c['atk_multiplier'] == 1 and c['rcv_multiplier'] != 1 and c['damage_reduction'] == 0:
            c['skill_text'] += str(c['rcv_multiplier']).rstrip('0').rstrip('.') + \
                'x RCV when matching 5 Heal orbs in a cross fromation'
        elif c['atk_multiplier'] == 1 and c['rcv_multiplier'] == 1 and c['damage_reduction'] != 0:
            c['skill_text'] += 'Reduce damage taken by ' + str(c['damage_reduction'] * 100).rstrip(
                '0').rstrip('.') + '% when matching 5 Heal orbs in a cross fromation'
        return 'heart_cross', c
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
    189: convert('unlock_board_path', {}),
    11: passive_stats_convert({'for_attr': (0, listify), 'atk_multiplier': (1, multi)}),
    12: after_attack_convert({'multiplier': (0, multi)}),
    13: heal_on_convert({'multiplier': (0, multi)}),
    14: resolve_convert({'threshold': (0, multi)}),
    15: bonus_time_convert({'time': (0, multi), 'skill_text': ''}),
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
    33: convert('drumming_sound', {'skill_text': 'Turn orb sound effects into Taiko noises'}),
    36: passive_stats_convert({'reduction_attributes': (slice(0, 2), list_con), 'damage_reduction': (2, multi)}),
    38: threshold_stats_convert(BELOW, {'for_attr': all_attr, 'threshold': (0, multi), 'damage_reduction': (2, multi)}),
    39: threshold_stats_convert(BELOW, {'for_attr': all_attr, 'threshold': (0, multi), 'atk_multiplier': (slice(1, 4), atk_from_slice), 'rcv_multiplier': (slice(1, 4), rcv_from_slice)}),
    40: passive_stats_convert({'for_attr': (slice(0, 2), list_con), 'atk_multiplier': (2, multi)}),
    41: counter_attack_convert({'chance': (0, multi), 'multiplier': (1, multi), 'attribute': (2, cc)}),
    43: threshold_stats_convert(ABOVE, {'for_attr': all_attr, 'threshold': (0, multi), 'damage_reduction': (2, multi)}),
    44: threshold_stats_convert(ABOVE, {'for_attr': all_attr, 'threshold': (0, multi), 'atk_multiplier': (slice(1, 4), atk_from_slice), 'rcv_multiplier': (slice(1, 4), rcv_from_slice)}),
    45: passive_stats_convert({'for_attr': (0, listify), 'hp_multiplier': (1, multi), 'atk_multiplier': (1, multi)}),
    46: passive_stats_convert({'for_attr': (slice(0, 2), list_con), 'hp_multiplier': (2, multi)}),
    48: passive_stats_convert({'for_attr': (0, listify), 'hp_multiplier': (1, multi)}),
    49: passive_stats_convert({'for_attr': (0, listify), 'rcv_multiplier': (1, multi)}),
    53: egg_drop_convert({'multiplier': (0, multi)}),
    54: coin_drop_convert({'multiplier': (0, multi)}),
    61: attribute_match_convert({'attributes': (0, binary_con), 'minimum_attributes': (1, cc), 'minimum_atk_multiplier': (2, multi), 'bonus_atk_multiplier': (3, multi)}),
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
    100: skill_used_convert({'for_attr': all_attr, 'for_type': [], 'atk_multiplier': (slice(0, 4), atk_from_slice), 'rcv_multiplier': (slice(0, 4), rcv_from_slice)}),
    101: exact_combo_convert({'combos': (0, cc), 'atk_multiplier': (1, multi)}),
    103: combo_match_convert({'for_attr': all_attr, 'minimum_combos': (0, cc), 'minimum_atk_multiplier': (slice(1, 4), atk_from_slice), 'minimum_rcv_multiplier': (slice(1, 4), rcv_from_slice), 'maximum_combos': (0, cc)}),
    104: combo_match_convert({'for_attr': (1, binary_con), 'minimum_combos': (0, cc), 'minimum_atk_multiplier': (slice(2, 5), atk_from_slice), 'minimum_rcv_multiplier': (slice(2, 5), rcv_from_slice), 'maximum_combos': (0, cc)}),
    105: passive_stats_convert({'for_attr': all_attr, 'atk_multiplier': (1, multi), 'rcv_multiplier': (0, multi)}),
    106: passive_stats_convert({'for_attr': all_attr, 'hp_multiplier': (0, multi), 'atk_multiplier': (1, multi)}),
    107: passive_stats_convert({'for_attr': all_attr, 'hp_multiplier': (0, multi)}),
    108: passive_stats_type_atk_all_hp_convert({'for_type': (1, listify), 'atk_multiplier': (2, multi), 'hp_multiplier': (0, multi)}),
    109: mass_match_convert({'attributes': (0, binary_con), 'minimum_count': (1, cc), 'minimum_atk_multiplier': (2, multi)}),
    111: passive_stats_convert({'for_attr': (slice(0, 2), list_con), 'hp_multiplier': (2, multi), 'atk_multiplier': (2, multi)}),
    114: passive_stats_convert({'for_attr': (slice(0, 2), list_con), 'hp_multiplier': (2, multi), 'atk_multiplier': (2, multi), 'rcv_multiplier': (2, multi)}),
    119: mass_match_convert({'attributes': (0, binary_con), 'minimum_count': (1, cc), 'minimum_atk_multiplier': (2, multi), 'bonus_atk_multiplier': (3, multi), 'maximum_count': (4, cc)}),
    121: passive_stats_convert({'for_attr': (0, binary_con), 'for_type': (1, binary_con), 'hp_multiplier': (2, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2)}),
    122: threshold_stats_convert(BELOW, {'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'threshold': (0, multi), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2)}),
    123: threshold_stats_convert(ABOVE, {'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'threshold': (0, multi), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2)}),
    124: multi_attribute_match_convert({'attributes': (slice(0, 5), list_binary_con), 'minimum_match': (5, cc), 'minimum_atk_multiplier': (6, multi), 'bonus_atk_multiplier': (7, multi)}),
    125: team_build_bonus_convert({'monster_ids': (slice(0, 5), list_con_pos), 'hp_multiplier': (5, multi2), 'atk_multiplier': (6, multi2), 'rcv_multiplier': (7, multi2)}),
    129: passive_stats_convert({'for_attr': (0, binary_con), 'for_type': (1, binary_con), 'hp_multiplier': (2, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2), 'reduction_attributes': (5, binary_con), 'damage_reduction': (6, multi)}),
    130: threshold_stats_convert(BELOW, {'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'threshold': (0, multi), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2), 'reduction_attributes': (5, binary_con), 'damage_reduction': (6, multi)}),
    131: threshold_stats_convert(ABOVE, {'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'threshold': (0, multi), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2), 'reduction_attributes': (5, binary_con), 'damage_reduction': (6, multi)}),
    133: skill_used_convert({'for_attr': (0, binary_con), 'for_type': (1, binary_con), 'atk_multiplier': (2, multi2), 'rcv_multiplier': (3, multi2)}),
    136: convert('dual_passive_stats', {'for_attr_1': (0, binary_con), 'for_type_1': [], 'hp_multiplier_1': (1, multi2), 'atk_multiplier_1': (2, multi2), 'rcv_multiplier_1': (3, multi2),
                                        'for_attr_2': (4, binary_con), 'for_type_2': [], 'hp_multiplier_2': (5, multi2), 'atk_multiplier_2': (6, multi2), 'rcv_multiplier_2': (7, multi2)}),
    137: convert('dual_passive_stats', {'for_attr_1': [], 'for_type_1': (0, binary_con), 'hp_multiplier_1': (1, multi2), 'atk_multiplier_1': (2, multi2), 'rcv_multiplier_1': (3, multi2),
                                        'for_attr_2': [], 'for_type_2': (4, binary_con), 'hp_multiplier_2': (5, multi2), 'atk_multiplier_2': (6, multi2), 'rcv_multiplier_2': (7, multi2)}),
    138: convert('combine_leader_skills', {'skill_ids': (slice(None), list_con)}),
    139: convert('dual_threshold_stats', {'for_attr': (0, binary_con), 'for_type': (1, binary_con),
                                          'threshold_1': (2, multi), 'above_1': (3, lambda x: not bool(x)), 'atk_multiplier_1': (4, multi), 'rcv_multiplier_1': 1.0, 'damage_reduction_1': 0.0,
                                          'threshold_2': (5, multi), 'above_2': (6, lambda x: not bool(x)), 'atk_multiplier_2': (7, multi), 'rcv_multiplier_2': 1.0, 'damage_reduction_2': 0.0}),
    148: rank_exp_rate_convert({'multiplier': (0, multi)}),
    149: heart_tpa_stats_convert({'rcv_multiplier': (0, multi)}),
    150: five_orb_one_enhance_convert({'atk_multiplier': (1, multi)}),
    151: heart_cross_convert({'atk_multiplier': (0, multi2), 'rcv_multiplier': (1, multi2), 'damage_reduction': (2, multi)}),
    155: convert('multiplayer_stats', {'for_attr': (0, binary_con), 'for_type': (1, binary_con), 'hp_multiplier': (2, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2)}),
    157: convert('color_cross', {'crosses': (slice(None), lambda x: [{'attribute': a, 'atk_multiplier': multi(d)} for a, d in zip(x[::2], x[1::2])])}),
    158: convert('minimum_match', {'minimum_match': (0, cc), 'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'hp_multiplier': (4, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (5, multi2)}),
    159: mass_match_convert({'attributes': (0, binary_con), 'minimum_count': (1, cc), 'minimum_atk_multiplier': (2, multi), 'bonus_atk_multiplier': (3, multi), 'maximum_count': (4, cc)}),
    162: convert('large_board', {'for_attr': [], 'for_type': [], 'hp_multiplier': 1.0, 'atk_multiplier': 1.0, 'rcv_multiplier': 1.0}),
    163: passive_stats_convert({'for_attr': (0, binary_con), 'for_type': (1, binary_con), 'hp_multiplier': (2, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2), 'reduction_attributes': (5, binary_con), 'damage_reduction': (6, multi),
                                'skill_text': '[No Skyfall] '}),
    164: multi_attribute_match_convert({'attributes': (slice(0, 4), list_binary_con), 'minimum_match': (4, cc), 'minimum_atk_multiplier': (5, multi), 'minimum_rcv_multiplier': (6, multi), 'bonus_atk_multiplier': (7, multi), 'bonus_rcv_multiplier': (7, multi)}),
    165: attribute_match_convert({'attributes': (0, binary_con), 'minimum_attributes': (1, cc), 'minimum_atk_multiplier': (2, multi), 'minimum_rcv_multiplier': (3, multi), 'bonus_atk_multiplier': (4, multi), 'bonus_rcv_multiplier': (5, multi),
                                  'maximum_attributes': (slice(1, 7, 6), lambda x: x[0] + x[1])}),
    166: combo_match_convert({'for_attr': all_attr, 'minimum_combos': (0, cc), 'minimum_atk_multiplier': (1, multi), 'minimum_rcv_multiplier': (2, multi), 'bonus_atk_multiplier': (3, multi), 'bonus_rcv_multiplier': (4, multi), 'maximum_combos': (5, cc)}),
    167: mass_match_convert({'attributes': (0, binary_con), 'minimum_count': (1, cc), 'minimum_atk_multiplier': (2, multi), 'minimum_rcv_multiplier': (3, multi), 'bonus_atk_multiplier': (4, multi), 'bonus_atk_multiplier': (5, multi), 'maximum_count': (6, cc)}),
    169: combo_match_convert({'for_attr': all_attr, 'minimum_combos': (0, cc), 'minimum_atk_multiplier': (1, multi), 'minimum_damage_reduction': (2, multi)}),
    170: attribute_match_convert({'attributes': (0, binary_con), 'minimum_attributes': (1, cc), 'minimum_atk_multiplier': (2, multi), 'minimum_damage_reduction': (3, multi)}),
    171: multi_attribute_match_convert({'attributes': (slice(0, 4), list_binary_con), 'minimum_match': (4, cc), 'minimum_atk_multiplier': (5, multi), 'minimum_damage_reduction': (6, multi)}),
    175: convert('collab_bonus', {'collab_id': (0, cc), 'hp_multiplier': (3, multi2), 'atk_multiplier': (4, multi2), 'rcv_multiplier': (5, multi2)}),
    177: convert('orbs_remaining', {'orb_count': (5, cc), 'atk_multiplier': (6, multi), 'bonus_atk_multiplier': (7, multi)}),
    178: convert('fixed_move_time', {'time': (0, cc), 'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'hp_multiplier': (3, multi2), 'atk_multiplier': (4, multi2), 'rcv_multiplier': (5, multi2)}),
    182: mass_match_convert({'attributes': (0, binary_con), 'minimum_count': (1, cc), 'minimum_atk_multiplier': (2, multi), 'minimum_damage_reduction': (3, multi)}),
    183: convert('dual_threshold_stats', {'for_attr': (0, binary_con), 'for_type': (1, binary_con),
                                          'threshold_1': (2, multi), 'above_1': True, 'atk_multiplier_1': (3, multi), 'rcv_multiplier_1': 1.0, 'damage_reduction_1': (4, multi),
                                          'threshold_2': (5, multi), 'above_2': False, 'atk_multiplier_2': (6, multi2), 'rcv_multiplier_2': (7, multi2), 'damage_reduction_2': 0.0}),
    185: bonus_time_convert({'time': (0, multi), 'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'hp_multiplier': (3, multi2), 'atk_multiplier': (4, multi2), 'rcv_multiplier': (5, multi2)}),
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


if __name__ == '__main__':
    pass
