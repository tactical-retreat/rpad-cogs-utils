from datetime import date
import time

from . import db_util
from ..common import monster_id_mapping
from ..common import shared_types
from ..common.padguide_values import TYPE_MAP, AWAKENING_MAP, EvoType
from ..data.card import BookCard


class SqlItem(object):
    def exists_sql(self):
        sql = 'SELECT {} FROM {} WHERE {}'.format(
            self._key(), self._table(), self._col_compare(self._key()))
        return sql.format(**db_util.object_to_sql_params(self))

    def needs_update_sql(self):
        update_cols = self._update_columns()
        if update_cols is None:
            return False
        cols = [self._key()] + update_cols
        sql = 'SELECT {} FROM {} WHERE'.format(self._key(), self._table())
        sql += ' ' + ' AND '.join(map(self._col_compare, cols))
        formatted_sql = sql.format(**db_util.object_to_sql_params(self))
        fixed_sql = formatted_sql.replace('= NULL', 'is NULL')
        return fixed_sql

    def _col_compare(self, col):
        return col + ' = ' + self._col_value_ref(col)

    def _col_value_ref(self, col):
        return '{' + col + '}'

    def _col_name_ref(self, col):
        return '`' + col + '`'

    # TODO: move to dbutil
    def update_sql(self):
        cols = self._update_columns()
        if not cols:
            return None  # Update not supported

        # If an item is timestamped, modify the timestamp on every update
        if hasattr(self, 'tstamp'):
            cols = cols + ['tstamp']

        sql = 'UPDATE {}'.format(self._table())
        sql += ' SET ' + ', '.join(map(self._col_compare, cols))
        sql += ' WHERE ' + self._col_compare(self._key())
        return sql.format(**db_util.object_to_sql_params(self))

    def insert_sql(self):
        cols = self._insert_columns()
        return db_util.generate_insert_sql(self._table(), cols, self)

    def _table(self):
        raise NotImplemented('no table name set')

    def _key(self):
        raise NotImplemented('no key name set')

    def _insert_columns(self):
        raise NotImplemented('no insert columns set')

    def _update_columns(self):
        return None


class MonsterItem(SqlItem):
    def __init__(self, card: BookCard, card_na: BookCard):
        # Primary key
        self.monster_no = monster_id_mapping.jp_id_to_monster_no(card.card_id)
        self.monster_no_jp = card.card_id
        self.monster_no_kr = card.card_id
        self.monster_no_us = card_na.card_id

        # Flat values
        self.app_version = None
        self.atk_max = card.max_atk
        self.atk_min = card.min_atk
        self.comment_jp = None
        self.comment_kr = None
        self.comment_us = None
        self.cost = card.cost
        self.exp = 0  # Not actual value
        self.hp_max = card.max_hp
        self.hp_min = card.min_hp
        self.level = card.max_level
        self.limit_mult = card.limit_mult
        self.pronunciation_jp = card.furigana
        self.rarity = card.rarity
        self.ratio_atk = 1  # Not sure about this
        self.ratio_hp = 1  # Not sure about this
        self.ratio_rcv = 1  # Not sure about this
        self.rcv_max = card.max_rcv
        self.rcv_min = card.min_rcv
        self.reg_date = date.today().isoformat()
        self.tm_name_jp = card.name
        self.tm_name_kr = 'unknown_{}'.format(self.monster_no)
        self.tm_name_us = card_na.name
        self.tstamp = int(time.time()) * 1000

        if self.level == 1:
            self.exp = 0
        else:
            self.exp = shared_types.curve_value(
                0, card_na.xp_max, card_na.xp_scale, self.level, 99)

        # Foreign keys

        # There's a lookup table for this, but the colors are just offset by 1 (including null)
        self.ta_seq = card.attr_id + 1
        self.ta_seq_sub = card.sub_attr_id + 1

        # Exp value (wrong, needs a lookup)
        self.te_seq = 1

        # Unset by default
        self.ts_seq_leader = None
        self.ts_seq_skill = None

        # Hardcoded mapping because simple
        self.tt_seq = TYPE_MAP[card.type_1_id]
        self.tt_seq_sub = TYPE_MAP[card.type_2_id]

    def is_valid(self):
        return True

    def _table(self):
        return 'monster_list'

    def _key(self):
        return 'monster_no'

    def _insert_columns(self):
        return [
            'app_version',
            'atk_max', 'atk_min',
            'comment_jp', 'comment_kr', 'comment_us',
            'cost',
            'exp',
            'hp_max', 'hp_min',
            'level',
            'limit_mult',
            'monster_no', 'monster_no_jp', 'monster_no_kr', 'monster_no_us',
            'pronunciation_jp',
            'rarity',
            'ratio_atk', 'ratio_hp', 'ratio_rcv',
            'rcv_max', 'rcv_min',
            'reg_date',
            'ta_seq', 'ta_seq_sub',
            'te_seq',
            'tm_name_jp', 'tm_name_kr', 'tm_name_us',
            'tstamp',
            'ts_seq_leader', 'ts_seq_skill',
            'tt_seq', 'tt_seq_sub',
        ]

    def _update_columns(self):
        return ['tm_name_us', 'limit_mult', 'exp']

    def __repr__(self):
        return 'MonsterItem({} - {})'.format(self.monster_no, self.tm_name_us)


