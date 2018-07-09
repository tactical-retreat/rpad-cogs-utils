#  Created by CandyNinja, edited by cate and tactical_retreat
#
# Reformats pad file data into useful skill info

from collections import defaultdict
import json
from operator import itemgetter
import sys

from defaultlist import defaultlist


def make_defaultlist(fx, initial=[]):
    df = defaultlist(fx)
    df.extend(initial)
    return df


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


def fmt_mult(x):
    return str(x).rstrip('0').rstrip('.')


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
        x = make_defaultlist(int, x)

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


def fmt_multiplier_text(hp_mult, atk_mult, rcv_mult):
    if hp_mult == atk_mult and atk_mult == rcv_mult:
        if hp_mult == 1:
            return None
        return '{}x all stats'.format(fmt_mult(hp_mult))

    mults = [('HP', hp_mult), ('ATK', atk_mult), ('RCV', rcv_mult)]
    mults = list(filter(lambda x: x[1] != 1, mults))
    mults.sort(key=itemgetter(1), reverse=True)

    chunks = []
    x = 0
    while x < len(mults):
        can_check_double = x + 1 < len(mults)
        if can_check_double and mults[x][1] == mults[x + 1][1]:
            chunks.append(('{} & {}'.format(mults[x][0], mults[x + 1][0]), mults[x][1]))
            x += 2
        else:
            chunks.append((mults[x][0], mults[x][1]))
            x += 1

    output = ''
    for c in chunks:
        if len(output):
            output += ' and '
        output += '{}x {}'.format(fmt_mult(c[1]), c[0])

    return output


