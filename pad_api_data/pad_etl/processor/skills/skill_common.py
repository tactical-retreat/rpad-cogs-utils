from operator import itemgetter


def fmt_mult(x):
    return str(round(float(x), 2)).rstrip('0').rstrip('.')


def multi_getattr(o, *args):
    for a in args:
        v = getattr(o, a, None)
        if v is not None:
            return v
    raise Exception('Attributs not found:' + str(args))


class BaseTextConverter(object):
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

    def attributes_format(self, attributes):
        return ', '.join([self.ATTRIBUTES[i] for i in attributes])

    def types_format(self, types):
        return ', '.join([self.TYPES[i] for i in types])

    def fmt_stats_type_attr_bonus(self, ls,
                                  reduce_join_txt='; ',
                                  skip_attr_all=True,
                                  atk=None,
                                  rcv=None):
        types = getattr(ls, 'types', [])
        attributes = getattr(ls, 'attributes', [])
        hp_mult = getattr(ls, 'hp', 1)
        # TODO: maybe we can just move min_atk and min_rcv in here
        # TODO: had to add all these getattr because this is being used in the active
        #       skill parser as well, is this right?
        atk_mult = atk or getattr(ls, 'atk', 1)
        rcv_mult = rcv or getattr(ls, 'rcv', 1)
        damage_reduct = getattr(ls, 'shield', 0)
        reduct_att = getattr(ls, 'reduction_attributes', [])
        skill_text = ''

        multiplier_text = self.fmt_multiplier_text(hp_mult, atk_mult, rcv_mult)
        if multiplier_text:
            skill_text += multiplier_text

            for_skill_text = ''
            if types:
                for_skill_text += ' ' + ', '.join([self.TYPES[i] for i in types]) + ' type'

            is_attr_all = len(attributes) in [0, 5]
            should_skip_attr = is_attr_all and skip_attr_all

            if attributes and not should_skip_attr:
                if for_skill_text:
                    for_skill_text += ' and'
                color_text = 'all' if len(attributes) == 5 else self.attributes_format(attributes)
                for_skill_text += ' ' + color_text + ' Att.'

            if for_skill_text:
                skill_text += ' for' + for_skill_text

        reduct_text = self.fmt_reduct_text(damage_reduct, reduct_att)
        if reduct_text:
            if multiplier_text:
                skill_text += reduce_join_txt
            if not skill_text or ';' in reduce_join_txt:
                reduct_text = reduct_text.capitalize()
            skill_text += reduct_text

        return skill_text

    def fmt_multi_attr(self, attributes, conjunction='or'):
        prefix = ' '
        if 1 <= len(attributes) <= 7:
            attr_list = [self.ATTRIBUTES[i] for i in attributes]
        elif 7 <= len(attributes) < 10:
            att_sym_diff = sorted(list(set(self.ATTRIBUTES) - set(attributes)), key=lambda x: self.ATTRIBUTES[x])
            attr_list = [self.ATTRIBUTES[i] for i in att_sym_diff]
            prefix = ' non '
        else:
            return '' if conjunction == 'or' else ' all'

        if len(attr_list) == 1:
            return prefix + attr_list[0]
        elif len(attributes) == 2:
            return prefix + ' '.join([attr_list[0], conjunction, attr_list[1]])
        else:
            return prefix + ', '.join(attr for attr in attr_list[:-1]) + ', {} {}'.format(conjunction, attr_list[-1])

    def fmt_multiplier_text(self, hp_mult, atk_mult, rcv_mult):
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

    def fmt_reduct_text(self, shield, reduct_att=None):
        if shield == 0:
            return None
        if reduct_att is None or reduct_att == [0, 1, 2, 3, 4]:
            return 'reduce damage taken by {}%'.format(fmt_mult(shield * 100))
        else:
            color_text = self.attributes_format(reduct_att)
            return 'reduce damage taken from ' + color_text + \
                   ' Att. by {}%'.format(fmt_mult(shield * 100))
