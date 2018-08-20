#  Created by CandyNinja, edited by cate and tactical_retreat
#
# Reformats pad file data into useful skill info

from collections import defaultdict
import json
from operator import itemgetter
import sys

from defaultlist import defaultlist

from ..common.padguide_values import AWAKENING_MAP

def make_defaultlist(fx, initial=[]):
    df = defaultlist(fx)
    df.extend(initial)
    return df

# this is used to name the skill ids and their arguments
def cc(x): return x


def ccf(x): return float(x)


def multi(x): return x / 100


def multi2(x): return x / 100 if x != 0 else 1.0


def listify(x): return [x]


def list_con(x): return list(x)


def list_con_pos(x): return [i for i in x if i > 0]


def binary_con(x): return [i for i, v in enumerate(str(bin(x))[:1:-1]) if v == '1']


def list_binary_con(x): return [b for i in x for b in binary_con(i)]


def atk_from_slice(x): return multi(x[2]) if 1 in x[:2] else 1.0


def rcv_from_slice(x): return multi(x[2]) if 2 in x[:2] else 1.0


def fmt_mult(x):
    return str(round(float(x), 2)).rstrip('0').rstrip('.')


all_attr = [0, 1, 2, 3, 4]

ATTRIBUTES = {0: 'Fire',
              1: 'Water',
              2: 'Wood',
              3: 'Light',
              4: 'Dark',
              5: 'Heal',
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

def convert_with_defaults(type_name, args, defaults):
    new_args = {k: (args[k] if k in args else v) for k, v in defaults.items()}
    return convert(type_name, new_args)


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


def fmt_reduct_text(damage_reduct, reduct_att=[0, 1, 2, 3, 4]):
    if damage_reduct != 0:
        text = ''
        if reduct_att == [0, 1, 2, 3, 4]:
            text += 'reduce damage taken by {}%'.format(fmt_mult(damage_reduct * 100))
            return text
        else:
            color_text = ', '.join([ATTRIBUTES[i] for i in reduct_att])
            text += 'reduce damage taken from ' + color_text + \
                ' Att. by {}%'.format(fmt_mult(damage_reduct * 100))
            return text
    else:
        return None


def fmt_stats_type_attr_bonus(c, reduce_join_txt='; ', skip_attr_all=False):
    for_type = c.get('for_type', [])
    for_attr = c.get('for_attr', [])
    hp_mult = c.get('hp_multiplier', 1)
    atk_mult = c.get('atk_multiplier', c.get('minimum_atk_multiplier', 1))
    rcv_mult = c.get('rcv_multiplier', c.get('minimum_rcv_multiplier', 1))
    damage_reduct = c.get('damage_reduction', c.get('minimum_damage_reduction', 0))
    reduct_att = c.get('reduction_attributes', [])
    skill_text = ''

    multiplier_text = fmt_multiplier_text(hp_mult, atk_mult, rcv_mult)
    if multiplier_text:
        skill_text += multiplier_text

        for_skill_text = ''
        if for_type:
            for_skill_text += ' ' + ', '.join([TYPES[i] for i in for_type]) + ' type'

        if for_attr and not (skip_attr_all and len(for_attr) == 5):
            if for_skill_text:
                for_skill_text += ' and'
            color_text = 'all' if len(for_attr) == 5 else ', '.join(
                [ATTRIBUTES[i] for i in for_attr])
            for_skill_text += ' ' + color_text + ' Att.'

        if for_skill_text:
            skill_text += ' for' + for_skill_text

    reduct_text = fmt_reduct_text(damage_reduct, reduct_att)
    if reduct_text:
        if multiplier_text:
            skill_text += reduce_join_txt
        if not skill_text or ';' in reduce_join_txt:
            reduct_text = reduct_text.capitalize()
        skill_text += reduct_text

    return skill_text


# Active skill

def fmt_mass_atk(mass_attack):
    if mass_attack:
        return 'all enemies'
    else:
        return 'an enemy'


def fmt_duration(duration):
    if duration > 1:
        return 'For ' + str(duration) + ' turns, '
    else:
        return 'For ' + str(duration) + ' turn, '


attr_nuke_convert_backups = {'attribute': 0,
                             'multiplier': 1,
                             'mass_attack': False,
                             'skill_text': ''}


def attr_nuke_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('attack_attr_x_atk',
                                     arguments,
                                     attr_nuke_convert_backups)(x)
        c['skill_text'] += 'Deal ' + fmt_mult(c['multiplier']) + 'x ATK ' + ATTRIBUTES[int(
            c['attribute'])] + ' damage to ' + fmt_mass_atk(c['mass_attack'])
        return 'attack_attr_x_atk', c
    return f


fixed_attr_nuke_convert_backups = {'attribute': 0,
                                   'damage': 1,
                                   'mass_attack': False,
                                   'skill_text': ''}


def fixed_attr_nuke_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('attack_attr_damage',
                                     arguments,
                                     fixed_attr_nuke_convert_backups)(x)
        c['skill_text'] += 'Deal ' + str(c['damage']) + ' ' + ATTRIBUTES[int(
            c['attribute'])] + ' damage to ' + fmt_mass_atk(c['mass_attack'])
        return 'attack_attr_damage', c
    return f


self_att_nuke_convert_backups = {'multiplier': 1,
                                 'mass_attack': False,
                                 'skill_text': ''}


def self_att_nuke_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('attack_x_atk',
                                     arguments,
                                     self_att_nuke_convert_backups)(x)
        c['skill_text'] += 'Deal ' + fmt_mult(c['multiplier']) + \
            'x ATK damage to ' + fmt_mass_atk(c['mass_attack'])
        return 'attack_x_atk', c
    return f


shield_convert_backups = {'duration': 1,
                          'reduction': 0,
                          'skill_text': ''}


def shield_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('damage_shield_buff',
                                     arguments,
                                     shield_convert_backups)(x)
        c['skill_text'] += fmt_duration(c['duration']) + fmt_reduct_text(c['reduction'])
        return 'damage_shield_buff', c
    return f


elemental_shield_backups = {'duration': 0,
                            'attribute': 0,
                            'reduction': 0,
                            'skill_text': ''}


def elemental_shield_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('elemental_shield',
                                     arguments,
                                     elemental_shield_backups)(x)
        c['skill_text'] += fmt_duration(c['duration'])
        if c['reduction'] == 1:
            c['skill_text'] += 'void all ' + ATTRIBUTES[int(c['attribute'])] + ' damage'
        else:
            c['skill_text'] += 'reduce ' + \
                ATTRIBUTES[int(c['attribute'])] + ' damage by ' + \
                fmt_mult(c['reduction'] * 100) + '%'
        return 'elemental_shield', c
    return f


drain_attack_backups = {'atk_multiplier': 0,
                        'recover_multiplier': 0,
                        'mass_attack': False,
                        'skill_text': ''}


def drain_attack_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('drain_attack',
                                     arguments,
                                     drain_attack_backups)(x)
        c['skill_text'] += 'Deal ' + \
            fmt_mult(c['atk_multiplier']) + 'x ATK damage to ' + fmt_mass_atk(c['mass_attack'])
        if c['recover_multiplier'] == 1:
            c['skill_text'] += ' and recover the same amount as HP'
        else:
            c['skill_text'] += ' and recover ' + \
                fmt_mult(c['recover_multiplier'] * 100) + '% of the damage as HP'
        return 'drain_attack', c
    return f


poison_convert_backups = {'multiplier': 1,
                          'skill_text': ''}


def poison_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('poison',
                                     arguments,
                                     poison_convert_backups)(x)
        c['skill_text'] += 'Poison all enemies (' + fmt_mult(c['multiplier']) + 'x ATK)'
        return 'poison', c
    return f


ctw_convert_backups = {'duration': 0,
                       'skill_text': ''}


def ctw_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('change_the_world',
                                     arguments,
                                     ctw_convert_backups)(x)
        c['skill_text'] += 'Freely move orbs for ' + str(c['duration']) + ' seconds'
        return 'change_the_world', c
    return f


gravity_convert_backups = {'percentage_hp': 0,
                           'skill_text': ''}


def gravity_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('gravity',
                                     arguments,
                                     gravity_convert_backups)(x)
        c['skill_text'] += 'Reduce enemies\' HP by ' + fmt_mult(c['percentage_hp'] * 100) + '%'
        return 'gravity', c
    return f


heal_active_convert_backups = {'hp': 0,
                               'rcv_multiplier_as_hp': 0,
                               'card_bind': 0,
                               'percentage_max_hp': 0,
                               'awoken_bind': 0,
                               'team_rcv_multiplier_as_hp': 0,
                               'skill_text': ''}


def heal_active_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('heal_active',
                                     arguments,
                                     heal_active_convert_backups)(x)
        rcv_mult = c['rcv_multiplier_as_hp']
        php = c['percentage_max_hp']
        trcv_mult = c['team_rcv_multiplier_as_hp']

        if c['hp'] != 0:
            c['skill_text'] += 'Recover ' + str(c['hp']) + ' HP'
        elif rcv_mult != 0:
            c['skill_text'] += 'Recover ' + fmt_mult(rcv_mult) + 'x RCV as HP'
        elif php != 0:
            if php == 1:
                c['skill_text'] += 'Recover all HP'
            else:
                c['skill_text'] += 'Recover ' + fmt_mult(php * 100) + '% of max HP'
        elif trcv_mult != 0:
            c['skill_text'] += 'Recover HP equal to ' + fmt_mult(trcv_mult) + 'x team\'s total RCV'
        if c['card_bind'] != 0 and c['awoken_bind'] != 0:
            if c['skill_text'] != '':
                c['skill_text'] += '; '
            if c['card_bind'] == 9999:
                c['skill_text'] += 'Remove all binds and awoken skill binds'
            else:
                c['skill_text'] += 'Reduce binds and awoken skill binds by ' + \
                    str(c['card_bind']) + ' turns'
        elif c['card_bind'] == 0 and c['awoken_bind'] != 0:
            if c['skill_text'] != '':
                c['skill_text'] += '; '
            if c['awoken_bind'] == 9999:
                c['skill_text'] += 'Remove all awoken skill binds'
            else:
                c['skill_text'] += 'Reduce awoken skill binds by ' + \
                    str(c['awoken_bind']) + ' turns'
        elif c['awoken_bind'] == 0 and c['card_bind'] != 0:
            if c['skill_text'] != '':
                c['skill_text'] += '; '
            if c['card_bind'] == 9999:
                c['skill_text'] += 'Remove all binds'
            else:
                c['skill_text'] += 'Reduce binds by ' + str(c['card_bind']) + ' turns'
        return 'heal_active', c
    return f


single_orb_change_convert_backups = {'from': 0,
                                     'to': 0,
                                     'skill_text': ''}


def single_orb_change_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('single_orb_convert',
                                     arguments,
                                     single_orb_change_convert_backups)(x)
        c['skill_text'] += 'Change ' + \
            ATTRIBUTES[int(c['from'])] + ' orbs to ' + ATTRIBUTES[int(c['to'])] + ' orbs'
        return 'single_orb_convert', c
    return f


delay_convert_backups = {'turns': 0,
                         'skill_text': ''}


def delay_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('delay_convert',
                                     arguments,
                                     delay_convert_backups)(x)
        c['skill_text'] += 'Delay enemies for ' + str(c['turns']) + ' turns'
        return 'delay_convert', c
    return f


defense_reduction_convert_backups = {'duration': 0,
                                     'reduction': 0,
                                     'skill_text': ''}


def defense_reduction_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('defense_reduction',
                                     arguments,
                                     defense_reduction_convert_backups)(x)
        c['skill_text'] += fmt_duration(c['duration']) + \
            'reduce enemies\' defense by ' + fmt_mult(c['reduction'] * 100) + '%'
        return 'defense_reduction', c
    return f


double_orb_convert_backups = {'from_1': 0,
                              'to_1': 0,
                              'from_2': 0,
                              'to_2': 0,
                              'skill_text': ''}


def double_orb_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('double_orb_convert',
                                     arguments,
                                     double_orb_convert_backups)(x)
        if c['to_1'] == c['to_2']:
            c['skill_text'] += 'Change ' + ATTRIBUTES[int(c['from_1'])] + ' orbs and ' + ATTRIBUTES[int(
                c['from_2'])] + ' orbs to ' + ATTRIBUTES[int(c['to_1'])] + ' orbs'
        else:
            c['skill_text'] += 'Change ' + \
                ATTRIBUTES[int(c['from_1'])] + ' orbs to ' + ATTRIBUTES[int(c['to_1'])] + ' orbs'
            c['skill_text'] += ' and change ' + \
                ATTRIBUTES[int(c['from_2'])] + ' orbs to ' + ATTRIBUTES[int(c['to_2'])] + ' orbs'
        return 'double_orb_convert', c
    return f


damage_to_att_enemy_backups = {'enemy_attribute': 0,
                               'attack_attribute': 0,
                               'damage': 0,
                               'skill_text': ''}


def damage_to_att_enemy_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('damage_to_att_enemy',
                                     arguments,
                                     damage_to_att_enemy_backups)(x)
        c['skill_text'] += 'Deal ' + str(c['damage']) + ' ' + ATTRIBUTES[int(
            c['attack_attribute'])] + ' damage to all ' + ATTRIBUTES[int(c['enemy_attribute'])] + ' Att. enemies'
        return 'damage_to_att_enemy', c
    return f


rcv_boost_backups = {'duration': 0,
                     'multiplier': 1,
                     'skill_text': ''}


def rcv_boost_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('rcv_boost',
                                     arguments,
                                     rcv_boost_backups)(x)
        c['skill_text'] += fmt_duration(c['duration']) + fmt_mult(c['multiplier']) + 'x RCV'
        return 'rcv_boost', c
    return f


attribute_attack_boost_backups = {'duration': 0,
                                  'for_attr': 0,
                                  'atk_multiplier': 0,
                                  'skill_text': ''}


def attribute_attack_boost_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('attribute_attack_boost',
                                     arguments,
                                     attribute_attack_boost_backups)(x)
        skill_text = ''
        if 5 in c['for_attr']:
            c['for_attr'].remove(5)
            skill_text += fmt_duration(c['duration']) + fmt_mult(c['atk_multiplier']) + 'x RCV'
        if skill_text:
            skill_text += '; '
        skill_text += fmt_duration(c['duration']) + fmt_stats_type_attr_bonus(c)
        c['skill_text'] += skill_text
        return 'attribute_attack_boost', c
    return f


mass_attack_backups = {'duration': 0,
                       'skill_text': ''}


def mass_attack_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('mass_attack_buff',
                                     arguments,
                                     mass_attack_backups)(x)
        c['skill_text'] += fmt_duration(c['duration']) + 'all attacks become mass attack'
        return 'mass_attack_buff', c
    return f


enhance_backups = {'orbs': [],
                   'skill_text': ''}


def enhance_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('enhance_orbs',
                                     arguments,
                                     enhance_backups)(x)
        for_attr = c['orbs']
        for_skill_text = ''

        if for_attr:
            if not len(for_attr) == 6:
                color_text = 'all' if len(for_attr) == 5 else ', '.join(
                    [ATTRIBUTES[i] for i in for_attr])
                for_skill_text += ' ' + color_text
                c['skill_text'] += 'Enhance all' + for_skill_text + ' orbs'
            else:
                c['skill_text'] += 'Enhance all orbs'
        return 'enhance_orbs', c
    return f


lock_backups = {'orbs': [],
                'skill_text': ''}


def lock_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('lock_orbs',
                                     arguments,
                                     lock_backups)(x)
        for_attr = c['orbs']
        for_skill_text = ''

        if for_attr:
            color_text = 'all' if len(for_attr) == 10 else ', '.join(
                [ATTRIBUTES[i] for i in for_attr])
            for_skill_text += ' ' + color_text
            c['skill_text'] += 'Lock all' + for_skill_text + ' orbs'
        return 'lock_orbs', c
    return f


laser_backups = {'damage': 0,
                 'mass_attack': False,
                 'skill_text': ''}


def laser_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('laser',
                                     arguments,
                                     laser_backups)(x)
        c['skill_text'] += 'Deal ' + str(c['damage']) + \
            ' fixed damage to ' + fmt_mass_atk(c['mass_attack'])
        return 'laser', c
    return f


no_skyfall_backups = {'duration': 0,
                      'skill_text': ''}


def no_skyfall_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('no_skyfall_buff',
                                     arguments,
                                     no_skyfall_backups)(x)
        c['skill_text'] += fmt_duration(c['duration']) + 'no skyfall'
        return 'no_skyfall_buff', c
    return f


enhance_skyfall_backups = {'duration': 0,
                           'percentage_increase': 0,
                           'skill_text': ''}


def enhance_skyfall_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('enhance_skyfall_buff',
                                     arguments,
                                     enhance_skyfall_backups)(x)
        c['skill_text'] += fmt_duration(c['duration']) + 'enhanced orbs are more likely to appear by ' + \
            fmt_mult(c['percentage_increase'] * 100) + '%'
        return 'enhance_skyfall_buff', c
    return f


auto_heal_backups = {'duration': 0,
                     'percentage_max_hp': 0,
                     'unbind': 0,
                     'awoken_unbind': 0,
                     'skill_text': ''}


def auto_heal_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('auto_heal',
                                     arguments,
                                     auto_heal_backups)(x)
        skill_text = ''
        if c['duration']:
            skill_text += fmt_duration(c['duration']) + 'recover ' + \
                fmt_mult(c['percentage_max_hp'] * 100) + '% of max HP'
        
        if c['unbind'] and c['awoken_unbind'] and skill_text:
            skill_text += '; Reduce binds and awoken skill binds by {} turns'.format(c['unbind'])
        elif c['unbind'] and c['awoken_unbind']:
            skill_text += 'Reduce binds and awoken skill binds by {} turns'.format(c['unbind'])
        elif c['unbind'] and skill_text:
            skill_text += '; Reduce binds by {} turns'.format(c['unbind'])
        elif c['unbind']:
            skill_text += 'Reduce binds by {} turns'.format(c['unbind'])
        elif c['awoken_unbind'] and skill_text:
            skill_text += '; Reduce awoken skill binds by {} turns'.format(c['awoken_unbind'])
        elif c['awoken_unbind']:
            skill_text += 'Reduce awoken skill binds by {} turns'.format(c['awoken_unbind'])

        c['skill_text'] += skill_text
        
        return 'auto_heal', c
    return f


absorb_mechanic_void_backups = {'duration': 0,
                                'attribute_absorb': False,
                                'damage_absorb': False,
                                'skill_text': ''}


def absorb_mechanic_void_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('absorb_mechanic_void',
                                     arguments,
                                     absorb_mechanic_void_backups)(x)
        if c['attribute_absorb'] and c['damage_absorb']:
            c['skill_text'] += fmt_duration(c['duration']) + \
                'void damage absorb shield and att. absorb shield effects'
        elif c['attribute_absorb'] and not c['damage_absorb']:
            c['skill_text'] += fmt_duration(c['duration']) + 'void att. absorb shield effects'
        elif not c['attribute_absorb'] and c['damage_absorb']:
            c['skill_text'] += fmt_duration(c['duration']) + 'void damage absorb shield effects'
        return 'absorb_mechanic_void', c
    return f


true_gravity_convert_backups = {'percentage_max_hp': 0,
                                'skill_text': ''}


def true_gravity_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('true_gravity',
                                     arguments,
                                     true_gravity_convert_backups)(x)
        c['skill_text'] += 'Deal damage equal to ' + \
            fmt_mult(c['percentage_max_hp'] * 100) + '% of enemies\' max HP'
        return 'true_gravity', c
    return f


extra_combo_backups = {'duration': 0,
                       'combos': 0,
                       'skill_text': ''}


def extra_combo_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('extra_combo',
                                     arguments,
                                     extra_combo_backups)(x)
        c['skill_text'] += fmt_duration(c['duration']) + \
            'increase combo count by ' + str(c['combos'])
        return 'extra_combo', c
    return f


awakening_heal_backups = {'awakenings': [],
                          'amount_per': 0,
                          'skill_text': ''}


def awakening_heal_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('awakening_heal',
                                     arguments,
                                     awakening_heal_backups)(x)
        c['skill_text'] += 'Recover ' + str(c['amount_per']) + ' HP for each '
        for i in range(0, len(c['awakenings']) - 1):
            if c['awakenings'][i + 1] != 0:
                c['skill_text'] += AWAKENING_MAP[c['awakenings'][i]] + ', '
            else:
                c['skill_text'] += AWAKENING_MAP[c['awakenings'][i]]
        if int(c['awakenings'][-1]) != 0:
            c['skill_text'] += AWAKENING_MAP[int(c['awakenings'][-1])]
        c['skill_text'] += ' awakening skill on the team'
        return 'awakening_heal', c
    return f


awakening_attack_boost_backups = {'duration': 0,
                                  'awakenings': [],
                                  'amount_per': 0,
                                  'skill_text': ''}


def awakening_attack_boost_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('awakening_attack_boost',
                                     arguments,
                                     awakening_attack_boost_backups)(x)
        c['skill_text'] += fmt_duration(c['duration']) + 'increase ATK by ' + \
            fmt_mult(c['amount_per'] * 100) + '% for each '
        for i in range(0, len(c['awakenings']) - 1):
            if c['awakenings'][i + 1] != 0:
                c['skill_text'] += AWAKENING_MAP[c['awakenings'][i]] + ', '
            else:
                c['skill_text'] += AWAKENING_MAP[c['awakenings'][i]]
        if int(c['awakenings'][-1]) != 0:
            c['skill_text'] += AWAKENING_MAP[int(c['awakenings'][-1])]
        c['skill_text'] += ' awakening skill on the team'
        return 'awakening_attack_boost', c
    return f


awakening_shield_backups = {'duration': 0,
                            'awakenings': [],
                            'amount_per': 0,
                            'skill_text': ''}


def awakening_shield_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('awakening_shield',
                                     arguments,
                                     awakening_shield_backups)(x)
        c['skill_text'] += fmt_duration(c['duration']) + 'reduce damage taken by ' + \
            fmt_mult(c['amount_per'] * 100) + '% for each '
        for i in range(0, len(c['awakenings']) - 1):
            if c['awakenings'][i + 1] != 0:
                c['skill_text'] += AWAKENING_MAP[c['awakenings'][i]] + ', '
            else:
                c['skill_text'] += AWAKENING_MAP[c['awakenings'][i]]
        if int(c['awakenings'][-1]) != 0:
            c['skill_text'] += AWAKENING_MAP[int(c['awakenings'][-1])]
        c['skill_text'] += ' awakening skill on the team'
        return 'awakening_shield', c
    return f


change_enemies_attribute_backups = {'attribute': 0,
                                    'skill_text': ''}


def change_enemies_attribute_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('change_enemies_attribute',
                                     arguments,
                                     change_enemies_attribute_backups)(x)
        c['skill_text'] += 'Change all enemies to ' + ATTRIBUTES[c['attribute']] + ' Att.'
        return 'change_enemies_attribute', c
    return f


haste_backups = {'turns': 0,
                 'max_turns': 0,
                 'skill_text': ''}


def haste_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('haste',
                                     arguments,
                                     haste_backups)(x)
        if c['turns'] == c['max_turns']:
            if c['turns'] > 1:
                c['skill_text'] += 'Charge allies\' skill by ' + str(c['turns']) + ' turns'
            else:
                c['skill_text'] += 'Charge allies\' skill by ' + str(c['turns']) + ' turn'
        else:
            c['skill_text'] += 'Charge allies\' skill by ' + str(c['turns']) + '~' + str(c['max_turns']) + ' turns'
        return 'haste', c
    return f


random_orb_change_backups = {'from': [],
                             'to': [],
                             'skill_text': ''}


def random_orb_change_convert(arguments):
    def f(x):

        _, c = convert_with_defaults('random_orb_change',
                                     arguments,
                                     random_orb_change_backups)(x)
        c['skill_text'] += 'Change '
        if c['from'] == [0,1,2,3,4,5,6,7,8,9]:
            c['skill_text'] += 'all orbs to '
        elif len(c['from']) > 1:
            for i in c['from'][:-1]:
                c['skill_text'] += ATTRIBUTES[i] + ', '
            c['skill_text'] += ATTRIBUTES[c['from'][-1]] + ' orbs to '
        elif c['from'] != []:
            c['skill_text'] += ATTRIBUTES[c['from'][0]] + ' orbs to '
        if len(c['to']) > 1:
            for i in c['to'][:-1]:
                c['skill_text'] += ATTRIBUTES[i] + ', '
            c['skill_text'] += ATTRIBUTES[c['to'][-1]] + ' orbs'
        elif c['to'] != []:
            c['skill_text'] += ATTRIBUTES[c['to'][0]] + ' orbs'
        return 'random_orb_change', c
    return f


attack_attr_x_team_atk_backups = {'team_attributes': [],
                                  'multiplier': 1,
                                  'mass_attack': False,
                                  'attack_attribute': 0,
                                  'skill_text': ''}


def attack_attr_x_team_atk_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('attack_attr_x_team_atk',
                                     arguments,
                                     attack_attr_x_team_atk_backups)(x)
        c['skill_text'] += 'Deal ' + ATTRIBUTES[c['attack_attribute']] + \
            ' damage equal to ' + fmt_mult(c['multiplier']) + 'x of team\'s total '
        if len(c['team_attributes']) == 1:
            c['skill_text'] += ATTRIBUTES[c['team_attributes'][0]] + ' ATK to '
        elif len(c['team_attributes']) > 1:
            for i in c['team_attributes'][:-1]:
                c['skill_text'] += ATTRIBUTES[i] + ', '
            c['skill_text'] += ATTRIBUTES[c['team_attributes'][-1]] + ' ATK to '
        c['skill_text'] += fmt_mass_atk(c['mass_attack'])
        return 'attack_attr_x_team_atk', c
    return f


spawn_orb_backups = {'amount': 0,
                     'orbs': [],
                     'excluding_orbs': [],
                     'skill_text': ''}


def spawn_orb_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('spawn_orb',
                                     arguments,
                                     spawn_orb_backups)(x)
        c['skill_text'] += 'Create ' + str(c['amount']) + ' '
        if len(c['orbs']) == 1:
            c['skill_text'] += ATTRIBUTES[c['orbs'][0]] + ' orbs at random'
        elif len(c['orbs']) > 1:
            for i in c['orbs'][:-1]:
                c['skill_text'] += ATTRIBUTES[i] + ', '
            c['skill_text'] += ATTRIBUTES[c['orbs'][-1]] + ' orbs at random'
        if c['orbs'] != c['excluding_orbs']:
            templist = list(set(c['excluding_orbs']) - set(c['orbs']))
            c['skill_text'] += ' except '
            if len(templist) > 1:
                for i in templist[:-1]:
                    c['skill_text'] += ATTRIBUTES[i] + ', '
                c['skill_text'] += ATTRIBUTES[templist[-1]] + ' orbs'
            elif len(templist) == 1:
                c['skill_text'] += ATTRIBUTES[templist[0]] + ' orbs'
        return 'spawn_orb', c
    return f


move_time_buff_backups = {'duration': 0,
                          'static': 0,
                          'percentage': 0,
                          'skill_text': ''}


def move_time_buff_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('move_time_buff',
                                     arguments,
                                     move_time_buff_backups)(x)
        if c['static'] == 0:
            c['skill_text'] += fmt_duration(c['duration']) + \
                fmt_mult(c['percentage']) + 'x orb move time'
        elif c['percentage'] == 0:
            c['skill_text'] += fmt_duration(c['duration']) + \
                'increase orb move time by ' + fmt_mult(c['static']) + ' seconds'
        return 'move_time_buff', c
    return f


row_change_backups = {'rows': [],
                      'skill_text': ''}


def row_change_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('row_change',
                                     arguments,
                                     row_change_backups)(x)

        ROW_INDEX = {
            0: 'top row',
            1: '2nd row from top',
            2: '3rd row from bottom',
            3: '2nd row from bottom',
            -2: 'bottom row',
        }

        if len(c['rows']) == 1:
            c['skill_text'] += 'Change ' + \
                ROW_INDEX[int(c['rows'][0]['index'])] + ' to ' + \
                ATTRIBUTES[int(c['rows'][0]['orbs'][0])] + ' orbs'
        elif len(c['rows']) == 2:
            if c['rows'][0]['orbs'][0] == c['rows'][1]['orbs'][0]:
                c['skill_text'] += 'Change ' + ROW_INDEX[int(c['rows'][0]['index'])] + ' and ' + ROW_INDEX[int(
                    c['rows'][1]['index'])] + ' to ' + ATTRIBUTES[int(c['rows'][0]['orbs'][0])] + ' orbs'
            else:
                c['skill_text'] += 'Change ' + \
                    ROW_INDEX[int(c['rows'][0]['index'])] + ' to ' + \
                    ATTRIBUTES[int(c['rows'][0]['orbs'][0])] + ' orbs'
                c['skill_text'] += ' and change ' + \
                    ROW_INDEX[int(c['rows'][1]['index'])] + ' to ' + \
                    ATTRIBUTES[int(c['rows'][1]['orbs'][0])] + ' orbs'
        return 'row_change', c
    return f


column_change_backups = {'columns': [],
                         'skill_text': ''}


def column_change_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('column_change',
                                     arguments,
                                     column_change_backups)(x)

        COLUMN_INDEX = {
            0: 'far left column',
            1: '2nd column from left',
            2: '3rd column from left',
            3: '3rd column from right',
            4: '2nd column from right',
            5: 'far right column',
        }

        if len(c['columns']) == 1:
            c['skill_text'] += 'Change ' + COLUMN_INDEX[int(
                c['columns'][0]['index'])] + ' to ' + ATTRIBUTES[int(c['columns'][0]['orbs'][0])] + ' orbs'
        elif len(c['columns']) == 2:
            if c['columns'][0]['orbs'][0] == c['columns'][1]['orbs'][0]:
                c['skill_text'] += 'Change ' + COLUMN_INDEX[int(c['columns'][0]['index'])] + ' and ' + COLUMN_INDEX[int(
                    c['columns'][1]['index'])] + ' to ' + ATTRIBUTES[int(c['columns'][0]['orbs'][0])] + ' orbs'
            else:
                c['skill_text'] += 'Change ' + COLUMN_INDEX[int(
                    c['columns'][0]['index'])] + ' to ' + ATTRIBUTES[int(c['columns'][0]['orbs'][0])] + ' orbs'
                c['skill_text'] += ' and change ' + COLUMN_INDEX[int(
                    c['columns'][1]['index'])] + ' to ' + ATTRIBUTES[int(c['columns'][1]['orbs'][0])] + ' orbs'
        return 'column_change', c
    return f


change_skyfall_backups = {'orbs': [],
                          'duration': 0,
                          'percentage': 0,
                          'skill_text': ''}


def change_skyfall_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('change_skyfall',
                                     arguments,
                                     change_skyfall_backups)(x)
        c['skill_text'] += fmt_duration(c['duration'])

        if len(c['orbs']) > 1:
            for i in c['orbs'][:-1]:
                c['skill_text'] += ATTRIBUTES[i] + ', '
            c['skill_text'] += ATTRIBUTES[c['orbs'][-1]] + \
                ' orbs are more likely to appear by ' + fmt_mult(c['percentage'] * 100) + '%'
        elif len(c['orbs']) == 1:
            c['skill_text'] += ATTRIBUTES[c['orbs'][0]] + \
                ' orbs are more likely to appear by ' + fmt_mult(c['percentage'] * 100) + '%'
        return 'change_skyfall', c
    return f


random_nuke_backups = {'attribute': 0,
                       'minimum_multiplier': 1,
                       'maximum_multiplier': 1,
                       'mass_attack': False,
                       'skill_text': ''}


def random_nuke_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('random_nuke',
                                     arguments,
                                     random_nuke_backups)(x)
        if c['minimum_multiplier'] != c['maximum_multiplier']:
            c['skill_text'] += 'Randomized ' + ATTRIBUTES[c['attribute']] + ' damage to ' + fmt_mass_atk(
                c['mass_attack']) + '(' + fmt_mult(c['minimum_multiplier']) + '~' + fmt_mult(c['maximum_multiplier']) + 'x)'
        else:
            c['skill_text'] += 'Deal ' + fmt_mult(c['maximum_multiplier']) + 'x ' + \
                ATTRIBUTES[c['attribute']] + ' damage to ' + fmt_mass_atk(c['mass_attack'])
        return 'random_nuke', c
    return f


counterattack_backups = {'duration': 0,
                         'multiplier': 1,
                         'attribute': 0,
                         'skill_text': ''}


def counterattack_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('counterattack',
                                     arguments,
                                     counterattack_backups)(x)

        c['skill_text'] += fmt_duration(c['duration']) + fmt_mult(c['multiplier']) + \
            'x ' + ATTRIBUTES[c['attribute']] + ' counterattack'
        return 'counterattack', c
    return f


board_change_backups = {'attributes': [],
                        'skill_text': ''}


def board_change_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('board_change',
                                     arguments,
                                     board_change_backups)(x)
        c['skill_text'] += 'Change all orbs to '
        if len(c['attributes']) > 1:
            for i in c['attributes'][:-1]:
                c['skill_text'] += ATTRIBUTES[i] + ', '
            c['skill_text'] += 'and ' + ATTRIBUTES[c['attributes'][-1]] + ' orbs'
        elif len(c['attributes']) == 1:
            c['skill_text'] += ATTRIBUTES[c['attributes'][0]] + ' orbs'
        return 'board_change', c
    return f


suicide_random_nuke_backups = {'attribute': 0,
                               'minimum_multiplier': 1,
                               'maximum_multiplier': 1,
                               'hp_remaining': 1,
                               'mass_attack': False,
                               'skill_text': ''}


def suicide_random_nuke_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('suicide_random_nuke',
                                     arguments,
                                     suicide_random_nuke_backups)(x)
        if c['hp_remaining'] == 0:
            c['skill_text'] += 'Reduce HP to 1; '
        else:
            c['skill_text'] += 'Reduce HP by ' + fmt_mult((1 - c['hp_remaining']) * 100) + '%; '
        if c['minimum_multiplier'] != c['maximum_multiplier']:
            c['skill_text'] += 'Randomized ' + ATTRIBUTES[c['attribute']] + ' damage to ' + fmt_mass_atk(
                c['mass_attack']) + '(' + fmt_mult(c['minimum_multiplier']) + '~' + fmt_mult(c['maximum_multiplier']) + 'x)'
        else:
            c['skill_text'] += 'Deal ' + fmt_mult(c['maximum_multiplier']) + 'x ' + \
                ATTRIBUTES[c['attribute']] + ' damage to ' + fmt_mass_atk(c['mass_attack'])
        return 'suicide_random_nuke', c
    return f


suicide_nuke_backups = {'attribute': 0,
                        'damage': 0,
                        'hp_remaining': 1,
                        'mass_attack': False,
                        'skill_text': ''}


def suicide_nuke_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('suicide_nuke',
                                     arguments,
                                     suicide_nuke_backups)(x)
        if c['hp_remaining'] == 0:
            c['skill_text'] += 'Reduce HP to 1; '
        else:
            c['skill_text'] += 'Reduce HP by ' + fmt_mult(c['hp_remaining'] * 100) + '%; '
        c['skill_text'] += 'Deal ' + str(c['damage']) + ' ' + ATTRIBUTES[c['attribute']
                                                                         ] + ' damage to ' + fmt_mass_atk(c['mass_attack'])
        return 'suicide_nuke', c
    return f


type_attack_boost_backups = {'duration': 0,
                             'types': [],
                             'multiplier': 0,
                             'skill_text': ''}


def type_attack_boost_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('type_attack_boost',
                                     arguments,
                                     type_attack_boost_backups)(x)
        c['skill_text'] += fmt_duration(c['duration']) + fmt_mult(c['multiplier']) + 'x ATK for '
        if len(c['types']) > 1:
            for i in c['types'][:-1]:
                c['skill_text'] += TYPES[i] + ', '
            c['skill_text'] += TYPES[c['types'][-1]] + ' types'
        elif len(c['types']) == 1:
            c['skill_text'] += TYPES[c['types'][-1]] + ' type'
        return 'type_attack_boost', c
    return f


grudge_strike_backups = {'mass_attack': False,
                         'attribute': 0,
                         'high_multiplier': 1,
                         'low_multiplier': 1,
                         'skill_text': ''}


def grudge_strike_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('grudge_strike',
                                     arguments,
                                     grudge_strike_backups)(x)
        c['skill_text'] += 'Deal ' + ATTRIBUTES[c['attribute']] + ' damage to ' + fmt_mass_atk(c['mass_attack']) + ' depending on HP level (' + fmt_mult(
            c['low_multiplier']) + 'x at 1 HP and ' + fmt_mult(c['high_multiplier']) + 'x at 100% HP)'
        return 'grudge_strike', c
    return f


drain_attr_attack_backups = {'attribute': 0,
                             'atk_multiplier': 0,
                             'recover_multiplier': 0,
                             'mass_attack': False,
                             'skill_text': ''}


def drain_attr_attack_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('drain_attr_attack',
                                     arguments,
                                     drain_attr_attack_backups)(x)
        c['skill_text'] += 'Deal ' + fmt_mult(c['atk_multiplier']) + 'x ATK ' + \
            ATTRIBUTES[c['attribute']] + ' damage to ' + fmt_mass_atk(c['mass_attack'])
        if c['recover_multiplier'] == 1:
            c['skill_text'] += ' and recover the amount as HP'
        else:
            c['skill_text'] += ' and recover ' + \
                fmt_mult(c['recover_multiplier'] * 100) + '% of the damage as HP'
        return 'drain_attr_attack', c
    return f


attribute_change_backups = {'duration': 0,
                            'attribute': 0,
                            'skill_text': ''}


def attribute_change_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('attribute_change',
                                     arguments,
                                     attribute_change_backups)(x)
        c['skill_text'] += 'Change own Att. to ' + \
            ATTRIBUTES[c['attribute']] + ' for ' + str(c['duration']) + ' turns'
        return 'attribute_change', c
    return f


multi_hit_laser_backups = {'damage': 0,
                           'mass_attack': False,
                           'repeat': 0,
                           'skill_text': ''}


def multi_hit_laser_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('multi_hit_laser',
                                     arguments,
                                     multi_hit_laser_backups)(x)
        c['skill_text'] += 'Deal ' + str(c['damage']) + ' damage to ' + \
            fmt_mass_atk(c['mass_attack'])
        return 'multi_hit_laser', c
    return f


hp_nuke_convert_backups = {'multiplier': 1,
                           'attribute': 0,
                           'mass_attack': True,
                           'skill_text': ''}


def hp_nuke_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('hp_nuke',
                                     arguments,
                                     hp_nuke_convert_backups)(x)
        c['skill_text'] += 'Deal ' + ATTRIBUTES[c['attribute']] + ' damage equal to ' + fmt_mult(c['multiplier']) +\
            'x of team\'s total HP to ' + fmt_mass_atk(c['mass_attack'])
        return 'hp_nuke', c
    return f

# End of Active skill

# Leader skill


def fmt_parameter(c):
    hp_mult = c.get('hp_multiplier', 1)
    atk_mult = c.get('atk_multiplier', c.get('minimum_atk_multiplier', 1.0))
    rcv_mult = c.get('rcv_multiplier', c.get('minimum_rcv_multiplier', 1.0))
    bonus_atk_mult = c.get('bonus_atk_multiplier', 0.0)
    bonus_rcv_mult = c.get('bonus_rcv_multiplier', 0.0)
    damage_reduct = c.get('damage_reduction', c.get('minimum_damage_reduction', 0.0))
    step = c.get('step', 0.0)

    if atk_mult < 1:
        atk_mult = 1.0

    return [float(hp_mult),
            float("{0:.2f}".format(atk_mult + step * bonus_atk_mult)),
            float(rcv_mult + step * bonus_rcv_mult),
            float(damage_reduct)]


passive_stats_backups = {'for_attr': [], 'for_type': [], 'hp_multiplier': 1.0, 'atk_multiplier': 1.0,
                         'rcv_multiplier': 1.0, 'reduction_attributes': all_attr, 'damage_reduction': 0.0, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def passive_stats_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('passive_stats',
                                     arguments,
                                     passive_stats_backups)(x)

        skill_text = fmt_stats_type_attr_bonus(c)
        if skill_text != '' and c['skill_text'] == '':
            c['skill_text'] += skill_text
        elif skill_text != '' and c['skill_text'] != '':
            c['skill_text'] += '; ' + skill_text

        c['parameter'] = fmt_parameter(c)
        return 'passive_stats', c
    return f


threshold_stats_backups = {'for_attr': [], 'for_type': [], 'threshold': False, 'atk_multiplier': 1.0,
                           'rcv_multiplier': 1.0, 'reduction_attributes': all_attr, 'damage_reduction': 0.0, 'skill_text': ''}
ABOVE = True
BELOW = False


def threshold_stats_convert(above, arguments):
    def f(x):
        tag, c = convert_with_defaults('above_threshold_stats' if above else 'below_threshold_stats',
                                       arguments,
                                       threshold_stats_backups)(x)
        threshold = c['threshold']
        skill_text = fmt_stats_type_attr_bonus(c, reduce_join_txt=' and ', skip_attr_all=True)
        if threshold != 1:
            skill_text += ' when above ' if above else ' when below '
            skill_text += fmt_mult(threshold * 100) + '% HP'
        else:
            skill_text += ' when '
            skill_text += 'HP is full' if above else 'HP is not full'
        c['skill_text'] += skill_text
        c['parameter'] = fmt_parameter(c)
        return tag, c
    return f


combo_match_backups = {'for_attr': [], 'for_type': [], 'minimum_combos': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                                            'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                                       'maximum_combos': 0, 'reduction_attributes': all_attr, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def combo_match_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('combo_match',
                                     arguments,
                                     combo_match_backups)(x)
        skill_text = c['skill_text']
        max_combos = c['maximum_combos']
        min_combos = c['minimum_combos']
        min_atk_mult = c['minimum_atk_multiplier']
        bonus_atk_mult = c['bonus_atk_multiplier']

        if max_combos == 0:
            max_combos = min_combos
            c['maximum_combos'] = max_combos

        skill_text += fmt_stats_type_attr_bonus(c, reduce_join_txt=' and ', skip_attr_all=True)
        skill_text += ' when {} or more combos'.format(min_combos)

        if min_combos != max_combos:
            max_mult = min_atk_mult + (max_combos - min_combos) * bonus_atk_mult
            skill_text += ' up to {}x at {} combos'.format(fmt_mult(max_mult), max_combos)

        c['skill_text'] = skill_text

        c['step'] = max_combos - min_combos
        c['parameter'] = fmt_parameter(c)
        return 'combo_match', c
    return f


attribute_match_backups = {'attributes': [], 'minimum_attributes': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                                      'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                             'maximum_attributes': 0, 'reduction_attributes': all_attr, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def attribute_match_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('attribute_match',
                                     arguments,
                                     attribute_match_backups)(x)
        skill_text = c['skill_text']

        skill_text += fmt_stats_type_attr_bonus(c, reduce_join_txt=' and ', skip_attr_all=True)

        max_attr = c['maximum_attributes']
        min_attr = c['minimum_attributes']
        attr = c['attributes']

        if max_attr == 0:
            max_attr = min_attr
            c['maximum_attributes'] = max_attr

        min_atk_mult = c['minimum_atk_multiplier']
        bonus_atk_mult = c['bonus_atk_multiplier']
        max_mult = min_atk_mult + (len(attr) - min_attr) * bonus_atk_mult
        if attr == [0, 1, 2, 3, 4]:
            skill_text += ' when matching {} or more colors'.format(min_attr)
            if max_mult > min_atk_mult:
                skill_text += ' up to {}x at 5 colors'.format(fmt_mult(max_mult))
        elif attr == [0, 1, 2, 3, 4, 5]:
            skill_text += ' when matching {} or more colors ({}+heal)'.format(
                min_attr, min_attr - 1)
            if max_mult > min_atk_mult:
                skill_text += ' up to {}x at 5 colors+heal)'.format(
                    fmt_mult(max_mult), min_attr - 1)
        elif min_attr == max_attr and len(attr) > min_attr:
            attr_text = ', '.join([ATTRIBUTES[i] for i in attr])
            skill_text += ' when matching ' + str(min_attr) + '+ of {} at once'.format(attr_text)
        else:
            attr_text = ', '.join([ATTRIBUTES[i] for i in attr])
            skill_text += ' when matching {} at once'.format(attr_text)

        c['skill_text'] = skill_text
        if max_attr == min_attr and bonus_atk_mult != 0:
            c['step'] = len(attr) - min_attr
        else:
            c['step'] = max_attr - min_attr
        c['parameter'] = fmt_parameter(c)
        return 'attribute_match', c
    return f


multi_attribute_match_backups = {'attributes': [], 'minimum_match': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                                       'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                                   'reduction_attributes': all_attr, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0], 'step': 0}


def multi_attribute_match_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('multi-attribute_match',
                                     arguments,
                                     multi_attribute_match_backups)(x)
        attributes = c['attributes']
        if not attributes:
            return 'multi-attribute_match', c

        min_atk_mult = c['minimum_atk_multiplier']
        min_match = c['minimum_match']
        bonus_atk_mult = c['bonus_atk_multiplier']

        skill_text = c['skill_text']
        skill_text += fmt_stats_type_attr_bonus(c, reduce_join_txt=' and ', skip_attr_all=True)

        if all(x == attributes[0] for x in attributes):
            match_or_more = len(attributes) == min_match
            skill_text += ' when matching {}'.format(min_match)
            if match_or_more:
                skill_text += '+'
            try:
                skill_text += ' {} combos'.format(ATTRIBUTES[attributes[0]])
            except Exception as ex:
                print(ex)
            if not match_or_more:
                max_mult = min_atk_mult + (len(attributes) - min_match) * bonus_atk_mult
                skill_text += ', up to {}x at {} {} combos'.format(
                    fmt_mult(max_mult), len(attributes), ATTRIBUTES[attributes[0]])

        else:
            min_colors = '+'.join([ATTRIBUTES[a] for a in attributes[:min_match]])
            skill_text += ' when matching {}'.format(min_colors)
            if len(attributes) > min_match:
                alt_colors = '+'.join([ATTRIBUTES[a] for a in attributes[1:min_match + 1]])
                skill_text += '({})'.format(alt_colors)

            max_mult = min_atk_mult + (len(attributes) - min_match) * bonus_atk_mult
            if max_mult > min_atk_mult:
                all_colors = '+'.join([ATTRIBUTES[a] for a in attributes])
                skill_text += ' up to {}x when matching {}'.format(fmt_mult(max_mult), all_colors)

        c['skill_text'] = skill_text

        c['step'] = len(attributes) - min_match
        c['parameter'] = fmt_parameter(c)

        return 'multi-attribute_match', c
    return f


mass_match_backups = {'attributes': [], 'minimum_count': 0, 'minimum_atk_multiplier': 1.0, 'minimum_rcv_multiplier': 1.0, 'minimum_damage_reduction': 0.0,
                                                            'bonus_atk_multiplier': 0.0,   'bonus_rcv_multiplier': 0.0,   'bonus_damage_reduction': 0.0,
                                        'maximum_count': 0, 'reduction_attributes': all_attr, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def mass_match_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('mass_match',
                                     arguments,
                                     mass_match_backups)(x)
        max_count = c['maximum_count']
        min_count = c['minimum_count']

        min_atk_mult = c['minimum_atk_multiplier']
        attributes = c['attributes']
        bonus_atk_mult = c['bonus_atk_multiplier']

        skill_text = fmt_stats_type_attr_bonus(c, reduce_join_txt=' and ', skip_attr_all=True)

        skill_text += ' when matching ' + str(min_count)
        if max_count != min_count:
            skill_text += ' or more connected'

        if len(attributes) == 1:
            skill_text += ' ' + ATTRIBUTES[attributes[0]]
        elif len(attributes) > 1 and attributes != [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
            color_text = ', '.join([ATTRIBUTES[i] for i in attributes[:-1]])
            color_text += ' or ' + ATTRIBUTES[attributes[-1]]
            skill_text += ' ' + color_text

        skill_text += ' orbs'

        if max_count != min_count and max_count > 0:
            max_atk = (max_count - min_count) * bonus_atk_mult + min_atk_mult
            skill_text += ' up to {}x at {} orbs'.format(fmt_mult(max_atk), max_count)

        c['skill_text'] += skill_text

        # Temporary hack during tieout to prevent problems
        if max_count == 0:
            c['maximum_count'] = min_count
        # End Temporary hack

        c['step'] = max_count - min_count
        c['parameter'] = fmt_parameter(c)

        return 'mass_match', c
    return f


after_attack_on_match_backups = {'multiplier': 0,
                                 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def after_attack_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('after_attack_on_match',
                                     arguments,
                                     after_attack_on_match_backups)(x)
        c['skill_text'] += fmt_mult(c['multiplier']) + \
            'x ATK additional damage when matching orbs'
        return 'after_attack_on_match', c
    return f


heal_on_match_backups = {'multiplier': 0, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def heal_on_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('heal_on',
                                     arguments,
                                     heal_on_match_backups)(x)
        c['skill_text'] += fmt_mult(c['multiplier']) + \
            'x RCV additional heal when matching orbs'
        return 'heal on match', c
    return f


resolve_backups = {'threshold': 0, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def resolve_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('resolve',
                                     arguments,
                                     resolve_backups)(x)
        c['skill_text'] += 'May survive when HP is reduced to 0 (HP>' + str(
            c['threshold'] * 100).rstrip('0').rstrip('.') + '%)'
        return 'resolve', c
    return f


bonus_move_time_backups = {'time': 0.0, 'for_attr': [], 'for_type': [],
                           'hp_multiplier': 1.0, 'atk_multiplier': 1.0, 'rcv_multiplier': 1.0,
                           'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def bonus_time_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('bonus_move_time',
                                     arguments,
                                     bonus_move_time_backups)(x)
        skill_text = fmt_stats_type_attr_bonus(c)

        time = c['time']
        if time:
            if skill_text:
                skill_text += '; '

            skill_text += 'Increase orb movement time by ' + fmt_mult(time) + ' seconds'

        c['skill_text'] += skill_text

        c['parameter'] = fmt_parameter(c)
        c['parameter'][3] = 0.0
        return 'bonus_move_time', c
    return f


counter_attack_backups = {'chance': 0, 'multiplier': 0, 'attribute': [],
                          'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def counter_attack_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('counter_attack',
                                     arguments,
                                     counter_attack_backups)(x)
        if c['chance'] == 1:
            c['skill_text'] += fmt_mult(c['multiplier']) + \
                'x ' + ATTRIBUTES[int(c['attribute'])] + ' counterattack'
        else:
            c['skill_text'] += fmt_mult(c['chance'] * 100) + '% chance to counterattack with ' + str(
                c['multiplier']).rstrip('0').rstrip('.') + 'x ' + ATTRIBUTES[int(c['attribute'])] + ' damage'

        return 'counter_attack', c
    return f


egg_drop_backups = {'multiplier': 1.0, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def egg_drop_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('egg_drop_rate',
                                     arguments,
                                     egg_drop_backups)(x)
        c['skill_text'] += fmt_mult(c['multiplier']) + 'x Egg Drop rate'
        return 'egg_drop_rate', c
    return f


coin_drop_backups = {'multiplier': 1.0, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def coin_drop_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('coin_drop_rate',
                                     arguments,
                                     coin_drop_backups)(x)
        c['skill_text'] += fmt_mult(c['multiplier']) + 'x Coin Drop rate'
        return 'coin_drop_rate', c
    return f


skill_used_backups = {'for_attr': [], 'for_type': [],
                      'atk_multiplier': 1, 'rcv_multiplier': 1, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def skill_used_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('skill_used_stats',
                                     arguments,
                                     skill_used_backups)(x)
        skill_text = fmt_stats_type_attr_bonus(c, skip_attr_all=True)
        skill_text += ' on the turn a skill is used'
        c['skill_text'] = skill_text

        c['parameter'] = fmt_parameter(c)
        c['parameter'][3] = 0.0
        return 'skill_used_stats', c
    return f


exact_combo_backups = {'combos': 0, 'atk_multiplier': 1,
                       'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def exact_combo_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('exact_combo_match',
                                     arguments,
                                     exact_combo_backups)(x)
        c['skill_text'] += fmt_mult(c['atk_multiplier']) + \
            'x ATK when exactly ' + str(c['combos']) + ' combos'

        c['parameter'] = fmt_parameter(c)
        c['parameter'][3] = 0.0
        return 'exact_combo_match', c
    return f


passive_stats_type_atk_all_hp_backups = {'for_type': [],
                                         'atk_multiplier': 1, 'hp_multiplier': 1, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def passive_stats_type_atk_all_hp_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('passive_stats_type_atk_all_hp',
                                     arguments,
                                     passive_stats_type_atk_all_hp_backups)(x)
        c['skill_text'] += 'Reduce total HP by ' + \
            fmt_mult((1 - c['hp_multiplier']) * 100) + '%; ' + \
            fmt_mult(c['atk_multiplier']) + 'x ATK for '
        for i in c['for_type'][:-1]:
            c['skill_text'] += TYPES[i] + ', '
        c['skill_text'] += TYPES[int(c['for_type'][-1])] + ' type'

        c['parameter'] = fmt_parameter(c)
        c['parameter'][3] = 0.0
        return 'passive_stats_type_atk_all_hp', c
    return f


team_build_bonus_backups = {'monster_ids': 0, 'hp_multiplier': 1,
                            'atk_multiplier': 1, 'rcv_multiplier': 1, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def team_build_bonus_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('team_build_bonus',
                                     arguments,
                                     team_build_bonus_backups)(x)
        monster_ids = str(c['monster_ids'])

        skill_text = fmt_stats_type_attr_bonus(c)
        skill_text += ' if ' + monster_ids + ' is on the team'

        c['skill_text'] += skill_text

        c['parameter'] = fmt_parameter(c)
        c['parameter'][3] = 0.0
        return 'team_build_bonus', c
    return f


rank_exp_rate_backups = {'multiplier': 1, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def rank_exp_rate_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('rank_exp_rate',
                                     arguments,
                                     rank_exp_rate_backups)(x)
        c['skill_text'] += fmt_mult(c['multiplier']) + 'x Rank EXP'
        c['parameter'][3] = 0.0
        return 'rank_exp_rate', c
    return f


heart_tpa_stats_backups = {'rcv_multiplier': 1, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def heart_tpa_stats_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('heart_tpa_stats',
                                     arguments,
                                     heart_tpa_stats_backups)(x)
        c['skill_text'] += fmt_mult(c['rcv_multiplier']) + \
            'x RCV when matching 4 Heal orbs'

        c['parameter'] = fmt_parameter(c)
        c['parameter'][3] = 0.0
        return 'heart_tpa_stats', c
    return f


five_orb_one_enhance_backups = {'atk_multiplier': 1,
                                'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def five_orb_one_enhance_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('five_orb_one_enhance',
                                     arguments,
                                     five_orb_one_enhance_backups)(x)
        c['skill_text'] += fmt_mult(c['atk_multiplier']) + \
            'x ATK for matched Att. when matching 5 Orbs with 1+ enhanced'

        c['parameter'] = fmt_parameter(c)
        c['parameter'][3] = 0.0
        return 'five_orb_one_enhance', c
    return f


heart_cross_backups = {'atk_multiplier': 1, 'rcv_multiplier': 1,
                       'damage_reduction': 0,
                       'cross_count': 1,
                       'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def heart_cross_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('heart_cross',
                                     arguments,
                                     heart_cross_backups)(x)
        atk_mult = c['atk_multiplier']
        rcv_mult = c['rcv_multiplier']
        skill_text = c['skill_text']
        damage_reduct = c['damage_reduction']

        multiplier_text = fmt_multiplier_text(1, atk_mult, rcv_mult)
        if multiplier_text:
            skill_text += multiplier_text

        reduct_text = fmt_reduct_text(damage_reduct)
        if reduct_text:
            if multiplier_text:
                skill_text += ' and ' + reduct_text
            else:
                skill_text += reduct_text.capitalize()

        skill_text += ' when matching 5 Heal orbs in a cross formation'

        c['skill_text'] = skill_text

        c['parameter'] = fmt_parameter(c)
        return 'heart_cross', c
    return f


multi_play_backups = {'for_attr': [], 'for_type': [], 'hp_multiplier': 1.0, 'atk_multiplier': 1.0,
                      'rcv_multiplier': 1.0, 'reduction_attributes': all_attr, 'damage_reduction': 0.0, 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def multi_play_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('multi_play',
                                     arguments,
                                     multi_play_backups)(x)

        c['skill_text'] += fmt_stats_type_attr_bonus(c) + ' when in multiplayer mode'

        c['parameter'] = fmt_parameter(c)
        c['parameter'][3] = 0.0
        return 'multi_play', c
    return f


dual_passive_stat_backups = {'for_attr_1': [], 'for_type_1': [], 'hp_multiplier_1': 1.0, 'atk_multiplier_1': 1.0, 'rcv_multiplier_1': 1.0,
                             'for_attr_2': [], 'for_type_2': [], 'hp_multiplier_2': 1.0, 'atk_multiplier_2': 1.0, 'rcv_multiplier_2': 1.0,
                             'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def dual_passive_stat_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('dual_passive_stat',
                                     arguments,
                                     dual_passive_stat_backups)(x)
        c1 = {}
        c1['for_attr'] = c['for_attr_1']
        c1['for_type'] = c['for_type_1']
        c1['hp_multiplier'] = c['hp_multiplier_1']
        c1['atk_multiplier'] = c['atk_multiplier_1']
        c1['rcv_multiplier'] = c['rcv_multiplier_1']
        c2 = {}
        c2['for_attr'] = c['for_attr_2']
        c2['for_type'] = c['for_type_2']
        c2['hp_multiplier'] = c['hp_multiplier_2']
        c2['atk_multiplier'] = c['atk_multiplier_2']
        c2['rcv_multiplier'] = c['rcv_multiplier_2']
        c['skill_text'] += fmt_stats_type_attr_bonus(c1) + \
            '; ' + c['skill_text'] + fmt_stats_type_attr_bonus(c2)
        if c1['for_type'] == [] and c2['for_type'] == [] and c1['atk_multiplier'] != 1 and c2['atk_multiplier'] != 1:
            c['skill_text'] += '; ' + fmt_mult(c1['atk_multiplier'] *
                                               c2['atk_multiplier']) + 'x ATK for allies with both Att.'

        hp_mult = c1['hp_multiplier'] * c2['hp_multiplier']
        atk_mult = c1['atk_multiplier'] * c2['atk_multiplier']
        rcv_mult = c1['rcv_multiplier'] * c2['rcv_multiplier']
        
        c['parameter'] = [max(hp_mult, 1.0),
                          atk_mult,
                          max(rcv_mult, 1.0),
                          0.0]
        
        return 'dual_passive_stat', c
    return f


dual_threshold_stats_backups = {'for_attr': [], 'for_type': [],
                                'threshold_1': 0, 'above_1': False, 'atk_multiplier_1': 1, 'rcv_multiplier_1': 1, 'damage_reduction_1': 0.0,
                                'threshold_2': 0, 'above_2': False, 'atk_multiplier_2': 1, 'rcv_multiplier_2': 1, 'damage_reduction_2': 0.0,
                                'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def dual_threshold_stats_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('dual_threshold_stats',
                                     arguments,
                                     dual_threshold_stats_backups)(x)
        c1 = {}
        c1['for_attr'] = c['for_attr']
        c1['for_type'] = c['for_type']
        c1['above'] = c['above_1']
        c1['threshold'] = c['threshold_1']
        c1['atk_multiplier'] = c['atk_multiplier_1']
        c1['rcv_multiplier'] = c['rcv_multiplier_1']
        c1['damage_reduction'] = c['damage_reduction_1']
        c1['reduction_attributes'] = [0, 1, 2, 3, 4]
        c2 = {}
        c2['for_attr'] = c['for_attr']
        c2['for_type'] = c['for_type']
        c2['above'] = c['above_2']
        c2['threshold'] = c['threshold_2']
        c2['atk_multiplier'] = c['atk_multiplier_2']
        c2['rcv_multiplier'] = c['rcv_multiplier_2']
        c2['damage_reduction'] = c['damage_reduction_2']
        c2['reduction_attributes'] = [0, 1, 2, 3, 4]
        skill_text = ''
        if c1['atk_multiplier'] != 0 or c1['rcv_multiplier'] != 1 or c1['damage_reduction'] != 0:
            if c1['atk_multiplier'] == 0:
                c1['atk_multiplier'] = 1
            if c1['threshold'] == 1:
                skill_text = fmt_stats_type_attr_bonus(c1, reduce_join_txt=' and ', skip_attr_all=True)
                skill_text += ' when HP is full' if c1['above'] else ' when HP is not full'
            else:
                skill_text = fmt_stats_type_attr_bonus(c1, reduce_join_txt=' and ', skip_attr_all=True)
                skill_text += ' when above ' if c1['above'] else ' when below '
                skill_text += fmt_mult(c1['threshold'] * 100) + '% HP'

        if c2['threshold'] != 0:
            if skill_text != '':
                skill_text += '; '
            if c2['threshold'] == 1:
                skill_text += fmt_stats_type_attr_bonus(c2, reduce_join_txt=' and ', skip_attr_all=True)
                skill_text += ' when HP is full' if c2['above'] else ' when HP is not full'
            else:
                skill_text += fmt_stats_type_attr_bonus(c2, reduce_join_txt=' and ', skip_attr_all=True)
                skill_text += ' when above ' if c2['above'] else ' when below '
                skill_text += fmt_mult(c2['threshold'] * 100) + '% HP'
        c['skill_text'] += skill_text

        c['parameter'] = fmt_parameter(c1)
        c2['parameter'] = fmt_parameter(c2)

        for i in range(1, len(c['parameter'])):
            if c2['parameter'][i] > c['parameter'][i]:
                c['parameter'][i] = c2['parameter'][i]

        return 'dual_threshold_stats', c
    return f


color_cross_backups = {'crosses': [],
                       'hp_multiplier': 1.0, 'atk_multiplier': 1.0, 'rcv_multiplier': 1.0, 'damage_reduction': 0.0,
                       'cross_count': 2,
                       'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def color_cross_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('color_cross',
                                     arguments,
                                     color_cross_backups)(x)
        if len(c['crosses']) == 1:
            c['skill_text'] += fmt_mult(c['crosses'][0]['atk_multiplier']) + 'x ATK for each cross of 5 ' + \
                ATTRIBUTES[int(c['crosses'][0]['attribute'])] + ' orbs'

            c['atk_multiplier'] = pow(c['crosses'][0]['atk_multiplier'], 2)
            c['parameter'] = fmt_parameter(c)
        elif len(c['crosses']) > 1:
            c['cross_count'] = 3
            c['skill_text'] += fmt_mult(c['crosses'][0]['atk_multiplier']
                                        ) + 'x ATK for each cross of 5 '
            for i in range(0, len(c['crosses']))[:-1]:
                c['skill_text'] += ATTRIBUTES[c['crosses'][i]['attribute']] + ', '
            c['skill_text'] += ATTRIBUTES[c['crosses'][-1]['attribute']] + ' orbs'

            c['atk_multiplier'] = pow(c['crosses'][0]['atk_multiplier'], 3)

            c['parameter'] = fmt_parameter(c)

        return 'color_cross', c
    return f


minimum_orb_backups = {'minimum_orb': 3, 'for_attr': [], 'for_type': [],
                       'hp_multiplier': 1.0, 'atk_multiplier': 1.0, 'rcv_multiplier': 1.0,
                       'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def minimum_orb_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('minimum_orb',
                                     arguments,
                                     minimum_orb_backups)(x)

        c['skill_text'] += '[Unable to erase ' + \
            str(c['minimum_orb'] - 1) + ' orbs or less]; ' + fmt_stats_type_attr_bonus(c)

        c['parameter'] = fmt_parameter(c)
        c['parameter'][3] = 0.0
        return 'minimum_orb', c
    return f


orb_remain_backups = {'orb_count': 0,
                      'atk_multiplier': 1,
                      'bonus_atk_multiplier': 0,
                      'skill_text': '',
                      'parameter': [1.0, 1.0, 1.0, 0.0]}


def orb_remain_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('orb_remain',
                                     arguments,
                                     orb_remain_backups)(x)
        c['skill_text'] += fmt_mult(c['atk_multiplier']) + 'x ATK when there are less than ' +\
            str(c['orb_count']) + ' orbs remaining'
        if c['bonus_atk_multiplier'] != 0:
            c['skill_text'] += ' up to ' + fmt_mult(c['atk_multiplier'] +
                                                    c['bonus_atk_multiplier'] *
                                                    c['orb_count']) +\
                               'x ATK when 0 orbs left'
        c['step'] = c['orb_count']
        c['parameter'] = fmt_parameter(c)
        c['parameter'][3] = 0.0
        return 'orb_remain', c
    return f


collab_bonus_backups = {'collab_id': 0, 'for_attr': [0, 1, 2, 3, 4], 'for_type': [],
                        'hp_multiplier': 1.0, 'atk_multiplier': 1.0, 'rcv_multiplier': 1.0,
                        'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}


def collab_bonus_convert(arguments):
    def f(x):
        _, c = convert_with_defaults('collab_bonus',
                                     arguments,
                                     collab_bonus_backups)(x)

        COLLAB_MAP = {
            0: '',
            1: 'Ragnarok Online Collab',
            2: 'Taiko no Tatsujin Collab',
            3: 'ECO Collab',
            5: 'Gunma\'s Ambition Collab',
            6: 'Final Fantasy Crystal Defender Collab',
            7: 'Famitsu Collab',
            8: 'Princess Punt Sweet Collab',
            9: 'Android Collab',
            10: 'Batman Collab',
            11: 'Capybara-san Collab',
            12: 'GungHo Collab',
            13: 'GungHo Collab',
            14: 'Evangelion Collab',
            15: 'Seven Eleven Collab',
            16: 'Clash of Clan Collab',
            17: 'Groove Coaster Collab',
            18: 'RO ACE Collab',
            19: 'Dragon\'s Dogma Collab',
            20: 'Takaoka City Collab',
            21: 'Monster Hunter 4G Collab',
            22: 'Shinrabansho Choco Collab',
            23: 'Thirty One Icecream Collab',
            24: 'Angry Bird Collab',
            26: 'Hunter x Hunter Collab',
            27: 'Hello Kitty Collab',
            28: 'PAD Battle Tournament Collab',
            29: 'BEAMS Collab',
            30: 'Dragon Ball Z Collab',
            31: 'Saint Seiya Collab',
            32: 'GungHo Collab',
            33: 'GungHo Collab',
            34: 'GungHo Collab',
            35: 'Gungho Collab',
            36: 'Bikkuriman Collab',
            37: 'Angry Birds Collab',
            38: 'DC Universe Collab',
            39: 'Sangoku Tenka Trigger Collab',
            40: 'Fist of the North Star Collab',
            41: 'Chibi Series',
            44: 'Chibi Keychain Series',
            45: 'Final Fantasy Collab',
            46: 'Ghost in Shell Collab',
            47: 'Duel Masters Collab',
            48: 'Attack on Titans Collab',
            49: 'Ninja Hattori Collab',
            50: 'Shounen Sunday Collab',
            51: 'Crows Collab',
            52: 'Bleach Collab',
            53: 'DC Universe Collab',
            55: 'Ace Attorney Collab',
            56: 'Kenshin Collab',
            57: 'Pepper Collab',
            58: 'Kinnikuman Collab',
            59: 'Napping Princess Collab',
            60: 'Magazine All-Stars Collab',
            61: 'Monster Hunter Collab',
            62: 'Special edition MP series',
            64: 'DC Universe Collab',
            65: 'Full Metal Alchemist Collab',
            66: 'King of Fighters \'98 Collab',
            67: 'Yu Yu Hakusho Collab',
            68: 'Persona Collab',
            69: 'Coca Cola Collab',
            70: 'Magic: The Gathering Collab',
            71: 'GungHo Collab',
            72: 'GungHo Collab',
            74: 'Power Pro Collab',
            10001: 'Dragonbounds & Dragon Callers',
        }

        c['skill_text'] += fmt_stats_type_attr_bonus(c) + \
            ' when all cards are from ' + COLLAB_MAP[c['collab_id']]

        c['parameter'] = fmt_parameter(c)
        c['parameter'][3] = 0.0
        return 'collab_bonus', c
    return f

# End of Leader skill


SKILL_TRANSFORM = {
    0: lambda x:
    convert('null_skill', {})(x)
    if make_defaultlist(int, x)[1] == 0 else
    attr_nuke_convert({'attribute': (0, cc), 'multiplier': (1, multi), 'mass_attack': True})(x),
    1: fixed_attr_nuke_convert({'attribute': (0, cc), 'damage': (1, cc), 'mass_attack': True}),
    2: self_att_nuke_convert({'multiplier': (0, multi), 'mass_attack': False}),
    3: shield_convert({'duration': (0, cc), 'reduction': (1, multi)}),
    4: poison_convert({'multiplier': (0, multi)}),
    5: ctw_convert({'duration': (0, cc)}),
    6: gravity_convert({'percentage_hp': (0, multi)}),
    7: heal_active_convert({'rcv_multiplier_as_hp': (0, multi), 'card_bind': 0, 'hp': 0, 'percentage_max_hp': 0.0, 'awoken_bind': 0, 'team_rcv_multiplier_as_hp': 0.0}),
    8: heal_active_convert({'hp': (0, cc), 'card_bind': 0, 'rcv_multiplier_as_hp': 0.0, 'percentage_max_hp': 0.0, 'awoken_bind': 0, 'team_rcv_multiplier_as_hp': 0.0}),
    9: single_orb_change_convert({'from': (0, cc), 'to': (1, cc)}),
    10: convert('board_refresh', {'skill_text': 'Replace all orbs'}),
    18: delay_convert({'turns': (0, cc)}),
    19: defense_reduction_convert({'duration': (0, cc), 'reduction': (1, multi)}),
    20: double_orb_convert({'from_1': (0, cc), 'to_1': (1, cc), 'from_2': (2, cc), 'to_2': (3, cc)}),
    21: elemental_shield_convert({'duration': (0, cc), 'attribute': (1, cc), 'reduction': (2, multi)}),
    35: drain_attack_convert({'atk_multiplier': (0, multi), 'recover_multiplier': (1, multi), 'mass_attack': False}),
    37: attr_nuke_convert({'attribute': (0, cc), 'multiplier': (1, multi), 'mass_attack': False}),
    42: damage_to_att_enemy_convert({'enemy_attribute': (0, cc), 'attack_attribute': (1, cc), 'damage': (2, cc)}),
    50: lambda x:
    rcv_boost_convert({'duration': (0, cc), 'multiplier': (2, multi)})(x)
    if make_defaultlist(int, x)[1] == 5 else
    attribute_attack_boost_convert(
        {'duration': (0, cc), 'for_attr': (1, listify), 'atk_multiplier': (2, multi)})(x),
    51: mass_attack_convert({'duration': (0, cc)}),
    52: enhance_convert({'orbs': (0, listify)}),
    55: laser_convert({'damage': (0, cc), 'mass_attack': False}),
    56: laser_convert({'damage': (0, cc), 'mass_attack': True}),
    58: random_nuke_convert({'attribute': (0, cc), 'minimum_multiplier': (1, multi), 'maximum_multiplier': (2, multi), 'mass_attack': True}),
    59: random_nuke_convert({'attribute': (0, cc), 'minimum_multiplier': (1, multi), 'maximum_multiplier': (2, multi), 'mass_attack': False}),
    60: counterattack_convert({'duration': (0, cc), 'multiplier': (1, multi), 'attribute': (2, cc)}),
    71: board_change_convert({'attributes': (slice(None), lambda x: [v for v in x if v != -1])}),
    84: suicide_random_nuke_convert({'attribute': (0, cc), 'minimum_multiplier': (1, multi), 'maximum_multiplier': (2, multi), 'hp_remaining': (3, multi), 'mass_attack': False}),
    85: suicide_random_nuke_convert({'attribute': (0, cc), 'minimum_multiplier': (1, multi), 'maximum_multiplier': (2, multi), 'hp_remaining': (3, multi), 'mass_attack': True}),
    86: suicide_nuke_convert({'attribute': (0, cc), 'damage': (1, cc), 'hp_remaining': (3, multi), 'mass_attack': False}),
    87: suicide_nuke_convert({'attribute': (0, cc), 'damage': (1, cc), 'hp_remaining': (3, multi), 'mass_attack': True}),
    88: type_attack_boost_convert({'duration': (0, cc), 'types': (1, listify), 'multiplier': (2, multi)}),
    90: lambda x:
    attribute_attack_boost_convert({'duration': (0, cc), 'for_attr': (slice(1, 3), list_con), 'atk_multiplier': (2, ccf)})(x)
    if len(make_defaultlist(int, x)) == 3 else
    (attribute_attack_boost_convert({'duration': (0, cc), 'for_attr': (slice(1, 3), list_con), 'atk_multiplier': (3, multi)})(x)
     if len(make_defaultlist(int, x)) == 4 else
     (convert('unexpected', {'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]})(x)
      if len(make_defaultlist(int, x)) == 0 else
      (90, x))),
    91: enhance_convert({'orbs': (slice(0, 2), list_con)}),
    92: type_attack_boost_convert({'duration': (0, cc), 'types': (slice(1, 3), list_con), 'multiplier': (3, multi)}),
    93: convert('leader_swap', {'skill_text': 'Becomes Team leader, changes back when used again'}),
    110: grudge_strike_convert({'mass_attack': (0, lambda x: x == 0), 'attribute': (1, cc), 'high_multiplier': (2, multi), 'low_multiplier': (3, multi)}),
    115: drain_attr_attack_convert({'attribute': (0, cc), 'atk_multiplier': (1, multi), 'recover_multiplier': (2, multi), 'mass_attack': False}),
    116: convert('combine_active_skills', {'skill_ids': (slice(None), list_con), 'skill_text': ''}),
    117: heal_active_convert({'card_bind': (0, cc), 'rcv_multiplier_as_hp': (1, multi), 'hp': (2, cc), 'percentage_max_hp': (3, multi), 'awoken_bind': (4, cc), 'team_rcv_multiplier_as_hp': 0.0}),
    118: convert('random_skill', {'skill_ids': (slice(None), list_con), 'skill_text': 'Activate a random skill'}),
    126: change_skyfall_convert({'orbs': (0, binary_con), 'duration': (1, cc), 'percentage': (3, multi)}),
    127: column_change_convert({'columns': (slice(None), lambda x: [{'index': i, 'orbs': binary_con(orbs)} for indices, orbs in zip(x[::2], x[1::2]) for i in binary_con(indices)])}),
    128: row_change_convert({'rows': (slice(None), lambda x: [{'index': i if i < 4 else i - 6, 'orbs': binary_con(orbs)} for indices, orbs in zip(x[::2], x[1::2]) for i in binary_con(indices)])}),
    132: move_time_buff_convert({'duration': (0, cc), 'static': (1, lambda x: x / 10), 'percentage': (2, multi)}),
    140: enhance_convert({'orbs': (0, binary_con)}),
    141: spawn_orb_convert({'amount': (0, cc), 'orbs': (1, binary_con), 'excluding_orbs': (2, binary_con)}),
    142: attribute_change_convert({'duration': (0, cc), 'attribute': (1, cc)}),
    143: hp_nuke_convert({'multiplier': (0, multi)}), # May be using incomplete data eg. Mamoru SID: 10573
    144: attack_attr_x_team_atk_convert({'team_attributes': (0, binary_con), 'multiplier': (1, multi), 'mass_attack': (2, lambda x: x == 0), 'attack_attribute': (3, cc), }),
    145: heal_active_convert({'team_rcv_multiplier_as_hp': (0, multi), 'card_bind': 0, 'rcv_multiplier_as_hp': 0.0, 'hp': 0, 'percentage_max_hp': 0.0, 'awoken_bind': 0}),
    146: haste_convert({'turns': (0, cc), 'max_turns': (1, cc)}),
    152: lock_convert({'orbs': (0, binary_con)}),
    153: change_enemies_attribute_convert({'attribute': (0, cc)}),
    154: random_orb_change_convert({'from': (0, binary_con), 'to': (1, binary_con)}),
    156: lambda x:
    awakening_heal_convert({'awakenings': (slice(1, 4), list_con), 'amount_per': (5, cc)})(x)
    if make_defaultlist(int, x)[4] == 1 else
    (awakening_attack_boost_convert({'duration': (0, cc), 'awakenings': (slice(1, 4), list_con), 'amount_per': (5, lambda x: (x - 100) / 100)})(x)
        if make_defaultlist(int, x)[4] == 2 else
     (awakening_shield_convert({'duration': (0, cc), 'awakenings': (slice(1, 4), list_con), 'amount_per': (5, multi)})(x)
      if make_defaultlist(int, x)[4] == 3 else
      (convert('unexpected', {'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]})(x)
       if make_defaultlist(int, x)[4] == 0 else
       (156, x)))),
    160: extra_combo_convert({'duration': (0, cc), 'combos': (1, cc)}),
    161: true_gravity_convert({'percentage_max_hp': (0, multi)}),
    172: convert('unlock', {'skill_text': 'Unlock all orbs'}),
    173: absorb_mechanic_void_convert({'duration': (0, cc), 'attribute_absorb': (1, bool), 'damage_absorb': (3, bool)}),
    179: auto_heal_convert({'duration': (0, cc), 'percentage_max_hp': (2, multi), 'unbind': (3,cc), 'awoken_unbind': (4,cc)}),
    180: enhance_skyfall_convert({'duration': (0, cc), 'percentage_increase': (1, multi)}),
    184: no_skyfall_convert({'duration': (0, cc)}),
    188: multi_hit_laser_convert({'damage': (0, cc), 'mass_attack': False}),
    189: convert('unlock_board_path', { 'skill_text': 'Unlock all orbs; Change all orbs to Fire, Water, Wood, and Light orbs; Show path to 3 combos'}),  # May be using incomplete data eg. Toragon SID: 10136
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
    33: convert('drumming_sound', {'skill_text': 'Turn orb sound effects into Taiko noises', 'parameter': [1.0, 1.0, 1.0, 0.0]}),
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
    136: dual_passive_stat_convert({'for_attr_1': (0, binary_con), 'for_type_1': [], 'hp_multiplier_1': (1, multi2), 'atk_multiplier_1': (2, multi2), 'rcv_multiplier_1': (3, multi2),
                                    'for_attr_2': (4, binary_con), 'for_type_2': [], 'hp_multiplier_2': (5, multi2), 'atk_multiplier_2': (6, multi2), 'rcv_multiplier_2': (7, multi2)}),
    137: dual_passive_stat_convert({'for_attr_1': [], 'for_type_1': (0, binary_con), 'hp_multiplier_1': (1, multi2), 'atk_multiplier_1': (2, multi2), 'rcv_multiplier_1': (3, multi2),
                                    'for_attr_2': [], 'for_type_2': (4, binary_con), 'hp_multiplier_2': (5, multi2), 'atk_multiplier_2': (6, multi2), 'rcv_multiplier_2': (7, multi2)}),
    138: convert('combine_leader_skills', {'skill_ids': (slice(None), list_con), 'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}),
    139: dual_threshold_stats_convert({'for_attr': (0, binary_con), 'for_type': (1, binary_con),
                                       'threshold_1': (2, multi), 'above_1': (3, lambda x: not bool(x)), 'atk_multiplier_1': (4, multi), 'rcv_multiplier_1': 1.0, 'damage_reduction_1': 0.0,
                                       'threshold_2': (5, multi), 'above_2': (6, lambda x: not bool(x)), 'atk_multiplier_2': (7, multi), 'rcv_multiplier_2': 1.0, 'damage_reduction_2': 0.0}),
    148: rank_exp_rate_convert({'multiplier': (0, multi)}),
    149: heart_tpa_stats_convert({'rcv_multiplier': (0, multi)}),
    150: five_orb_one_enhance_convert({'atk_multiplier': (1, multi)}),
    151: heart_cross_convert({'atk_multiplier': (0, multi2), 'rcv_multiplier': (1, multi2), 'damage_reduction': (2, multi)}),
    155: multi_play_convert({'for_attr': (0, binary_con), 'for_type': (1, binary_con), 'hp_multiplier': (2, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2)}),
    157: color_cross_convert({'crosses': (slice(None), lambda x: [{'attribute': a, 'atk_multiplier': multi(d)} for a, d in zip(x[::2], x[1::2])])}),
    158: minimum_orb_convert({'minimum_orb': (0, cc), 'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'hp_multiplier': (4, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (5, multi2)}),
    159: mass_match_convert({'attributes': (0, binary_con), 'minimum_count': (1, cc), 'minimum_atk_multiplier': (2, multi), 'bonus_atk_multiplier': (3, multi), 'maximum_count': (4, cc)}),
    162: passive_stats_convert({'for_attr': [], 'for_type': [], 'hp_multiplier': 1.0, 'atk_multiplier': 1.0, 'rcv_multiplier': 1.0, 'skill_text': '[Board becomes 7x6]'}),
    163: passive_stats_convert({'for_attr': (0, binary_con), 'for_type': (1, binary_con), 'hp_multiplier': (2, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2), 'reduction_attributes': (5, binary_con), 'damage_reduction': (6, multi),
                                'skill_text': '[No Skyfall]'}),
    164: multi_attribute_match_convert({'attributes': (slice(0, 4), list_binary_con), 'minimum_match': (4, cc), 'minimum_atk_multiplier': (5, multi), 'minimum_rcv_multiplier': (6, multi), 'bonus_atk_multiplier': (7, multi), 'bonus_rcv_multiplier': (7, multi)}),
    165: attribute_match_convert({'attributes': (0, binary_con), 'minimum_attributes': (1, cc), 'minimum_atk_multiplier': (2, multi), 'minimum_rcv_multiplier': (3, multi), 'bonus_atk_multiplier': (4, multi), 'bonus_rcv_multiplier': (5, multi),
                                  'maximum_attributes': (slice(1, 7, 6), lambda x: x[0] + x[1])}),
    166: combo_match_convert({'for_attr': all_attr, 'minimum_combos': (0, cc), 'minimum_atk_multiplier': (1, multi), 'minimum_rcv_multiplier': (2, multi), 'bonus_atk_multiplier': (3, multi), 'bonus_rcv_multiplier': (4, multi), 'maximum_combos': (5, cc)}),
    167: mass_match_convert({'attributes': (0, binary_con), 'minimum_count': (1, cc), 'minimum_atk_multiplier': (2, multi), 'minimum_rcv_multiplier': (3, multi), 'bonus_atk_multiplier': (4, multi), 'bonus_rcv_multiplier': (5, multi), 'maximum_count': (6, cc)}),
    169: combo_match_convert({'for_attr': all_attr, 'minimum_combos': (0, cc), 'minimum_atk_multiplier': (1, multi), 'minimum_damage_reduction': (2, multi)}),
    170: attribute_match_convert({'attributes': (0, binary_con), 'minimum_attributes': (1, cc), 'minimum_atk_multiplier': (2, multi), 'minimum_damage_reduction': (3, multi)}),
    171: multi_attribute_match_convert({'attributes': (slice(0, 4), list_binary_con), 'minimum_match': (4, cc), 'minimum_atk_multiplier': (5, multi), 'minimum_damage_reduction': (6, multi)}),
    175: collab_bonus_convert({'collab_id': (0, cc), 'hp_multiplier': (3, multi2), 'atk_multiplier': (4, multi2), 'rcv_multiplier': (5, multi2)}),
    176: convert('unexpected', {'skill_text': '', 'parameter': [1.0, 1.0, 1.0, 0.0]}),
    177: orb_remain_convert({'orb_count': (5, cc), 'atk_multiplier': (6, multi), 'bonus_atk_multiplier': (7, multi), 'skill_text': '[No skyfall]; '}),
    178: passive_stats_convert({'time': (0, cc), 'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'hp_multiplier': (3, multi2), 'atk_multiplier': (4, multi2), 'rcv_multiplier': (5, multi2), 'skill_text': '[Fixed 4 second movetime]'}),
    182: mass_match_convert({'attributes': (0, binary_con), 'minimum_count': (1, cc), 'minimum_atk_multiplier': (2, multi), 'minimum_damage_reduction': (3, multi)}),
    183: dual_threshold_stats_convert({'for_attr': (0, binary_con), 'for_type': (1, binary_con),
                                       'threshold_1': (2, multi), 'above_1': True, 'atk_multiplier_1': (3, multi), 'rcv_multiplier_1': 1.0, 'damage_reduction_1': (4, multi),
                                       'threshold_2': (5, multi), 'above_2': False, 'atk_multiplier_2': (6, multi2), 'rcv_multiplier_2': (7, multi2), 'damage_reduction_2': 0.0}),
    185: bonus_time_convert({'time': (0, multi), 'for_attr': (1, binary_con), 'for_type': (2, binary_con), 'hp_multiplier': (3, multi2), 'atk_multiplier': (4, multi2), 'rcv_multiplier': (5, multi2)}),
    186: passive_stats_convert({'for_attr': (0, binary_con), 'for_type': (1, binary_con), 'hp_multiplier': (2, multi2), 'atk_multiplier': (3, multi2), 'rcv_multiplier': (4, multi2), 'skill_text': '[Board becomes 7x6]'}), }


MULTI_PART_LS = {}
MULTI_PART_AS = {}


def reformat(in_file_name, out_file_name):
    print('-- Parsing skills --\n')
    with open(in_file_name) as f:
        skill_data = json.load(f)
    print('Raw skills json loaded\n')
    reformatted = reformat_json(skill_data)

    print('Converted {active} active skills and {leader} leader skills ({comb} total)\n'.format(
        active=len(reformatted['active_skills']),
        leader=len(reformatted['leader_skills']),
        comb=(len(reformatted['active_skills']) + len(reformatted['leader_skills']))))

    def verify(skills):
        ls_verification = defaultdict(lambda: defaultdict(set))
        for name, data in skills.items():
            ls_verification[data['type']]['_arg_names'].add(frozenset(data['args'].keys()))
            for a_name, a_value in data['args'].items():
                ls_verification[data['type']][a_name].add(type(a_value))
        for name, value in ls_verification.items():
            for a, p in value.items():
                if len(p) != 1:
                    print('INCONSISTENT name:{name} difference in {repa}: {repp}\n'.format(
                        name=name, repa=repr(a)), repp=repr(p))

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


class CalculatedSkill(object):
    def __init__(self, skill_id, skill_desc, skill_params=None):
        self.skill_id = skill_id
        self.description = skill_desc
        self.params = skill_params


def reformat_json_info(skill_data):
    reformatted = reformat_json(skill_data)
    leader_skills = {}
    active_skills = {}

    for sid, info in reformatted['leader_skills'].items():
        args = info['args']
        if 'skill_text' in args:
            parameter = args.get('parameter', [1.0, 1.0, 1.0, 1.0])
            leader_skills[sid] = CalculatedSkill(sid, args['skill_text'], parameter)
    for sid, info in reformatted['active_skills'].items():
        args = info['args']
        if 'skill_text' in args:
            leader_skills[sid] = CalculatedSkill(sid, args['skill_text'])

    # IDs are unique, no need for two maps
    results = leader_skills.copy()
    leader_skills.update(active_skills)
    return results

def reformat_json(skill_data):
    reformatted = {}
    reformatted['res'] = skill_data['res']
    reformatted['version'] = skill_data['v']
    reformatted['ckey'] = skill_data['ckey']
    reformatted['active_skills'] = {}
    reformatted['leader_skills'] = {}

    print('Starting skill conversion of {count} skills'.format(count=len(skill_data["skill"])))
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
                    print('Unhandled leader skill type: {c2} (skill id: {i})'.format(
                        c2=c[2], i=i))
                    del reformatted['leader_skills'][i]
                    continue
                if reformatted['leader_skills'][i]['type'] == 'combine_leader_skills':
                    for j in range(0, len(reformatted['leader_skills'][i]['args']['skill_ids'])):
                        if MULTI_PART_LS.get(str(reformatted['leader_skills'][i]['args']['skill_ids'][j])):
                            MULTI_PART_LS[str(reformatted['leader_skills'][i]
                                              ['args']['skill_ids'][j])] += [i]
                        else:
                            MULTI_PART_LS[str(reformatted['leader_skills'][i]
                                              ['args']['skill_ids'][j])] = [i]
            else:
                print('Unexpected leader skill type: {c2} (skill id: {i})'.format(c2=c[2], i=i))
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
                    print('Unhandled active skill type: {c2} (skill id: {i})'.format(c2=c[2], i=i))
                    del reformatted['active_skills'][i]
                if reformatted['active_skills'][i]['type'] == 'combine_active_skills':
                    for j in range(0, len(reformatted['active_skills'][i]['args']['skill_ids'])):
                        part_id = str(reformatted['active_skills'][i]['args']['skill_ids'][j])
                        if not part_id in MULTI_PART_AS.keys():
                            MULTI_PART_AS[part_id] = []
                        MULTI_PART_AS[part_id].append(reformatted['active_skills'][i]['id'])
            else:
                print('Unexpected active skill type: {c2} (skill id: {i})'.format(c2=c[2], i=i))
                del reformatted['active_skills'][i]
                #reformatted['active_skills'][i]['type'] = f'_{c[2]}'
                #reformatted['active_skills'][i]['args'] = {f'_{i}':v for i,v in enumerate(c[6:])}
    for j, c in enumerate(skill_data['skill']):
        if c[2] in SKILL_TRANSFORM:
            i_str = str(j)
            if MULTI_PART_LS.get(i_str):
                for k in range(0, len(MULTI_PART_LS[i_str])):
                        # Generating skill_text
                    combined_skill_args = reformatted['leader_skills'][j]['args']
                    cur_skill_id = int(MULTI_PART_LS[i_str][k])
                    cur_args = reformatted['leader_skills'][cur_skill_id]['args']

                    if cur_args['skill_text'] == '':
                        cur_args['skill_text'] += combined_skill_args['skill_text']
                    else:
                        cur_args['skill_text'] += '; ' + \
                            combined_skill_args['skill_text']
                    # Generating parameter
                    hp_mult = float(cur_args['parameter'][0])
                    atk_mult = float(cur_args['parameter'][1])
                    rcv_mult = float(cur_args['parameter'][2])
                    reduction = float(cur_args['parameter'][3])

                    hp_mult *= combined_skill_args['parameter'][0]
                    atk_mult *= combined_skill_args['parameter'][1]
                    rcv_mult *= combined_skill_args['parameter'][2]
                    reduction = 1 - (1 - reduction) * \
                        (1 - float(combined_skill_args['parameter'][3]))
                    cur_args['parameter'] = [hp_mult, atk_mult, rcv_mult, reduction]
            elif MULTI_PART_AS.get(str(j)):
                AS = reformatted['active_skills']
                LS = reformatted['leader_skills']

                for repeated_skill in range(0,len(MULTI_PART_AS[str(j)])):
                    
                    AS_comb_skill_text = reformatted['active_skills'][MULTI_PART_AS[str(j)][repeated_skill]]['args']['skill_text']
                    if AS.get(j):

                        AS_curr_arg = AS[j]['args']
                        AS_comb_skill_ids = AS[MULTI_PART_AS[str(j)][repeated_skill]]['args']['skill_ids']

                        if AS_curr_arg.get('skill_text'):

                            AS_curr_type = AS[j]['type']
                            AS_curr_skill_text = AS[j]['args']['skill_text']

                            if AS_comb_skill_text == '':
                                AS_comb_skill_text += AS_curr_skill_text

                                if AS_curr_type == 'multi_hit_laser':  # Adding extra text for multi_hit_laser
                                    repeat = 0
                                    for k in range(0, len(AS_comb_skill_ids)):
                                        if AS_comb_skill_ids[k] == j:
                                            repeat += 1
                                    AS_comb_skill_text += ' ' + str(repeat) + ' times'
                                    MULTI_PART_AS[str(j)] = [MULTI_PART_AS[str(j)][0]]
                            else:
                                AS_comb_skill_text += '; ' + AS_curr_skill_text

                                if AS_curr_type == 'multi_hit_laser':  # Adding extra text for multi_hit_laser
                                    repeat = 0
                                    for k in range(0, len(AS_comb_skill_ids)):
                                        if AS_comb_skill_ids[k] == j:
                                            repeat += 1
                                    AS_comb_skill_text += ' ' + str(repeat) + ' times'
                                    MULTI_PART_AS[str(j)] = [MULTI_PART_AS[str(j)][0]]
                    elif LS.get(j):

                        LS_curr_arg = LS[j]['args']
                        AS_comb_skill_ids = AS[MULTI_PART_AS[str(j)][repeated_skill]]['args']['skill_ids']

                        if LS_curr_arg.get('skill_text'):

                            LS_curr_type = LS[j]['type']
                            LS_curr_skill_text = LS[j]['args']['skill_text']

                            if AS_comb_skill_text == '':

                                AS_comb_skill_text += LS_curr_skill_text

                                if LS_curr_type == 'multi_hit_laser':  # Adding extra text for multi_hit_laser
                                    repeat = 0
                                    for k in range(0, len(AS_comb_skill_ids)):
                                        if AS_comb_skill_ids[k] == j:
                                            repeat += 1
                                    AS_comb_skill_text += ' ' + str(repeat) + ' times'
                                    MULTI_PART_AS[str(j)] = [MULTI_PART_AS[str(j)][0]]
                            else:

                                AS_comb_skill_text += '; ' + LS_curr_skill_text

                                if LS_curr_type == 'multi_hit_laser':  # Adding extra text for multi_hit_laser
                                    repeat = 0
                                    for k in range(0, len(AS_comb_skill_ids)):
                                        if AS_comb_skill_ids[k] == j:
                                            repeat += 1
                                    AS_comb_skill_text += ' ' + str(repeat) + ' times'
                                    MULTI_PART_AS[str(j)] = [MULTI_PART_AS[str(j)][0]]
                    reformatted['active_skills'][MULTI_PART_AS[str(j)][repeated_skill]]['args']['skill_text'] = AS_comb_skill_text
                    if 'times' in reformatted['active_skills'][MULTI_PART_AS[str(j)][repeated_skill]]['args']['skill_text']:
                        break

    # Do final trimming on parameter values now that all the math has completed
    for skill in reformatted['leader_skills'].values():
        args = skill['args']
        params = args.get('parameter', [])
        for i, v in enumerate(params):
            params[i] = round(float(v), 4)
    
    return reformatted


if __name__ == '__main__':
    reformat(sys.argv[1], sys.argv[2])
    pass