def passive_stats_convert(arguments):
    def f(x):
        _, c = convert('passive_stats', {
                       k: (arguments[k] if k in arguments else v) for k, v in passive_stats_backups.items()})(x)

        for_type = c['for_type']
        for_attr = c['for_attr']
        hp_mult = c['hp_multiplier']
        atk_mult = c['atk_multiplier']
        rcv_mult = c['rcv_multiplier']
        skill_text = c['skill_text']

        multiplier_text = fmt_multiplier_text(hp_mult, atk_mult, rcv_mult)
        if multiplier_text:
            skill_text += multiplier_text

            for_skill_text = ''
            if for_type:
                for_skill_text += ' ' + ', '.join([TYPES[i] for i in for_type]) + ' type'

            if for_attr:
                if for_skill_text:
                    for_skill_text += ' and'
                color_text = 'all' if len(for_attr) == 5 else ', '.join(
                    [ATTRIBUTES[i] for i in for_attr])
                for_skill_text += ' ' + color_text + ' Att.'

            if for_skill_text:
                skill_text += ' for' + for_skill_text

        if c['damage_reduction'] != 0.0:
            skill_text += '; Reduce damage taken by ' + \
                fmt_mult(c['damage_reduction'] * 100) + '%'
        c['skill_text'] = skill_text
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
            damage_reduction = c['damage_reduction']
            for_attr = c['for_attr']
            rcv_mult = c['rcv_multiplier']
            for_type = c['for_type']
            atk_mult = c['atk_multiplier']
            skill_text = c['skill_text']
            threshold = c['threshold'] * 100
            if damage_reduction == 0:
                if rcv_mult == 1.0:
                    if not for_type:
                        skill_text += fmt_mult(atk_mult) + 'x ATK '
                        if for_attr == [0, 1, 2, 3, 4]:
                            skill_text += 'when above ' + fmt_mult(threshold) + '% HP'
                        else:
                            skill_text += 'for '
                            for i in for_attr[:-1]:
                                skill_text += ATTRIBUTES[i] + ', '
                            skill_text += ATTRIBUTES[int(for_attr[-1])] + \
                                ' Att. when above ' + fmt_mult(threshold) + '% HP'
                        c['skill_text'] = skill_text
                        return 'above_threshold_stats', c
                    else:
                        skill_text += fmt_mult(atk_mult) + 'x ATK for '
                        for i in for_type[:-1]:
                            skill_text += TYPES[i] + ', '
                        skill_text += TYPES[int(for_type[-1])] + \
                            ' type when above ' + fmt_mult(threshold) + '% HP'
                        c['skill_text'] = skill_text
                        return 'above_threshold_stats', c
                else:
                    if rcv_mult == atk_mult:
                        if not for_type:
                            skill_text += fmt_mult(atk_mult) + 'x ATK & RCV '
                            if for_attr == [0, 1, 2, 3, 4]:
                                skill_text += 'when above ' + fmt_mult(threshold) + '% HP'
                            else:
                                skill_text += 'for '
                                for i in for_attr[:-1]:
                                    skill_text += ATTRIBUTES[i] + ', '
                                skill_text += ATTRIBUTES[int(for_attr[-1])] + \
                                    ' Att. when above ' + fmt_mult(threshold) + '% HP'
                            c['skill_text'] = skill_text
                            return 'above_threshold_stats', c
                        else:
                            skill_text += fmt_mult(atk_mult) + 'x ATK & RCV for '
                            for i in for_type[:-1]:
                                skill_text += TYPES[i] + ', '
                            skill_text += TYPES[int(for_type[-1])] + \
                                ' type when above ' + fmt_mult(threshold) + '% HP'
                            c['skill_text'] = skill_text
                            return 'above_threshold_stats', c
                    else:
                        if not for_type:
                            skill_text += fmt_mult(atk_mult) + 'x ATK and ' + \
                                fmt_mult(rcv_mult) + 'x RCV '
                            if for_attr == [0, 1, 2, 3, 4]:
                                skill_text += 'when above ' + fmt_mult(threshold) + '% HP'
                            else:
                                skill_text += 'for '
                                for i in for_attr[:-1]:
                                    skill_text += ATTRIBUTES[i] + ', '
                                skill_text += ATTRIBUTES[int(for_attr[-1])] + \
                                    ' Att. when above ' + fmt_mult(threshold) + '% HP'
                            c['skill_text'] = skill_text
                            return 'above_threshold_stats', c
                        else:
                            skill_text += fmt_mult(atk_mult) + 'x ATK and ' + \
                                fmt_mult(rcv_mult) + 'x RCV for '
                            for i in for_type[:-1]:
                                skill_text += TYPES[i] + ', '
                            skill_text += TYPES[int(for_type[-1])] + \
                                ' type when above ' + fmt_mult(threshold) + '% HP'
                            c['skill_text'] = skill_text
                            return 'above_threshold_stats', c
            elif atk_mult == 1.0:
                skill_text += 'Reduce damage taken by ' + str(damage_reduction * 100).rstrip(
                    '0').rstrip('.') + '% when above ' + fmt_mult(threshold) + '% HP'
                c['skill_text'] = skill_text
                return 'above_threshold_stats', c
            else:
                if not for_type:
                    skill_text += fmt_mult(atk_mult) + 'x ATK for '
                    if for_attr == [0, 1, 2, 3, 4]:
                        skill_text += 'all Att. and reduce damage taken by ' + str(damage_reduction * 100).rstrip(
                            '0').rstrip('.') + '% when above ' + fmt_mult(threshold) + '% HP'
                    else:
                        for i in for_attr[:-1]:
                            skill_text += ATTRIBUTES[i] + ', '
                        skill_text += ATTRIBUTES[int(for_attr[-1])] + ' and reduce damage taken by ' + str(damage_reduction * 100).rstrip(
                            '0').rstrip('.') + '% when above ' + fmt_mult(threshold) + '% HP'
                    c['skill_text'] = skill_text
                    return 'above_threshold_stats', c
                else:
                    skill_text += fmt_mult(atk_mult) + 'x ATK for '
                    for i in for_type[:-1]:
                        skill_text += TYPES[i] + ', '
                    skill_text += TYPES[int(for_type[-1])] + ' type when above ' + \
                        fmt_mult(threshold) + '% HP'
                    c['skill_text'] = skill_text
                    return 'above_threshold_stats', c
        else:
            _, c = convert('below_threshold_stats', {
                           k: (arguments[k] if k in arguments else v) for k, v in threshold_stats_backups.items()})(x)

            damage_reduction = c['damage_reduction']
            for_attr = c['for_attr']
            rcv_mult = c['rcv_multiplier']
            for_type = c['for_type']
            atk_mult = c['atk_multiplier']
            skill_text = c['skill_text']
            threshold = c['threshold'] * 100

            if damage_reduction == 0:
                if rcv_mult == 1.0:
                    if not for_type:
                        skill_text += fmt_mult(atk_mult) + 'x ATK '
                        if for_attr == [0, 1, 2, 3, 4]:
                            skill_text += 'when below ' + \
                                fmt_mult(threshold) + '% HP'
                        else:
                            skill_text += 'for '
                            for i in for_attr[:-1]:
                                skill_text += ATTRIBUTES[i] + ', '
                            skill_text += ATTRIBUTES[int(for_attr[-1])] + ' Att. when below ' + \
                                fmt_mult(threshold) + '% HP'
                        c['skill_text'] = skill_text
                        return 'below_threshold_stats', c
                    else:
                        skill_text += fmt_mult(atk_mult) + 'x ATK for '
                        for i in for_type[:-1]:
                            skill_text += TYPES[i] + ', '
                        skill_text += TYPES[int(for_type[-1])] + ' type when below ' + \
                            fmt_mult(threshold) + '% HP'
                        c['skill_text'] = skill_text
                        return 'below_threshold_stats', c
                else:
                    if rcv_mult == atk_mult:
                        if not for_type:
                            skill_text += fmt_mult(atk_mult) + 'x ATK & RCV '
                            if for_attr == [0, 1, 2, 3, 4]:
                                skill_text += 'when below ' + \
                                    fmt_mult(threshold) + '% HP'
                            else:
                                skill_text += 'for '
                                for i in for_attr[:-1]:
                                    skill_text += ATTRIBUTES[i] + ', '
                                skill_text += ATTRIBUTES[int(for_attr[-1])] + ' Att. when below ' + str(
                                    threshold).rstrip('0').rstrip('.') + '% HP'
                            c['skill_text'] = skill_text
                            return 'below_threshold_stats', c
                        else:
                            skill_text += fmt_mult(atk_mult) + 'x ATK & RCV for '
                            for i in for_type[:-1]:
                                skill_text += TYPES[i] + ', '
                            skill_text += TYPES[int(for_type[-1])] + ' type when below ' + \
                                fmt_mult(threshold) + '% HP'
                            c['skill_text'] = skill_text
                            return 'below_threshold_stats', c
                    else:
                        if not for_type:
                            skill_text += str(atk_mult).rstrip('0').rstrip(
                                '.') + 'x ATK and ' + fmt_mult(rcv_mult) + 'x RCV '
                            if for_attr == [0, 1, 2, 3, 4]:
                                skill_text += 'when below ' + \
                                    fmt_mult(threshold) + '% HP'
                            else:
                                skill_text += 'for '
                                for i in for_attr[:-1]:
                                    skill_text += ATTRIBUTES[i] + ', '
                                skill_text += ATTRIBUTES[int(for_attr[-1])] + \
                                    ' Att. when below ' + fmt_mult(threshold) + '% HP'
                            c['skill_text'] = skill_text
                            return 'below_threshold_stats', c
                        else:
                            skill_text += fmt_mult(atk_mult) + \
                                'x ATK and ' + fmt_mult(rcv_mult) + 'x RCV for '
                            for i in for_type[:-1]:
                                skill_text += TYPES[i] + ', '
                            skill_text += TYPES[int(for_type[-1])] + ' type when below ' + \
                                fmt_mult(threshold) + '% HP'
                            c['skill_text'] = skill_text
                            return 'below_threshold_stats', c
            elif atk_mult == 1.0:
                skill_text += 'Reduce damage taken by ' + \
                    fmt_mult(damage_reduction * 100) + \
                    '% when below ' + fmt_mult(threshold) + '% HP'
                c['skill_text'] = skill_text
                return 'below_threshold_stats', c
            else:
                if not for_type:
                    skill_text += fmt_mult(atk_mult) + 'x ATK for '
                    if for_attr == [0, 1, 2, 3, 4]:
                        skill_text += 'all Att. and reduce damage taken by ' + \
                            fmt_mult(damage_reduction * 100) + \
                            '% when below ' + fmt_mult(threshold) + '% HP'
                    else:
                        for i in for_attr[:-1]:
                            skill_text += ATTRIBUTES[i] + ', '
                        skill_text += ATTRIBUTES[int(for_attr[-1])] + ' and reduce damage taken by ' + fmt_mult(
                            damage_reduction * 100) + '% when below ' + fmt_mult(threshold) + '% HP'
                    c['skill_text'] = skill_text
                    return 'below_threshold_stats', c
                else:
                    skill_text += fmt_mult(atk_mult) + 'x ATK for '
                    for i in for_type[:-1]:
                        skill_text += TYPES[i] + ', '
                    skill_text += TYPES[int(for_type[-1])] + ' type when below ' + \
                        fmt_mult(threshold) + '% HP'
                    c['skill_text'] = skill_text
                    return 'below_threshold_stats', c
    return f


