from datetime import date, datetime, timedelta
import time

from enum import Enum

from . import db_util
from . import processor_util
from .merged_data import MergedBonus, MergedCard

# Requires: monster_name, monster_id, active_name, leader_name
LOOKUP_SQL = """
SELECT 
    monster.monster_no AS monster_no, 
    active.ts_seq AS active_ts_seq, 
    leader.ts_seq AS leader_ts_seq
FROM monster_list AS monster
LEFT OUTER JOIN skill_list AS active
  ON monster.ts_seq_skill = active.ts_seq
LEFT OUTER JOIN skill_list AS leader
  ON monster.ts_seq_leader = leader.ts_seq
WHERE (monster.tm_name_us = {name} OR monster.tm_name_jp = {name})
AND (monster.monster_no_us = {monster_id} or monster_no_jp = {monster_id})
AND (active.ts_seq IS NULL OR active.ts_name_us = {active_name} OR active.ts_name_jp = {active_name})
AND (leader.ts_seq IS NULL OR leader.ts_name_us = {leader_name} OR leader.ts_name_jp = {leader_name})
"""


def get_monster_lookup_sql(card: MergedCard):
    inputs = {
        'name': card.card.name,
        'monster_id': str(card.card.card_id),
        'active_name': card.active_skill.name if card.active_skill else '',
        'leader_name': card.leader_skill.name if card.leader_skill else '',
    }
    return LOOKUP_SQL.format(**db_util.object_to_sql_params(inputs))


def get_monster_exists_sql(card: MergedCard):
    return "SELECT monster_no FROM monster_list WHERE monster_no = '{}'".format(card.card.card_id)


PAD_PADGUIDE_TYPES = {
    -1: 0,  # Not set
    0: 7,  # Evolve
    1: 1,  # Dragon
    2: 3,  # Physical
    3: 4,  # Healer
    4: 2,  # Balance
    5: 6,  # God
    6: 5,  # Attacker
    7: 10,  # Devil
    8: 14,  # Machine
    # x: 9,  # Protected (no longer exists)
    # 10/11 don't exist
    12: 13,  # Awoken
    # 13 doesn't exist
    14: 8,  # Enhance
    15: 15,  # Vendor
}