def update_series_by_monster_no_sql(monster_no, series_id):
    args = {
        'monster_no': monster_no,
        'tsr_seq': series_id,
        'tstamp': int(time.time()) * 1000,
    }
    sql = """
    UPDATE monster_info_list 
    SET tsr_seq = {tsr_seq},
        tstamp = {tstamp}
    WHERE monster_no = {monster_no}
    """
    return sql.format(**db_util.object_to_sql_params(args))


class MonsterInfoItem(SqlItem):
    def __init__(self, jp_card: BookCard, na_card: BookCard):
        self.fodder_exp = 0
        self.history_jp = '[{}] New Added'.format(date.today().isoformat())
        self.history_kr = self.history_jp
        self.history_us = self.history_jp
        self.monster_no = monster_id_mapping.jp_id_to_monster_no(jp_card.card_id)
        self.on_kr = 0
        self.on_us = 1 if jp_card != na_card and na_card.released_status else 0
        self.pal_egg = 0
        self.rare_egg = 0
        self.sell_price = 0
        self.tsr_seq = 42  # This is an unused series; should be replaced by the updater
        self.tstamp = int(time.time()) * 1000

    def _table(self):
        return 'monster_info_list'

    def _key(self):
        return 'monster_no'

    def _insert_columns(self):
        return [
            'fodder_exp',
            'history_jp', 'history_kr', 'history_us',
            'monster_no',
            'on_kr', 'on_us',
            'pal_egg', 'rare_egg',
            'sell_price',
            'tsr_seq',
            'tstamp',
        ]

    def _update_columns(self):
        return ['on_us']

    def __repr__(self):
        return 'MonsterInfoItem({})'.format(self.monster_no)


class MonsterPriceItem(SqlItem):
    def __init__(self, card: BookCard):
        self.monster_no = monster_id_mapping.jp_id_to_monster_no(card.card_id)
        self.buy_price = 0
        self.sell_price = card.sell_mp
        self.tstamp = int(time.time()) * 1000

    def _table(self):
        return 'monster_price_list'

    def _key(self):
        return 'monster_no'

    def _insert_columns(self):
        return ['buy_price', 'monster_no', 'sell_price', 'tstamp']

    def _update_columns(self):
        return ['sell_price']

    def __repr__(self):
        return 'MonsterPriceItem({})'.format(self.monster_no)


def awoken_name_id_sql():
    return """
        SELECT sl.ts_name_us as name, sl.ts_seq AS ts_seq
        FROM awoken_skill_list asl
        INNER JOIN skill_list sl 
        USING (ts_seq)
        GROUP BY 1, 2
        """


def card_to_awakenings(awoken_name_to_id, card: BookCard):
    results = []
    try:
        for awakening_id in card.awakenings:
            pg_awakening_name = AWAKENING_MAP[awakening_id]
            ts_seq = awoken_name_to_id[pg_awakening_name]
            results.append(MonsterAwakeningItem(card.card_id, len(results) + 1, ts_seq, 0))
        for awakening_id in card.super_awakenings:
            pg_awakening_name = AWAKENING_MAP[awakening_id]
            ts_seq = awoken_name_to_id[pg_awakening_name]
            results.append(MonsterAwakeningItem(card.card_id, len(results) + 1, ts_seq, 1))
    except Exception as e:
        print('EXCEPTION', e)
    return results


class MonsterAwakeningItem(SqlItem):
    def __init__(self, card_id: int, order_idx: int, ts_seq: int, is_super: int):
        # Unique ID
        self.tma_seq = None

        # Skill ID (awakening info)
        self.ts_seq = ts_seq

        self.monster_no = monster_id_mapping.jp_id_to_monster_no(card_id)
        self.order_idx = order_idx
        self.is_super = is_super

        self.del_yn = 0
        self.tstamp = int(time.time()) * 1000

    def exists_by_values_sql(self):
        sql = """
        SELECT tma_seq FROM awoken_skill_list
        WHERE monster_no = {monster_no} and order_idx = {order_idx}
        """.format(**db_util.object_to_sql_params(self))
        return sql

    def _table(self):
        return 'awoken_skill_list'

    def _key(self):
        return 'tma_seq'

    def _insert_columns(self):
        return [
            'del_yn',
            'is_super',
            'monster_no',
            'order_idx',
            'tma_seq',
            'tstamp',
            'ts_seq'
        ]

    def _update_columns(self):
        return ['is_super', 'ts_seq']

    def __repr__(self):
        return 'MonsterAwakeningItem({})'.format(self.monster_no)