combo_match_backups = {'for_attr': [], 'for_type': [], 'minimum_combos': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                                            'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                                       'maximum_combos': 0, 'reduction_attributes': all_attr, 'skill_text': ''}


def combo_match_convert(arguments):
    def f(x):
        _, c = convert('combo_match', {
                       k: (arguments[k] if k in arguments else v) for k, v in combo_match_backups.items()})(x)
        skill_text = c['skill_text']
        max_combos = c['maximum_combos']
        min_combos = c['minimum_combos']
        if max_combos == 0:
            max_combos = min_combos
            c['maximum_combos'] = max_combos

        min_rcv_mult = c['minimum_rcv_multiplier']
        min_atk_mult = c['minimum_atk_multiplier']
        bonus_atk_mult = c['bonus_atk_multiplier']
        bonus_rcv_mult = c['bonus_rcv_multiplier']
        min_damage_reduct = c['minimum_damage_reduction']
        if min_atk_mult == min_rcv_mult and bonus_atk_mult == bonus_rcv_mult:
            skill_text = fmt_mult(min_atk_mult) + \
                'x ATK & RCV when ' + str(min_combos) + ' or more combos'
            if max_combos != min_combos:
                skill_text += ' up to ' + str(min_atk_mult + (max_combos - min_combos)
                                              * bonus_atk_mult).rstrip('0').rstrip('.') + 'x at ' + str(max_combos) + ' combos'
        elif min_damage_reduct != 0:
            skill_text = fmt_mult(min_atk_mult) + 'x ATK and reduce damage taken by ' + str(
                min_damage_reduct * 100).rstrip('0').rstrip('.') + '% when ' + str(min_combos) + ' or more combos'
        else:
            skill_text = fmt_mult(min_atk_mult) + \
                'x ATK when ' + str(min_combos) + ' or more combos'
            if max_combos != min_combos:
                skill_text += ' up to ' + str(min_atk_mult + (max_combos - min_combos)
                                              * bonus_atk_mult).rstrip('0').rstrip('.') + 'x at ' + str(max_combos) + ' combos'
        c['skill_text'] = skill_text
        return 'combo_match', c
    return f


attribute_match_backups = {'attributes': [], 'minimum_attributes': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                                      'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                             'maximum_attributes': 0, 'reduction_attributes': all_attr, 'skill_text': ''}


def attribute_match_convert(arguments):
    def f(x):
        _, c = convert('attribute_match', {
                       k: (arguments[k] if k in arguments else v) for k, v in attribute_match_backups.items()})(x)
        skill_text = c['skill_text']
        if c['maximum_attributes'] == 0:
            c['maximum_attributes'] = c['minimum_attributes']
        if c['attributes'] == [0, 1, 2, 3, 4]:
            if c['minimum_atk_multiplier'] == c['minimum_rcv_multiplier'] and c['bonus_atk_multiplier'] == c['bonus_rcv_multiplier']:
                skill_text += fmt_mult(c['minimum_atk_multiplier']) + \
                    'x ATK & RCV when matching ' + str(c['minimum_attributes']) + ' or more colors'
                if c['bonus_atk_multiplier'] != 0:
                    skill_text += ' up to ' + str(c['minimum_atk_multiplier'] + (
                        5 - c['minimum_attributes']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x at 5 colors'
            elif c['minimum_damage_reduction'] != 0:
                skill_text += fmt_mult(c['minimum_atk_multiplier']) + 'x ATK and reduce damage taken by ' + str(
                    c['minimum_damage_reduction'] * 100).rstrip('0').rstrip('.') + '% when matching ' + str(c['minimum_attributes']) + ' or more colors'
            else:
                skill_text += fmt_mult(c['minimum_atk_multiplier']) + \
                    'x ATK when matching ' + str(c['minimum_attributes']) + ' or more colors'
                if c['bonus_atk_multiplier'] != 0:
                    skill_text += ' up to ' + str(c['minimum_atk_multiplier'] + (
                        5 - c['minimum_attributes']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x at 5 colors'
        elif c['attributes'] == [0, 1, 2, 3, 4, 5]:
            if c['minimum_atk_multiplier'] == c['minimum_rcv_multiplier'] and c['bonus_atk_multiplier'] == c['bonus_rcv_multiplier']:
                skill_text += fmt_mult(c['minimum_atk_multiplier']) + 'x ATK & RCV when matching ' + str(
                    c['minimum_attributes']) + ' or more colors (' + str(c['minimum_attributes'] - 1) + '+heal)'
                if c['bonus_atk_multiplier'] != 0:
                    skill_text += ' up to ' + str(c['minimum_atk_multiplier'] + (
                        5 - c['minimum_attributes']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x at 5 colors'
            elif c['minimum_damage_reduction'] != 0:
                skill_text += fmt_mult(c['minimum_atk_multiplier']) + 'x ATK and reduce damage taken by ' + str(c['minimum_damage_reduction'] * 100).rstrip(
                    '0').rstrip('.') + '% when matching ' + str(c['minimum_attributes']) + ' or more colors (' + str(c['minimum_attributes'] - 1) + '+heal)'
            else:
                skill_text += fmt_mult(c['minimum_atk_multiplier']) + 'x ATK when matching ' + str(
                    c['minimum_attributes']) + ' or more colors (' + str(c['minimum_attributes'] - 1) + '+heal)'
                if c['bonus_atk_multiplier'] != 0:
                    skill_text += ' up to ' + str(c['minimum_atk_multiplier'] + (
                        5 - c['minimum_attributes']) * c['bonus_atk_multiplier']).rstrip('0').rstrip('.') + 'x at 5 colors'
        elif c['attributes'] != []:
            if c['minimum_atk_multiplier'] == c['minimum_rcv_multiplier']:
                skill_text += str(c['minimum_atk_multiplier']
                                  ).rstrip('0').rstrip('.') + 'x ATK & RCV when matching '
                for i in c['attributes'][:-1]:
                    skill_text += ATTRIBUTES[i] + ', '
                skill_text += ATTRIBUTES[int(c['attributes'][-1])] + ' at once'
            else:
                skill_text += str(c['minimum_atk_multiplier']
                                  ).rstrip('0').rstrip('.') + 'x ATK when matching '
                for i in c['attributes'][:-1]:
                    skill_text += ATTRIBUTES[i] + ', '
                skill_text += ATTRIBUTES[int(c['attributes'][-1])] + ' at once'
        c['skill_text'] = skill_text
        return 'attribute_match', c
    return f


multi_attribute_match_backups = {'attributes': [], 'minimum_match': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                                       'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                                   'reduction_attributes': all_attr, 'skill_text': ''}


def multi_attribute_match_convert(arguments):
    def f(x):
        _, c = convert('multi-attribute_match',
                       {k: (arguments[k] if k in arguments else v) for k, v in multi_attribute_match_backups.items()})(x)
        attributes = c['attributes']
        min_damage_reduct = c['minimum_damage_reduction']
        min_rcv_mult = c['minimum_rcv_multiplier']
        min_atk_mult = c['minimum_atk_multiplier']
        min_match = c['minimum_match']
        bonus_atk_mult = c['bonus_atk_multiplier']
        if all(x == attributes[0] for x in attributes):
            if min_damage_reduct != 0 and min_rcv_mult == 1:
                c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK and reduce damage taken by ' + str(min_damage_reduct
                                                                                                      * 100).rstrip('0').rstrip('.') + '% when matching ' + str(min_match) + '+ ' + ATTRIBUTES[attributes[0]] + ' combos'
            elif len(attributes) != min_match and min_rcv_mult == 1:
                c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK when matching ' + str(min_match) + ' ' + ATTRIBUTES[attributes[0]] + ' combos, up to ' + str(
                    min_atk_mult + (len(attributes) - min_match) * bonus_atk_mult).rstrip('0').rstrip('.') + 'x at ' + str(len(attributes)) + ' ' + ATTRIBUTES[attributes[0]] + ' combos'
            elif attributes != [] and min_rcv_mult == 1:
                c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK when matching ' + str(
                    min_match) + '+ ' + ATTRIBUTES[attributes[0]] + ' combos'
            elif len(attributes) != min_match and min_rcv_mult != 1 and min_rcv_mult == min_atk_mult and min_damage_reduct != 0:
                c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK & RCV and reduce damage taken by ' + str(
                    min_damage_reduct * 100).rstrip('0').rstrip('.') + '% when matching ' + str(min_match) + '+ ' + ATTRIBUTES[attributes[0]] + ' combos'
            elif attributes != [] and min_rcv_mult != 1 and min_rcv_mult == min_atk_mult:
                c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK & RCV when matching ' + str(
                    min_match) + '+ ' + ATTRIBUTES[attributes[0]] + ' combos'
                if len(attributes) != min_match:
                    c['skill_text'] += ' up to ' + str(min_atk_mult + (len(attributes) - min_match) * bonus_atk_mult).rstrip(
                        '0').rstrip('.') + 'x at ' + str(len(attributes)) + ' ' + ATTRIBUTES[attributes[0]] + ' combos'
        else:
            if min_damage_reduct != 0 and min_rcv_mult == 1:
                c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK and reduce damage taken by ' + str(
                    min_damage_reduct * 100).rstrip('0').rstrip('.') + '% when matching '
                z = False
                for i in range(0, len(attributes) - int(min_match) + 1):
                    if i == len(attributes) - int(min_match) and i != 0:
                        c['skill_text'] += '('
                        z = True
                    for j in range(0, int(min_match)):
                        c['skill_text'] += ATTRIBUTES[int(attributes[j + i])]
                        if j != int(min_match) - 1:
                            c['skill_text'] += ', '
                if z == True:
                    c['skill_text'] += ')'
                if bonus_atk_mult != 0:
                    c['skill_text'] += ' up to ' + str(min_atk_mult + (len(
                        attributes) - min_match) * bonus_atk_mult).rstrip('0').rstrip('.') + 'x when matching '
                    for i in attributes:
                        c['skill_text'] += ATTRIBUTES[i]
                        if i != len(attributes):
                            c['skill_text'] += ', '
            elif min_damage_reduct != 0 and min_rcv_mult != 1 and min_rcv_mult == min_atk_mult:
                c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK & RCV and reduce damage taken by ' + str(
                    min_damage_reduct * 100).rstrip('0').rstrip('.') + '% when matching '
                z = False
                for i in range(0, len(attributes) - int(min_match) + 1):
                    if i == len(attributes) - int(min_match) and i != 0:
                        c['skill_text'] += '('
                        z = True
                    for j in range(0, int(min_match)):
                        c['skill_text'] += ATTRIBUTES[int(attributes[j + i])]
                        if j != int(min_match) - 1:
                            c['skill_text'] += ', '
                if z == True:
                    c['skill_text'] += ')'
                if bonus_atk_mult != 0:
                    c['skill_text'] += ' up to ' + str(min_atk_mult + (len(
                        attributes) - min_match) * bonus_atk_mult).rstrip('0').rstrip('.') + 'x when matching '
                    for i in attributes:
                        c['skill_text'] += ATTRIBUTES[i]
                        if i != len(attributes):
                            c['skill_text'] += ', '
            elif min_damage_reduct == 0 and min_rcv_mult != 1 and min_rcv_mult == min_atk_mult:
                c['skill_text'] += str(min_atk_mult
                                       ).rstrip('0').rstrip('.') + 'x ATK & RCV when matching '
                z = False
                for i in range(0, len(attributes) - int(min_match) + 1):
                    if i == len(attributes) - int(min_match) and i != 0:
                        c['skill_text'] += '('
                        z = True
                    for j in range(0, int(min_match)):
                        c['skill_text'] += ATTRIBUTES[int(attributes[j + i])]
                        if j != int(min_match) - 1:
                            c['skill_text'] += ', '
                if z == True:
                    c['skill_text'] += ')'
                if bonus_atk_mult != 0:
                    c['skill_text'] += ' up to ' + str(min_atk_mult + (len(
                        attributes) - min_match) * bonus_atk_mult).rstrip('0').rstrip('.') + 'x when matching '
                    for i in attributes:
                        c['skill_text'] += ATTRIBUTES[i]
                        if i != len(attributes):
                            c['skill_text'] += ', '
            elif min_damage_reduct == 0 and min_rcv_mult != 1 and min_rcv_mult != min_atk_mult:
                c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK and ' + \
                    fmt_mult(min_rcv_mult) + 'x RCV when matching '
                z = False
                for i in range(0, len(attributes) - int(min_match) + 1):
                    if i == len(attributes) - int(min_match) and i != 0:
                        c['skill_text'] += '('
                        z = True
                    for j in range(0, int(min_match)):
                        c['skill_text'] += ATTRIBUTES[int(attributes[j + i])]
                        if j != int(min_match) - 1:
                            c['skill_text'] += ', '
                if z == True:
                    c['skill_text'] += ')'
                if bonus_atk_mult != 0:
                    c['skill_text'] += ' up to ' + str(min_atk_mult + (
                        len(attributes) - min_match) * bonus_atk_mult).rstrip('0').rstrip('.') + 'x when matching '
                    for i in attributes:
                        c['skill_text'] += ATTRIBUTES[i]
                        if i != len(attributes):
                            c['skill_text'] += ', '
            elif min_damage_reduct == 0 and min_rcv_mult == 1:
                c['skill_text'] += fmt_mult(min_atk_mult) + \
                    'x ATK when matching '
                z = False
                for i in range(0, len(attributes) - int(min_match) + 1):
                    if i == len(attributes) - int(min_match) and i != 0:
                        c['skill_text'] += '('
                        z = True
                    for j in range(0, int(min_match)):
                        c['skill_text'] += ATTRIBUTES[int(attributes[j + i])]
                        if j != int(min_match) - 1:
                            c['skill_text'] += ', '
                if z == True:
                    c['skill_text'] += ')'
                if bonus_atk_mult != 0:
                    c['skill_text'] += ' up to ' + str(min_atk_mult + (
                        len(attributes) - min_match) * bonus_atk_mult).rstrip('0').rstrip('.') + 'x when matching '
                    for i in attributes:
                        c['skill_text'] += ATTRIBUTES[i]
                        if i != len(attributes):
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
        max_count = c['maximum_count']
        min_count = c['minimum_count']
        if max_count == 0:
            max_count = min_count
            c['maximum_count'] = max_count

        min_damage_reduction = c['minimum_damage_reduction']
        min_rcv_mult = c['minimum_rcv_multiplier']
        min_atk_mult = c['minimum_atk_multiplier']
        attributes = c['attributes']
        bonus_atk_mult = c['bonus_atk_multiplier']

        if max_count == min_count:
            if min_damage_reduction != 0:
                if min_rcv_mult != 1.0 and min_rcv_mult == min_atk_mult:
                    c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK and RCV and reduce damage taken by ' + str(min_damage_reduction * 100).rstrip(
                        '0').rstrip('.') + '% when matching ' + str(min_count) + '+ ' + ATTRIBUTES[attributes[0]] + ' orbs'
                elif min_rcv_mult != 1.0:
                    c['skill_text'] += fmt_mult(min_atk_mult).rstrip('0').rstrip('.') + 'x ATK and ' + str(min_rcv_mult) + 'x RCV and reduce damage taken by ' + str(
                        min_damage_reduction * 100).rstrip('0').rstrip('.') + '% when matching ' + str(min_count) + '+ ' + ATTRIBUTES[attributes[0]] + ' orbs'
                else:
                    c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK and reduce damage taken by ' + str(min_damage_reduction * 100).rstrip(
                        '0').rstrip('.') + '% when matching ' + str(min_count) + '+ ' + ATTRIBUTES[attributes[0]] + ' orbs'

            else:
                if min_rcv_mult != 1.0 and min_rcv_mult == min_atk_mult:
                    c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK and RCV when matching ' + str(
                        min_count) + '+ ' + ATTRIBUTES[attributes[0]] + ' orbs'
                elif attributes != []:
                    c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK and ' + str(min_rcv_mult).rstrip('0').rstrip(
                        '.') + 'x RCV when matching ' + str(min_count) + '+ ' + ATTRIBUTES[attributes[0]] + ' orbs'
        else:
            if min_rcv_mult != 1.0 and min_rcv_mult == min_atk_mult:
                c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK and RCV when matching ' + str(min_count) + '+ ' + ATTRIBUTES[attributes[0]] + \
                    ' orbs up to ' + str((max_count - min_count) * bonus_atk_mult +
                                         min_atk_mult) + 'x at ' + str(max_count) + ' orbs'
            elif min_rcv_mult != 1.0:
                c['skill_text'] += fmt_mult(min_atk_mult).rstrip('0').rstrip('.') + 'x ATK and ' + str(min_rcv_mult) + 'x RCV when matching ' + str(min_count) + \
                    '+ ' + ATTRIBUTES[attributes[0]] + ' orbs up to ' + str(
                        (max_count - min_count) * bonus_atk_mult + min_atk_mult) + 'x at ' + str(max_count) + ' orbs'
            else:
                c['skill_text'] += fmt_mult(min_atk_mult) + 'x ATK when matching ' + str(min_count) + '+ ' + ATTRIBUTES[attributes[0]] + \
                    ' orbs up to ' + str((max_count - min_count) * bonus_atk_mult +
                                         min_atk_mult) + 'x at ' + str(max_count) + ' orbs'
        return 'mass_match', c
    return f


