from operator import itemgetter


class LsTextConverter(object):
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

    def fmt_mult(x):
        return str(round(float(x), 2)).rstrip('0').rstrip('.')

    def attributes_format(attributes):
        return ', '.join([ATTRIBUTES[i] for i in attributes])

    def types_format(types):
        return ', '.join([TYPES[i] for i in types])

    def fmt_stats_type_attr_bonus(c, reduce_join_txt='; ', skip_attr_all=False):
        return ''
        types = c.get('types', [])
        attributes = c.get('attributes', [])
        hp_mult = c.get('hp', 1)
        atk_mult = c.get('atk', c.get('min_atk', 1))
        rcv_mult = c.get('rcv', c.get('min_rcv', 1))
        damage_reduct = c.get('damage_reduction', c.get('min_damage_reduction', 0))
        reduct_att = c.get('reduction_attributes', [])
        skill_text = ''

        multiplier_text = fmt_multiplier_text(hp_mult, atk_mult, rcv_mult)
        if multiplier_text:
            skill_text += multiplier_text

            for_skill_text = ''
            if types:
                for_skill_text += ' ' + ', '.join([TYPES[i] for i in types]) + ' type'

            if attributes and not (skip_attr_all and len(attributes) == 5):
                if for_skill_text:
                    for_skill_text += ' and'
                color_text = 'all' if len(attributes) == 5 else attributes_format(attributes)
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

    def fmt_multi_attr(attributes, conjunction='or'):
        return ''
        prefix = ' '
        if 1 <= len(attributes) <= 7:
            attr_list = [ATTRIBUTES[i] for i in attributes]
        elif 7 <= len(attributes) < 10:
            att_sym_diff = sorted(list(set(ATTRIBUTES) - set(attributes)), key=lambda x: ATTRIBUTES[x])
            attr_list = [ATTRIBUTES[i] for i in att_sym_diff]
            prefix = ' non '
        else:
            return '' if conjunction == 'or' else ' all'

        if len(attr_list) == 1:
            return prefix + attr_list[0]
        elif len(attributes) == 2:
            return prefix + ' '.join([attr_list[0], conjunction, attr_list[1]])
        else:
            return prefix + ', '.join(attr for attr in attr_list[:-1]) + ', {} {}'.format(conjunction, attr_list[-1])

    def fmt_multiplier_text(hp_mult, atk_mult, rcv_mult):
        return ''
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

    def fmt_reduct_text(shield, reduct_att=[0, 1, 2, 3, 4]):
        return ''
        if shield != 0:
            text = ''
            if reduct_att == [0, 1, 2, 3, 4]:
                text += 'reduce damage taken by {}%'.format(fmt_mult(shield * 100))
                return text
            else:
                color_text = attributes_format(reduct_att)
                text += 'reduce damage taken from ' + color_text + \
                        ' Att. by {}%'.format(fmt_mult(shield * 100))
                return text
        else:
            return None

    def passive_stats_convert(ls):
        skill_text = ''
        if ls.time > 0:
            skill_text += '[Fixed {} second movetime]; '.format(ls.time)
        skill_text += fmt_stats_type_attr_bonus(ls)
        if skill_text != '' and skill_text == '':
            skill_text += skill_text
        elif skill_text != '' and skill_text != '':
            skill_text += '; ' + skill_text

        if skill_text.endswith('; '):
            skill_text = skill_text[:-2]

        return skill_text

    def threshold_stats_convert(above, ls):
        skill_text = fmt_stats_type_attr_bonus(ls, reduce_join_txt=' and ', skip_attr_all=True)
        if ls.threshold != 1:
            skill_text += ' when above ' if above else ' when below '
            skill_text += fmt_mult(ls.threshold * 100) + '% HP'
        else:
            skill_text += ' when '
            skill_text += 'HP is full' if above else 'HP is not full'
        return skill_text

    def combo_match_convert(ls):
        max_combos = ls.max_combos
        min_combos = ls.min_combos
        min_atk_mult = ls.min_atk
        bonus_atk_mult = ls.bonus_atk

        skill_text = fmt_stats_type_attr_bonus(c, reduce_join_txt=' and ', skip_attr_all=True)
        skill_text += ' when {} or more combos'.format(min_combos)

        if min_combos != max_combos:
            max_mult = min_atk_mult + (max_combos - min_combos) * bonus_atk_mult
            skill_text += ' up to {}x at {} combos'.format(fmt_mult(max_mult), max_combos)

        return skill_text

    def attribute_match_convert(ls):
        skill_text = fmt_stats_type_attr_bonus(c, reduce_join_txt=' and ', skip_attr_all=True)

        max_attr = ls.max_attributes
        min_attr = ls.min_attributes
        attr = ls.attributes
        step = ls.atk_step
        max_mult = ls.max_atk

        if attr == [0, 1, 2, 3, 4]:
            skill_text += ' when matching {} or more colors'.format(min_attr)
            if step > 0:
                skill_text += ' up to {}x at {} colors'.format(fmt_mult(max_mult), max_attr)
        elif attr == [0, 1, 2, 3, 4, 5]:
            skill_text += ' when matching {} or more colors ({}+heal)'.format(
                min_attr, min_attr - 1)
            if step > 0:
                skill_text += ' up to {}x at 5 colors+heal'.format(
                    fmt_mult(max_mult), min_attr - 1)
        elif min_attr == max_attr and len(attr) > min_attr:
            attr_text = attributes_format(attr)
            skill_text += ' when matching ' + str(min_attr) + '+ of {} at once'.format(attr_text)
        else:
            attr_text = attributes_format(attr)
            skill_text += ' when matching {} at once'.format(attr_text)

        return skill_text

    def multi_attribute_match_convert(ls):
        attributes = ls.attributes
        if not attributes:
            return ''

        min_atk_mult = ls.min_atk
        min_match = ls.min_match
        bonus_atk_mult = ls.bonus_atk

        skill_text = fmt_stats_type_attr_bonus(ls, reduce_join_txt=' and ', skip_attr_all=True)

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

        return skill_text

    def mass_match_convert(ls):
        max_count = ls.max_count
        min_count = ls.min_count

        min_atk_mult = ls.min_atk
        attributes = ls.attributes
        bonus_atk_mult = ls.bonus_atk

        skill_text = fmt_stats_type_attr_bonus(ls, reduce_join_txt=' and ', skip_attr_all=True)

        skill_text += ' when matching ' + str(min_count)
        if max_count != min_count:
            skill_text += ' or more connected'

        skill_text += fmt_multi_attr(attributes) + ' orbs'

        if max_count != min_count and max_count > 0:
            max_atk = (max_count - min_count) * bonus_atk_mult + min_atk_mult
            skill_text += ' up to {}x at {} orbs'.format(fmt_mult(max_atk), max_count)

        return skill_text

    def after_attack_convert(ls):
        skill_text = fmt_mult(ls.multiplier) + 'x ATK additional damage when matching orbs'
        return skill_text

    def heal_on_convert(ls):
        skill_text = fmt_mult(ls.multiplier) + 'x RCV additional heal when matching orbs'
        return skill_text

    def resolve_convert(ls):
        skill_text = 'May survive when HP is reduced to 0 (HP>' + str(ls.threshold * 100).rstrip('0').rstrip('.') + '%)'
        return skill_text

    def bonus_time_convert(ls):
        skill_text = fmt_stats_type_attr_bonus(ls)

        if ls.time:
            if skill_text:
                skill_text += '; '

            skill_text += 'Increase orb movement time by ' + fmt_mult(ls.time) + ' seconds'

        return skill_text

    def counter_attack_convert(ls):
        if ls.chance == 1:
            skill_text = fmt_mult(ls.multiplier) + \
                         'x ' + ATTRIBUTES[ls.attributes[0]] + ' counterattack'
        else:
            skill_text = fmt_mult(ls.chance * 100) + '% chance to counterattack with ' + str(
                ls.multiplier).rstrip('0').rstrip('.') + 'x ' + ATTRIBUTES[ls.attributes[0]] + ' damage'

        return skill_text

    def egg_drop_convert(ls):
        skill_text = fmt_mult(ls.multiplier) + 'x Egg Drop rate'
        return skill_text

    def coin_drop_convert(ls):
        skill_text = fmt_mult(ls.multiplier) + 'x Coin Drop rate'
        return skill_text

    def skill_used_convert(ls):
        skill_text = fmt_stats_type_attr_bonus(ls, skip_attr_all=True)
        skill_text += ' on the turn a skill is used'
        return skill_text

    def exact_combo_convert(ls):
        skill_text = fmt_mult(ls.atk) + 'x ATK when exactly ' + str(ls.combos) + ' combos'
        return skill_text

    def passive_stats_type_atk_all_hp_convert(ls):
        skill_text = 'Reduce total HP by ' + \
                     fmt_mult((1 - ls.hp) * 100) + '%; ' + \
                     fmt_mult(ls.atk) + 'x ATK for '
        for i in ls.types[:-1]:
            skill_text += TYPES[i] + ', '
        skill_text += TYPES[int(ls.types[-1])] + ' type'

        return skill_text

    def team_build_bonus_convert(ls):
        skill_text = fmt_stats_type_attr_bonus(ls)
        skill_text += ' if ' + ','.join(ls.monster_ids) + ' is on the team'
        return skill_text

    def rank_exp_rate_convert(ls):
        skill_text = fmt_mult(ls.multiplier) + 'x Rank EXP'
        return skill_text

    def heart_tpa_stats_convert(ls):
        skill_text = fmt_mult(ls.rcv) + 'x RCV when matching 4 Heal orbs'
        return skill_text

    def five_orb_one_enhance_convert(ls):
        skill_text = fmt_mult(ls.atk) + 'x ATK for matched Att. when matching 5 Orbs with 1+ enhanced'
        return skill_text

    def heart_cross_convert(ls):
        skill_text = ''

        multiplier_text = fmt_multiplier_text(1, ls.atk, ls.rcv)
        if multiplier_text:
            skill_text += multiplier_text

        reduct_text = fmt_reduct_text(ls.damage_reduction)
        if reduct_text:
            skill_text += ' and ' + reduct_text if skill_text else reduct_text.capitalize()

        skill_text += ' when matching 5 Heal orbs in a cross formation'

        return skill_text

    def multi_play_convert(ls):
        skill_text = fmt_stats_type_attr_bonus(ls) + ' when in multiplayer mode'
        return skill_text

    def dual_passive_stat_convert(ls):
        c1 = {}
        c1['attributes'] = ls.attributes_1
        c1['types'] = ls.types_1
        c1['hp'] = ls.hp_1
        c1['atk'] = ls.atk_1
        c1['rcv'] = ls.rcv_1
        c2 = {}
        c2['attributes'] = ls.attributes_2
        c2['types'] = ls.types_2
        c2['hp'] = ls.hp_2
        c2['atk'] = ls.atk_2
        c2['rcv'] = ls.rcv_2
        skill_text = fmt_stats_type_attr_bonus(c1) + '; ' + fmt_stats_type_attr_bonus(c2)
        if c1['types'] == [] and c2['types'] == [] and c1['atk'] != 1 and c2['atk'] != 1:
            skill_text += '; ' + fmt_mult(c1['atk'] *
                                          c2['atk']) + 'x ATK for allies with both Att.'

        return skill_text

    def dual_threshold_stats_convert(ls):
        c1 = {}
        c1['attributes'] = ls.attributes
        c1['types'] = ls.types
        c1['above'] = ls.above_1
        c1['threshold'] = ls.threshold_1
        c1['atk'] = ls.atk_1
        c1['rcv'] = ls.rcv_1
        c1['damage_reduction'] = ls.damage_reduction_1
        c1['reduction_attributes'] = [0, 1, 2, 3, 4]
        c2 = {}
        c2['attributes'] = ls.attributes
        c2['types'] = ls.types
        c2['above'] = ls.above_2
        c2['threshold'] = ls.threshold_2
        c2['atk'] = ls.atk_2
        c2['rcv'] = ls.rcv_2
        c2['damage_reduction'] = ls.damage_reduction_2
        c2['reduction_attributes'] = [0, 1, 2, 3, 4]
        skill_text = ''
        if c1['atk'] != 0 or c1['rcv'] != 1 or c1['damage_reduction'] != 0:
            if c1['atk'] == 0:
                c1['atk'] = 1
            if c1['threshold'] == 1:
                skill_text = fmt_stats_type_attr_bonus(
                    c1, reduce_join_txt=' and ', skip_attr_all=True)
                skill_text += ' when HP is full' if c1['above'] else ' when HP is not full'
            else:
                skill_text = fmt_stats_type_attr_bonus(
                    c1, reduce_join_txt=' and ', skip_attr_all=True)
                skill_text += ' when above ' if c1['above'] else ' when below '
                skill_text += fmt_mult(c1['threshold'] * 100) + '% HP'

        if c2['threshold'] != 0:
            if skill_text != '':
                skill_text += '; '
            if c2['threshold'] == 1:
                skill_text += fmt_stats_type_attr_bonus(c2,
                                                        reduce_join_txt=' and ', skip_attr_all=True)
                skill_text += ' when HP is full' if c2['above'] else ' when HP is not full'
            else:
                skill_text += fmt_stats_type_attr_bonus(c2,
                                                        reduce_join_txt=' and ', skip_attr_all=True)
                skill_text += ' when above ' if c2['above'] else ' when below '
                skill_text += fmt_mult(c2['threshold'] * 100) + '% HP'

        return skill_text

    def color_cross_convert(ls):
        if len(ls.crosses) == 1:
            skill_text = fmt_mult(ls.crosses[0]['atk']) + 'x ATK for each cross of 5 ' + \
                         ATTRIBUTES[ls.crosses[0].attribute] + ' orbs'

        else:
            skill_text = fmt_mult(ls.crosses[0]['atk']) + 'x ATK for each cross of 5 '
            for i in range(0, len(ls.crosses))[:-1]:
                skill_text += ATTRIBUTES[ls.crosses[i]['attribute']] + ', '
            skill_text += ATTRIBUTES[ls.crosses[-1].attribute] + ' orbs'

        return skill_text

    def min_orb_convert(ls):
        skill_text = '[Unable to erase ' + str(ls.min_orb - 1) + ' orbs or less]; ' + fmt_stats_type_attr_bonus(ls)

        return skill_text

    def orb_remain_convert(ls):
        skill_text = '[No skyfall]'
        if ls.base_atk:
            skill_text += '; ' + fmt_mult(ls.base_atk) + 'x ATK when there are ' + \
                          str(ls.orb_count) + ' or fewer orbs remaining'
            if ls.bonus_atk != 0:
                skill_text += ' up to ' + fmt_mult(ls.atk) + 'x ATK when 0 orbs left'

        return skill_text

    def collab_bonus_convert(ls):
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
            76: 'Sword Art Online Collab',
            77: 'Kamen Rider Collab',
            78: 'Yo-kai Watch World Collab',
            83: 'Shaman King Collab',
            10001: 'Dragonbounds & Dragon Callers',
        }

        collab_id = ls.collab_id
        if collab_id not in COLLAB_MAP:
            print('Missing collab name for', collab_id)

        collab_name = COLLAB_MAP.get(collab_id, '<not populated>')
        skill_text = fmt_stats_type_attr_bonus(ls) + ' when all cards are from ' + collab_name

        return skill_text

    def multi_mass_match_convert(ls):
        if ls.atk not in [0, 1]:
            skill_text = fmt_multiplier_text(1, ls.atk, 1) + ' and increase '
        else:
            skill_text = 'Increase '
        skill_text += 'combo by {} when matching {} or more connected'.format(ls.add_combo, ls.min_orb)
        skill_text += fmt_multi_attr(ls.attributes, conjunction='and') + ' orbs at once'

        return skill_text

    def l_match_convert(ls):
        mult_text = fmt_multiplier_text(1, ls.atk, ls.rcv)
        reduct_text = fmt_reduct_text(ls.damage_reduction)
        if mult_text:
            skill_text = mult_text
            if reduct_text:
                skill_text += ' and ' + reduct_text
        elif reduct_text:
            skill_text = mult_text
        else:
            skill_text = '???'
        skill_text += ' when matching 5' + fmt_multi_attr(ls.attributes) + ' orbs in L shape'
        return skill_text

    def add_combo_att_convert(ls):
        attr = ls.attributes
        min_attr = ls.min_attr

        if ls.atk not in [0, 1]:
            skill_text = fmt_multiplier_text(1, ls.atk, 1) + ' and increase combo by {}'.format(
                ls.add_combo)
        else:
            skill_text = 'Increase combo by {}'.format(ls.add_combo)
        if attr == [0, 1, 2, 3, 4]:
            skill_text += ' when matching {} or more colors'.format(min_attr)
        elif attr == [0, 1, 2, 3, 4, 5]:
            skill_text += ' when matching {} or more colors ({}+heal)'.format(min_attr,
                                                                              min_attr - 1)
        else:
            attr_text = attributes_format(attr)
            skill_text += ' when matching {} at once'.format(attr_text)

        return skill_text

    def orb_heal_convert(ls):
        skill_text = ''

        if ls.atk != 1 and ls.atk != 0:
            skill_text += fmt_multiplier_text(1, ls.atk, 1)

        if ls.damage_reduction != 0:
            reduct_text = fmt_reduct_text(ls.damage_reduction)
            if skill_text:
                if ls.awk_unbind == 0:
                    skill_text += ' and '
                else:
                    skill_text += ', '
                skill_text += reduct_text
            else:
                skill_text += reduct_text[0].upper() + reduct_text[1:]

        if ls.awk_unbind != 0:
            skill_text += ' and reduce' if skill_text else 'Reduce'
            skill_text += ' awoken skill binds by {} turns'.format(ls.awk_unbind)

        skill_text += ' when recovering more than {} HP from Heal orbs'.format(ls.heal_amt)

        return skill_text

    def rainbow_bonus_damage_convert(ls):
        skill_text = '{} additional damage'.format(ls.bonus_damage)

        attr = ls.attributes
        min_attr = ls.min_attr

        if attr == [0, 1, 2, 3, 4]:
            skill_text += ' when matching {} or more colors'.format(min_attr)
        elif attr == [0, 1, 2, 3, 4, 5]:
            skill_text += ' when matching {} or more colors ({}+heal)'.format(
                min_attr, min_attr - 1)
        elif min_attr == ls.max_attr and len(attr) > min_attr:
            attr_text = attributes_format(attr)
            skill_text += ' when matching ' + str(min_attr) + '+ of {} at once'.format(attr_text)
        else:
            attr_text = attributes_format(attr)
            skill_text += ' when matching {} at once'.format(attr_text)
        return skill_text

    def mass_match_bonus_damage_convert(ls):
        skill_text = '{} TYPESadditional damage when matching {} or more'.format(ls.bonus_damage, ls.min_count)
        attr_text = fmt_multi_attr(ls.attributes)
        if attr_text:
            skill_text += '{} orbs'.format(attr_text)
        else:
            skill_text += ' orbs'

        return skill_text