class MonsterItem(object):
    def __init__(self, merged_card_jp: MergedCard, merged_card_na: MergedCard):
        card = merged_card_jp.card

        # Primary key
        self.monster_no = int(card.card_id)
        self.monster_no_jp = int(self.monster_no)
        self.monster_no_kr = int(self.monster_no)
        self.monster_no_us = int(self.monster_no)

        # Flat values
        self.app_version = None
        self.atk_max = card.max_atk
        self.atk_min = card.min_atk
        self.comment_jp = None
        self.comment_kr = None
        self.comment_us = None  # Used for 'jp only' ?
        self.cost = card.cost
        self.exp = 0  # Not actual value
        self.hp_max = card.max_hp
        self.hp_min = card.min_hp
        self.level = card.max_level
        self.pronunciation_jp = card.furigana
        self.rarity = card.rarity
        self.ratio_atk = 1  # Not sure about this
        self.ratio_hp = 1  # Not sure about this
        self.ratio_rcv = 1  # Not sure about this
        self.rcv_max = card.max_rcv
        self.rcv_min = card.min_rcv
        self.reg_date = date.today().isoformat()
        self.tm_name_jp = merged_card_jp.card.name
        self.tm_name_kr = 'unknown_{}'.format(self.monster_no)
        self.tm_name_us = merged_card_na.card.name
        self.tstamp = int(time.time())

        # Foreign keys

        # There's a lookup table for this, but the colors are just offset by 1 (including null)
        self.ta_seq = card.attr_id + 1
        self.ta_seq_sub = card.sub_attr_id + 1

        # Exp value (wrong, needs a lookup)
        self.te_seq = 1

        # Unset by default
        self.ts_seq_leader = 0
        self.ts_seq_skill = 0

        # Hardcoded mapping because simple
        self.tt_seq = PAD_PADGUIDE_TYPES[card.type_1_id]
        self.tt_seq_sub = PAD_PADGUIDE_TYPES[card.type_2_id]

    def is_valid(self):
        return True

    def exists_sql(self):
        sql = """SELECT schedule_seq FROM schedule_list
                 WHERE open_timestamp = {open_timestamp}
                 AND close_timestamp = {close_timestamp}
                 AND server = {server}
                 AND event_seq = {event_seq}
                 AND dungeon_seq = {dungeon_seq}
                 """

        return sql.format(**db_util.object_to_sql_params(self))

    def insert_sql(self):
        sql = """
        INSERT INTO `padguide`.`monster_list`
            (`app_version`,
            `atk_max`,
            `atk_min`,
            `comment_jp`,
            `comment_kr`,
            `comment_us`,
            `cost`,
            `exp`,
            `hp_max`,
            `hp_min`,
            `level`,
            `monster_no`,
            `monster_no_jp`,
            `monster_no_kr`,
            `monster_no_us`,
            `pronunciation_jp`,
            `rarity`,
            `ratio_atk`,
            `ratio_hp`,
            `ratio_rcv`,
            `rcv_max`,
            `rcv_min`,
            `reg_date`,
            `ta_seq`,
            `ta_seq_sub`,
            `te_seq`,
            `tm_name_jp`,
            `tm_name_kr`,
            `tm_name_us`,
            `tstamp`,
            `ts_seq_leader`,
            `ts_seq_skill`,
            `tt_seq`,
            `tt_seq_sub`)
            VALUES
            ({app_version},
            {atk_max},
            {atk_min},
            {comment_jp},
            {comment_kr},
            {comment_us},
            {cost},
            {exp},
            {hp_max},
            {hp_min},
            {level},
            {monster_no},
            {monster_no_jp},
            {monster_no_kr},
            {monster_no_us},
            {pronunciation_jp},
            {rarity},
            {ratio_atk},
            {ratio_hp},
            {ratio_rcv},
            {rcv_max},
            {rcv_min},
            {reg_date},
            {ta_seq},
            {ta_seq_sub},
            {te_seq},
            {tm_name_jp},
            {tm_name_kr},
            {tm_name_us},
            {tstamp},
            {ts_seq_leader},
            {ts_seq_skill},
            {tt_seq},
            {tt_seq_sub});
            """.format(**db_util.object_to_sql_params(self))

        return sql

    def __repr__(self):
        return 'MonsterItem({} - {})'.format(self.monster_no, self.tm_name_us)


class MonsterInfoItem(object):
    def __init__(self, merged_card: MergedCard):
        self.fodder_exp = 0
        self.history_jp = '[{}] New Added'.format(date.today().isoformat())
        self.history_kr = self.history_jp
        self.history_us = self.history_jp
        self.monster_no = merged_card.card.card_id
        self.on_kr = 0
        self.on_us = 1
        self.pal_egg = 0
        self.rare_egg = 0
        self.sell_price = 0
        self.tsr_seq = 42  # This is an unused series; should be replaced by the updater
        self.tstamp = int(time.time())

    def exists_sql(self):
        sql = """SELECT monster_no FROM monster_info_list
                 WHERE monster_no = {monster_no}
                 """.format(**db_util.object_to_sql_params(self))
        return sql

    def insert_sql(self):
        sql = """
        INSERT INTO `padguide`.`monster_info_list`
            (`fodder_exp`,
            `history_jp`,
            `history_kr`,
            `history_us`,
            `monster_no`,
            `on_kr`,
            `on_us`,
            `pal_egg`,
            `rare_egg`,
            `sell_price`,
            `tsr_seq`,
            `tstamp`)
            VALUES
            ({fodder_exp},
            {history_jp},
            {history_kr},
            {history_us},
            {monster_no},
            {on_kr},
            {on_us},
            {pal_egg},
            {rare_egg},
            {sell_price},
            {tsr_seq},
            {tstamp});
            """.format(**db_util.object_to_sql_params(self))
        return sql

    def __repr__(self):
        return 'MonsterInfoItem({})'.format(self.monster_no)