after_attack_on_match_backups = {'multiplier': 0, 'skill_text': ''}


def after_attack_convert(arguments):
    def f(x):
        _, c = convert('after_attack_on_match', {
                       k: (arguments[k] if k in arguments else v) for k, v in after_attack_on_match_backups.items()})(x)
        c['skill_text'] += fmt_mult(c['multiplier']) + \
            'x ATK additional damage when matching orbs'
        return 'after_attack_on_match', c
    return f


heal_on_match_backups = {'multiplier': 0, 'skill_text': ''}


def heal_on_convert(arguments):
    def f(x):
        _, c = convert('heal on match', {
                       k: (arguments[k] if k in arguments else v) for k, v in heal_on_match_backups.items()})(x)
        c['skill_text'] += fmt_mult(c['multiplier']) + \
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
        for_type = c['for_type']
        hp_mult = c['hp_multiplier']
        atk_mult = c['atk_multiplier']
        rcv_mult = c['rcv_multiplier']
        for_attr = c['for_attr']
        skill_text = c['skill_text']
        if not for_type:
            if hp_mult != 1 and hp_mult == atk_mult == rcv_mult:
                skill_text += fmt_mult(hp_mult) + 'x all stats for '
                if for_attr == [0, 1, 2, 3, 4]:
                    skill_text += 'all Att.'
                else:
                    for i in for_attr[:-1]:
                        skill_text += ATTRIBUTES[i] + ', '
                    skill_text += ATTRIBUTES[int(for_attr[-1])] + ' Att.'
            elif hp_mult == 1 and atk_mult != 1 and rcv_mult != 1:
                if atk_mult == rcv_mult:
                    skill_text += fmt_mult(atk_mult) + 'x ATK & RCV for '
                    if for_attr == [0, 1, 2, 3, 4]:
                        skill_text += 'all Att.'
                    else:
                        for i in for_attr[:-1]:
                            skill_text += ATTRIBUTES[i] + ', '
                        skill_text += ATTRIBUTES[int(for_attr[-1])] + ' Att.'
                else:
                    skill_text += fmt_mult(atk_mult) + \
                        'x ATK and ' + fmt_mult(rcv_mult) + 'x RCV for '
                    if for_attr == [0, 1, 2, 3, 4]:
                        skill_text += 'all Att.'
                    else:
                        for i in for_attr[:-1]:
                            skill_text += ATTRIBUTES[i] + ', '
                        skill_text += ATTRIBUTES[int(for_attr[-1])] + ' Att.'
            elif hp_mult != 1 and atk_mult == 1 and rcv_mult != 1:
                if hp_mult == rcv_mult:
                    skill_text += fmt_mult(hp_mult) + 'x HP & RCV for '
                    if for_attr == [0, 1, 2, 3, 4]:
                        skill_text += 'all Att.'
                    else:
                        for i in for_attr[:-1]:
                            skill_text += ATTRIBUTES[i] + ', '
                        skill_text += ATTRIBUTES[int(for_attr[-1])] + ' Att.'
                else:
                    skill_text += fmt_mult(hp_mult) + 'x HP and ' + \
                        fmt_mult(rcv_mult) + 'x RCV for '
                    if for_attr == [0, 1, 2, 3, 4]:
                        skill_text += 'all Att.'
                    else:
                        for i in for_attr[:-1]:
                            skill_text += ATTRIBUTES[i] + ', '
                        skill_text += ATTRIBUTES[int(for_attr[-1])] + ' Att.'
            elif hp_mult != 1 and atk_mult != 1 and rcv_mult == 1:
                if atk_mult == hp_mult:
                    skill_text += fmt_mult(hp_mult) + 'x HP & ATK for '
                    if for_attr == [0, 1, 2, 3, 4]:
                        skill_text += 'all Att.'
                    else:
                        for i in for_attr[:-1]:
                            skill_text += ATTRIBUTES[i] + ', '
                        skill_text += ATTRIBUTES[int(for_attr[-1])] + ' Att.'
                else:
                    skill_text += fmt_mult(hp_mult) + 'x HP and ' + \
                        fmt_mult(atk_mult) + 'x ATK for '
                    if for_attr == [0, 1, 2, 3, 4]:
                        skill_text += 'all Att.'
                    else:
                        for i in for_attr[:-1]:
                            skill_text += ATTRIBUTES[i] + ', '
                        skill_text += ATTRIBUTES[int(for_attr[-1])] + ' Att.'
            elif hp_mult == 1 and atk_mult == 1 and rcv_mult != 1:
                skill_text += fmt_mult(rcv_mult) + 'x RCV for '
                if for_attr == [0, 1, 2, 3, 4]:
                    skill_text += 'all Att.'
                else:
                    for i in for_attr[:-1]:
                        skill_text += ATTRIBUTES[i] + ', '
                    skill_text += ATTRIBUTES[int(for_attr[-1])] + ' Att.'
            elif hp_mult == 1 and atk_mult != 1 and rcv_mult == 1:
                skill_text += fmt_mult(atk_mult) + 'x ATK for '
                if for_attr == [0, 1, 2, 3, 4]:
                    skill_text += 'all Att.'
                else:
                    for i in for_attr[:-1]:
                        skill_text += ATTRIBUTES[i] + ', '
                    skill_text += ATTRIBUTES[int(for_attr[-1])] + ' Att.'
            elif hp_mult != 1 and atk_mult == 1 and rcv_mult == 1:
                skill_text += fmt_mult(hp_mult) + 'x HP for '
                if for_attr == [0, 1, 2, 3, 4]:
                    skill_text += 'all Att.'
                else:
                    for i in for_attr[:-1]:
                        skill_text += ATTRIBUTES[i] + ', '
                    skill_text += ATTRIBUTES[int(for_attr[-1])] + ' Att.'
        else:
            if hp_mult != 1 and hp_mult == atk_mult == rcv_mult:
                skill_text += str(hp_mult
                                  ).rstrip('0').rstrip('.') + 'x all stats for '
                for i in for_type[:-1]:
                    skill_text += TYPES[i] + ', '
                skill_text += TYPES[int(for_type[-1])] + ' type'
            elif hp_mult == 1 and atk_mult != 1 and rcv_mult != 1:
                if atk_mult == rcv_mult:
                    skill_text += fmt_mult(atk_mult) + 'x ATK & RCV for '
                    for i in for_type[:-1]:
                        skill_text += TYPES[i] + ', '
                    skill_text += TYPES[int(for_type[-1])] + ' type'
                else:
                    skill_text += fmt_mult(atk_mult) + \
                        'x ATK and ' + fmt_mult(rcv_mult) + 'x RCV for '
                    for i in for_type[:-1]:
                        skill_text += TYPES[i] + ', '
                    skill_text += TYPES[int(for_type[-1])] + ' type'
            elif hp_mult != 1 and atk_mult == 1 and rcv_mult != 1:
                if hp_mult == rcv_mult:
                    skill_text += fmt_mult(hp_mult) + 'x HP & RCV for '
                    for i in for_type[:-1]:
                        skill_text += TYPES[i] + ', '
                    skill_text += TYPES[int(for_type[-1])] + ' type'
                else:
                    skill_text += fmt_mult(hp_mult) + 'x HP and ' + \
                        fmt_mult(rcv_mult) + 'x RCV for '
                    for i in for_type[:-1]:
                        skill_text += TYPES[i] + ', '
                    skill_text += TYPES[int(for_type[-1])] + ' type'
            elif hp_mult != 1 and atk_mult != 1 and rcv_mult == 1:
                if atk_mult == hp_mult:
                    skill_text += fmt_mult(hp_mult) + 'x HP & ATK for '
                    for i in for_type[:-1]:
                        skill_text += TYPES[i] + ', '
                    skill_text += TYPES[int(for_type[-1])] + ' type'
                else:
                    skill_text += fmt_mult(hp_mult) + 'x HP and ' + \
                        fmt_mult(atk_mult) + 'x ATK for '
                    for i in for_type[:-1]:
                        skill_text += TYPES[i] + ', '
                    skill_text += TYPES[int(for_type[-1])] + ' type'
            elif hp_mult == 1 and atk_mult == 1 and rcv_mult != 1:
                skill_text += fmt_mult(rcv_mult) + 'x RCV for '
                for i in for_type[:-1]:
                    skill_text += TYPES[i] + ', '
                skill_text += TYPES[int(for_type[-1])] + ' type'
            elif hp_mult == 1 and atk_mult != 1 and rcv_mult == 1:
                skill_text += fmt_mult(atk_mult) + 'x ATK for '
                for i in for_type[:-1]:
                    skill_text += TYPES[i] + ', '
                skill_text += TYPES[int(for_type[-1])] + ' type'
            elif hp_mult != 1 and atk_mult == 1 and rcv_mult == 1:
                skill_text += fmt_mult(hp_mult) + 'x HP for '
                for i in for_type[:-1]:
                    skill_text += TYPES[i] + ', '
                skill_text += TYPES[int(for_type[-1])] + ' type'

        time = c['time']
        if time != 0 and skill_text != '':
            skill_text += '; Increase orb movement time by ' + \
                fmt_mult(time) + ' seconds'
        elif skill_text == '':
            skill_text += 'Increase orb movement time by ' + \
                fmt_mult(time) + ' seconds'

        c['skill_text'] = skill_text
        return 'bonus_move_time', c
    return f