class EvolutionItem(object):
    def __init__(self, card: BookCard):
        self.tv_seq = None

        self.to_no = monster_id_mapping.jp_id_to_monster_no(card.card_id)
        self.monster_no = monster_id_mapping.jp_id_to_monster_no(card.ancestor_id)
        self.tstamp = int(time.time()) * 1000

        # TODO: This is poorly done, but probably doesn't matter for my usage.
        # Doesn't handle UUVO properly.
        self.tv_type = EvoType.Evo.value  # Normal evo
        if card.is_ult:
            name = card.name.lower()
            if name.startswith('reincarnated') or '転生' in name:
                self.tv_type = EvoType.UuvoReincarnated.value
            else:
                self.tv_type = EvoType.UvoAwoken.value

    def is_valid(self):
        return self.monster_no != 0 and self.to_no != 0

    def exists_sql(self):
        sql = """SELECT tv_seq FROM evolution_list
                 WHERE to_no = {to_no}
                 """.format(**db_util.object_to_sql_params(self))
        return sql

    def insert_sql(self, tv_seq: int):
        self.tv_seq = tv_seq
        sql = """
        INSERT INTO `evolution_list`
            (`monster_no`, `to_no`, `tstamp`, `tv_seq`, `tv_type`)
            VALUES
            ({monster_no}, {to_no}, {tstamp}, {tv_seq}, {tv_type});
        """.format(**db_util.object_to_sql_params(self))
        return sql

    def __repr__(self):
        return 'EvolutionItem({} -> {})'.format(self.monster_no, self.to_no)


def lookup_evo_id_sql(card: BookCard):
    return 'select tv_seq from evolution_list where to_no = {}'.format(monster_id_mapping.jp_id_to_monster_no(card.card_id))


def card_to_evo_mats(card: BookCard, tv_seq: int):
    results = []
    if card.ancestor_id == 0:
        return results
    if card.evo_mat_id_1:
        results.append(EvolutionMaterialItem(card.evo_mat_id_1, 1, tv_seq))
    if card.evo_mat_id_2:
        results.append(EvolutionMaterialItem(card.evo_mat_id_2, 2, tv_seq))
    if card.evo_mat_id_3:
        results.append(EvolutionMaterialItem(card.evo_mat_id_3, 3, tv_seq))
    if card.evo_mat_id_4:
        results.append(EvolutionMaterialItem(card.evo_mat_id_4, 4, tv_seq))
    if card.evo_mat_id_5:
        results.append(EvolutionMaterialItem(card.evo_mat_id_5, 5, tv_seq))
    return results


class EvolutionMaterialItem(SqlItem):
    def __init__(self, mat_monster_id: int, order_idx: int, tv_seq: int):
        self.tem_seq = None
        self.monster_no = monster_id_mapping.jp_id_to_monster_no(mat_monster_id)
        self.order_idx = order_idx
        self.tv_seq = tv_seq
        self.tstamp = int(time.time()) * 1000

    def exists_by_values_sql(self):
        sql = """SELECT tem_seq FROM evo_material_list
                 WHERE order_idx = {order_idx} AND tv_seq = {tv_seq} 
                 """.format(**db_util.object_to_sql_params(self))
        return sql

    def _table(self):
        return 'evo_material_list'

    def _key(self):
        return 'tem_seq'

    def _insert_columns(self):
        return ['monster_no', 'order_idx', 'tem_seq', 'tstamp', 'tv_seq']

    def _update_columns(self):
        return ['monster_no']

    def __repr__(self):
        return 'EvolutionMaterialItem({} -> {})'.format(self.monster_no, self.tv_seq)


class MonsterAddInfoItem(SqlItem):
    def __init__(self, card: BookCard):
        self.extra_val1 = 1 if card.inheritable else 2
        self.monster_no = monster_id_mapping.jp_id_to_monster_no(card.card_id)
        self.sub_type = TYPE_MAP[card.type_3_id]
        self.tstamp = int(time.time()) * 1000

    def _table(self):
        return 'monster_add_info_list'

    def _key(self):
        return 'monster_no'

    def _insert_columns(self):
        return ['extra_val1', 'monster_no', 'sub_type', 'tstamp']

    def _update_columns(self):
        return ['extra_val1', 'sub_type']

    def __repr__(self):
        return 'MonsterInfoItem({} - {}/{})'.format(self.monster_no, self.extra_val1, self.sub_type)
