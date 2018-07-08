# from datetime import date, datetime, timedelta
import time
#
# from enum import Enum

from . import db_util
# from . import processor_util
from ..data.skill import MonsterSkill
from .merged_data import MergedCard


def get_monster_skill_ids(mc: MergedCard):
    args = {'monster_no': mc.card.card_id}
    sql = "SELECT ts_seq_leader, ts_seq_skill FROM monster_list WHERE monster_no = {monster_no}"
    return sql.format(**db_util.object_to_sql_params(args))


def get_update_monster_skill_ids(mc: MergedCard, ts_seq_leader: int, ts_seq_skill: int):
    args = {
        'ts_seq_leader': ts_seq_leader,
        'ts_seq_skill': ts_seq_skill,
        'monster_no': mc.card.card_id
    }
    sql = """
    UPDATE monster_list 
    SET ts_seq_leader = {ts_seq_leader}, ts_seq_skill = {ts_seq_skill} 
    WHERE monster_no = {monster_no}
    """
    return sql.format(**db_util.object_to_sql_params(args))


class MonsterSkillItem(object):
    def __init__(self, ts_seq: int, skill_jp: MonsterSkill, skill_na: MonsterSkill):
        # Primary key
        self.ts_seq = ts_seq

        # Not right but not useful either
        self.mag_atk = 0
        self.mag_hp = 0
        self.mag_rcv = 0
        self.reduce_dmg = 0

        # Not sure what this order is used for
        self.order_idx = 0

        # Used but not sure what for
        self.t_condition = 0

        # Seems (mostly) unused
        self.rta_seq_1 = None
        self.rta_seq_2 = None
        self.ta_seq_1 = 0
        self.ta_seq_2 = 0
        self.tt_seq_1 = 0
        self.tt_seq_2 = 0

        # Useful fields
        self.tstamp = int(time.time()) * 1000
        self.ts_desc_jp = skill_jp.clean_description
        self.ts_desc_kr = 'unknown_{}'.format(skill_jp.skill_id)
        self.ts_desc_us = skill_na.clean_description
        self.ts_name_jp = skill_jp.name
        self.ts_name_kr = 'unknown_{}'.format(skill_jp.skill_id)
        self.ts_name_us = skill_na.name
        self.turn_max = skill_jp.turn_max or 0
        self.turn_min = skill_jp.turn_min or 0

        self.search_data = '{} {}'.format(self.ts_name_jp, self.ts_name_us)

    def insert_sql(self):
        sql = """
        INSERT INTO `padguide`.`skill_list`
            (`mag_atk`,
            `mag_hp`,
            `mag_rcv`,
            `order_idx`,
            `reduce_dmg`,
            `rta_seq_1`,
            `rta_seq_2`,
            `search_data`,
            `ta_seq_1`,
            `ta_seq_2`,
            `tstamp`,
            `ts_desc_jp`,
            `ts_desc_kr`,
            `ts_desc_us`,
            `ts_name_jp`,
            `ts_name_kr`,
            `ts_name_us`,
            `ts_seq`,
            `tt_seq_1`,
            `tt_seq_2`,
            `turn_max`,
            `turn_min`,
            `t_condition`)
            VALUES
            ({mag_atk},
            {mag_hp},
            {mag_rcv},
            {order_idx},
            {reduce_dmg},
            {rta_seq_1},
            {rta_seq_2},
            {search_data},
            {ta_seq_1},
            {ta_seq_2},
            {tstamp},
            {ts_desc_jp},
            {ts_desc_kr},
            {ts_desc_us},
            {ts_name_jp},
            {ts_name_kr},
            {ts_name_us},
            {ts_seq},
            {tt_seq_1},
            {tt_seq_2},
            {turn_max},
            {turn_min},
            {t_condition});
        """
        return sql.format(**db_util.object_to_sql_params(self))

    def __repr__(self):
        return 'MonsterSkillItem({} - {})'.format(self.ts_seq, self.search_data)
>>>>>>> branch 'master' of https://github.com/nachoapps/rpad-cogs-utils.git