counter_attack_backups = {'chance': 0, 'multiplier': 0, 'attribute': [], 'skill_text': ''}


def counter_attack_convert(arguments):
    def f(x):
        _, c = convert('counter_attack', {
                       k: (arguments[k] if k in arguments else v) for k, v in counter_attack_backups.items()})(x)
        if c['chance'] == 1:
            c['skill_text'] += fmt_mult(c['multiplier']) + \
                'x ' + ATTRIBUTES[int(c['attribute'])] + ' counterattack'
        else:
            c['skill_text'] += fmt_mult(c['chance'] * 100) + '% chance to counterattack with ' + str(
                c['multiplier']).rstrip('0').rstrip('.') + 'x ' + ATTRIBUTES[int(c['attribute'])] + ' damage'

        return 'counter_attack', c
    return f


egg_drop_backups = {'multiplier': 1.0, 'skill_text': ''}


def egg_drop_convert(arguments):
    def f(x):
        _, c = convert('egg_drop_rate', {
                       k: (arguments[k] if k in arguments else v) for k, v in egg_drop_backups.items()})(x)
        c['skill_text'] += fmt_mult(c['multiplier']) + 'x Egg Drop rate'
        return 'egg_drop_rate', c
    return f


coin_drop_backups = {'multiplier': 1.0, 'skill_text': ''}


def coin_drop_convert(arguments):
    def f(x):
        _, c = convert('coin_drop_rate', {
                       k: (arguments[k] if k in arguments else v) for k, v in coin_drop_backups.items()})(x)
        c['skill_text'] += fmt_mult(c['multiplier']) + 'x Coin Drop rate'
        return 'coin_drop_rate', c
    return f


skill_used_backups = {'for_attr': [], 'for_type': [],
                      'atk_multiplier': 1, 'rcv_multiplier': 1, 'skill_text': ''}


def skill_used_convert(arguments):
    def f(x):
        _, c = convert('skill_used_stats', {
                       k: (arguments[k] if k in arguments else v) for k, v in skill_used_backups.items()})(x)
        skill_text = c['skill_text']
        for_attr = c['for_attr']
        rcv_mult = c['rcv_multiplier']
        atk_mult = c['atk_multiplier']
        for_type = c['for_type']
        if for_attr != []:
            if for_attr == [0, 1, 2, 3, 4]:
                if rcv_mult != 1 and rcv_mult == atk_mult:
                    skill_text += fmt_mult(atk_mult) + \
                        'x ATK & RCV on the turn a skill is used'
                elif rcv_mult != 1 and rcv_mult != atk_mult and atk_mult != 1:
                    skill_text += fmt_mult(atk_mult) + 'x ATK and ' + str(
                        rcv_mult).rstrip('0').rstrip('.') + 'x RCV on the turn a skill is used'
                elif rcv_mult == 1 and rcv_mult != atk_mult:
                    skill_text += fmt_mult(atk_mult) + \
                        'x ATK on the turn a skill is used'
                elif atk_mult == 1 and rcv_mult != atk_mult:
                    skill_text += fmt_mult(rcv_mult) + \
                        'x RCV on the turn a skill is used'
            else:
                if rcv_mult != 1 and rcv_mult == atk_mult:
                    skill_text += str(atk_mult
                                      ).rstrip('0').rstrip('.') + 'x ATK & RCV for '
                    for i in for_attr[:-1]:
                        skill_text += ATTRIBUTES[i] + ', '
                    skill_text += ATTRIBUTES[int(for_attr[-1])] + \
                        ' Att. on the turn a skill is used'
                elif rcv_mult != 1 and rcv_mult != atk_mult:
                    skill_text += fmt_mult(atk_mult) + \
                        'x ATK and ' + str(rcv_mult
                                           ).rstrip('0').rstrip('.') + 'x RCV for '
                    for i in for_attr[:-1]:
                        skill_text += ATTRIBUTES[i] + ', '
                    skill_text += ATTRIBUTES[int(for_attr[-1])] + \
                        ' Att. on the turn a skill is used'
                elif rcv_mult == 1 and rcv_mult != atk_mult:
                    skill_text += str(atk_mult
                                      ).rstrip('0').rstrip('.') + 'x ATK for '
                    for i in for_attr[:-1]:
                        skill_text += ATTRIBUTES[i] + ', '
                    skill_text += ATTRIBUTES[int(for_attr[-1])] + \
                        ' Att. on the turn a skill is used'
        elif for_type != []:
            if rcv_mult != 1 and rcv_mult == atk_mult:
                skill_text += fmt_mult(atk_mult) + 'x ATK & RCV for '
                for i in for_type[:-1]:
                    skill_text += TYPES[i] + ', '
                skill_text += TYPES[int(for_type[-1])] + \
                    ' type on the turn a skill is used'
            elif rcv_mult != 1 and rcv_mult != atk_mult:
                skill_text += fmt_mult(atk_mult) + \
                    'x ATK and ' + fmt_mult(rcv_mult) + 'x RCV for '
                for i in for_type[:-1]:
                    skill_text += TYPES[i] + ', '
                skill_text += TYPES[int(for_type[-1])] + \
                    ' type on the turn a skill is used'
            elif rcv_mult == 1 and rcv_mult != atk_mult:
                skill_text += fmt_mult(atk_mult) + 'x ATK for '
                for i in for_type[:-1]:
                    skill_text += TYPES[i] + ', '
                skill_text += TYPES[int(for_type[-1])] + \
                    ' type on the turn a skill is used'
            elif atk_mult == 1 and rcv_mult != atk_mult:
                skill_text += fmt_mult(rcv_mult) + 'x RCV for '
                for i in for_type[:-1]:
                    skill_text += TYPES[i] + ', '
                skill_text += TYPES[int(for_type[-1])] + \
                    ' type on the turn a skill is used'
        c['skill_text'] = skill_text
        return 'skill_used_stats', c
    return f


exact_combo_backups = {'combos': 0, 'atk_multiplier': 1, 'skill_text': ''}


def exact_combo_convert(arguments):
    def f(x):
        _, c = convert('exact_combo_match', {
                       k: (arguments[k] if k in arguments else v) for k, v in exact_combo_backups.items()})(x)
        c['skill_text'] += fmt_mult(c['atk_multiplier']) + \
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
            '0').rstrip('.') + '%; ' + fmt_mult(c['atk_multiplier']) + 'x ATK for '
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
        hp_multiplier = c['hp_multiplier']
        atk_multiplier = c['atk_multiplier']
        rcv_multiplier = c['rcv_multiplier']
        monster_ids = str(c['monster_ids'])

        if hp_multiplier != 1 and atk_multiplier != 1 and rcv_multiplier != 1:
            if hp_multiplier == atk_multiplier == rcv_multiplier:
                c['skill_text'] += fmt_mult(hp_multiplier) + \
                    'x all stats if ' + monster_ids + ' is on the team'
            elif hp_multiplier == atk_multiplier:
                c['skill_text'] += fmt_mult(hp_multiplier) + 'x HP & ATK and ' + fmt_mult(
                    rcv_multiplier) + 'x RCV if ' + monster_ids + ' is on the team'
            elif hp_multiplier == rcv_multiplier:
                c['skill_text'] += fmt_mult(hp_multiplier) + 'x HP & RCV and ' + fmt_mult(
                    atk_multiplier) + 'x ATK if ' + monster_ids + ' is on the team'
            elif atk_multiplier == rcv_multiplier:
                c['skill_text'] += fmt_mult(atk_multiplier) + 'x ATK & RCV and ' + fmt_mult(
                    hp_multiplier) + 'x HP if ' + monster_ids + ' is on the team'
        elif hp_multiplier == 1 and atk_multiplier != 1 and rcv_multiplier != 1:
            if atk_multiplier == rcv_multiplier:
                c['skill_text'] += fmt_mult(atk_multiplier) + \
                    'x ATK & RCV if ' + monster_ids + ' is on the team'
            else:
                c['skill_text'] += fmt_mult(atk_multiplier) + 'x ATK and ' + fmt_mult(
                    rcv_multiplier) + 'x RCV if ' + monster_ids + ' is on the team'
        elif hp_multiplier != 1 and atk_multiplier == 1 and rcv_multiplier != 1:
            if hp_multiplier == rcv_multiplier:
                c['skill_text'] += fmt_mult(hp_multiplier) + \
                    'x HP & RCV if ' + monster_ids + ' is on the team'
            else:
                c['skill_text'] += fmt_mult(hp_multiplier) + 'x HP and ' + str(
                    rcv_multiplier).rstrip('0').rstrip('.') + 'x RCV if ' + monster_ids + ' is on the team'
        elif hp_multiplier != 1 and atk_multiplier != 1 and rcv_multiplier == 1:
            if atk_multiplier == hp_multiplier:
                c['skill_text'] += fmt_mult(hp_multiplier) + \
                    'x HP & ATK if ' + monster_ids + ' is on the team'
            else:
                c['skill_text'] += fmt_mult(hp_multiplier) + 'x HP and ' + str(
                    atk_multiplier).rstrip('0').rstrip('.') + 'x ATK if ' + monster_ids + ' is on the team'
        elif hp_multiplier == 1 and atk_multiplier == 1 and rcv_multiplier != 1:
            c['skill_text'] += fmt_mult(rcv_multiplier) + \
                'x RCV if ' + monster_ids + ' is on the team'
        elif hp_multiplier == 1 and atk_multiplier != 1 and rcv_multiplier == 1:
            c['skill_text'] += fmt_mult(atk_multiplier) + \
                'x ATK if ' + monster_ids + ' is on the team'
        elif hp_multiplier != 1 and atk_multiplier == 1 and rcv_multiplier == 1:
            c['skill_text'] += fmt_mult(hp_multiplier) + \
                'x HP if ' + monster_ids + ' is on the team'
        return 'team_build_bonus', c
    return f


rank_exp_rate_backups = {'multiplier': 1, 'skill_text': ''}


def rank_exp_rate_convert(arguments):
    def f(x):
        _, c = convert('rank_exp_rate', {
                       k: (arguments[k] if k in arguments else v) for k, v in rank_exp_rate_backups.items()})(x)
        c['skill_text'] += fmt_mult(c['multiplier']) + 'x rank EXP'
        return 'rank_exp_rate', c
    return f


heart_tpa_stats_backups = {'rcv_multiplier': 1, 'skill_text': ''}


def heart_tpa_stats_convert(arguments):
    def f(x):
        _, c = convert('heart_tpa_stats', {
                       k: (arguments[k] if k in arguments else v) for k, v in heart_tpa_stats_backups.items()})(x)
        c['skill_text'] += fmt_mult(c['rcv_multiplier']) + \
            'x RCV when matching 4 Heal orbs'
        return 'heart_tpa_stats', c
    return f


five_orb_one_enhance_backups = {'atk_multiplier': 1, 'skill_text': ''}


def five_orb_one_enhance_convert(arguments):
    def f(x):
        _, c = convert('five_orb_one_enhance', {
                       k: (arguments[k] if k in arguments else v) for k, v in five_orb_one_enhance_backups.items()})(x)
        c['skill_text'] += fmt_mult(c['atk_multiplier']) + \
            'x ATK for matched Att. when matching 5 Orbs with 1+ enhanced'
        return 'five_orb_one_enhance', c
    return f


heart_cross_backups = {'atk_multiplier': 1, 'rcv_multiplier': 1,
                       'damage_reduction': 0, 'skill_text': ''}


def heart_cross_convert(arguments):
    def f(x):
        _, c = convert('heart_cross', {
                       k: (arguments[k] if k in arguments else v) for k, v in heart_cross_backups.items()})(x)
        atk_mult = c['atk_multiplier']
        atk_mult_str = fmt_mult(atk_mult)
        rcv_mult = c['rcv_multiplier']
        rcv_mult_str = fmt_mult(rcv_mult)
        skill_text = c['skill_text']
        damage_reduct = c['damage_reduction']
        damage_reduct_str = fmt_mult(damage_reduct * 100)

        cross_cond_str = 'when matching 5 Heal orbs in a cross fromation'
        if atk_mult != 1 and rcv_mult != 1 and damage_reduct != 0:
            if atk_mult == rcv_mult:
                skill_text += atk_mult_str + 'x ATK & RCV and reduce damage taken by ' + \
                    damage_reduct_str + '% ' + cross_cond_str
            else:
                skill_text += atk_mult_str + 'x ATK, ' + rcv_mult_str + 'x RCV and reduce damage taken by ' + \
                    damage_reduct_str + '% ' + cross_cond_str
        elif atk_mult != 1 and rcv_mult == 1 and damage_reduct != 0:
            skill_text += atk_mult_str + 'x ATK and reduce damage taken by ' + \
                damage_reduct_str + '% ' + cross_cond_str
        elif atk_mult == 1 and rcv_mult != 1 and damage_reduct != 0:
            skill_text += rcv_mult_str + 'x RCV and reduce damage taken by ' + \
                damage_reduct_str + '% ' + cross_cond_str
        elif atk_mult != 1 and rcv_mult != 1 and damage_reduct == 0:
            skill_text += atk_mult_str + 'x ATK, ' + rcv_mult_str + \
                'x RCV ' + cross_cond_str
        elif atk_mult != 1 and rcv_mult == 1 and damage_reduct == 0:
            skill_text += atk_mult_str + \
                'x ATK ' + cross_cond_str
        elif atk_mult == 1 and rcv_mult != 1 and damage_reduct == 0:
            skill_text += rcv_mult_str + \
                'x RCV ' + cross_cond_str
        elif atk_mult == 1 and rcv_mult == 1 and damage_reduct != 0:
            skill_text += 'Reduce damage taken by ' + damage_reduct_str + \
                '% ' + cross_cond_str
        c['skill_text'] = skill_text
        return 'heart_cross', c
    return f


SKILL_TRANSFORM = {
    0: lambda x:
    convert('null_skill', {})(x)
    if make_defaultlist(int, x)[1] == 0 else
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
    if make_defaultlist(int, x)[1] == 5 else
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
    if make_defaultlist(int, x)[4] == 1 else
    (convert('awakening_attack_boost', {'duration': (0, cc), 'awakenings': (slice(1, 4), list_con), 'amount_per': (5, lambda x: (x - 100) / 100)})(x)
        if make_defaultlist(int, x)[4] == 2 else
     (convert('awakening_shield', {'duration': (0, cc), 'awakenings': (slice(1, 4), list_con), 'amount_per': (5, multi)})(x)
      if make_defaultlist(int, x)[4] == 3 else
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


def reformat(in_file_name, out_file_name):
    print('-- Parsing skills --\n')
    with open(in_file_name) as f:
        skill_data = json.load(f)
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

    with open(out_file_name, 'w') as f:
        json.dump(reformatted, f, sort_keys=True, indent=4)
    print('Result saved\n')
    print('-- End skills --\n')


if __name__ == '__main__':
    reformat(sys.argv[1], sys.argv[2])
    pass
