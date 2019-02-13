import time
from typing import List

from . import sql_item
from ..common import monster_id_mapping
from ..data.skill import MonsterSkill
from ..processor.merged_data import MergedCard
from .sql_item import SqlItem


def get_monster_skill_ids(mc: MergedCard):
    args = {'monster_no': monster_id_mapping.jp_id_to_monster_no(mc.card.card_id)}
    sql = "SELECT ts_seq_leader, ts_seq_skill FROM monster_list WHERE monster_no = {monster_no}"
    return sql.format(**sql_item.object_to_sql_params(args))


def get_update_monster_skill_ids(mc: MergedCard, ts_seq_leader: int, ts_seq_skill: int):
    args = {
        'ts_seq_leader': ts_seq_leader,
        'ts_seq_skill': ts_seq_skill,
        'monster_no': mc.card.card_id,
        'tstamp': int(time.time()) * 1000,
    }
    sql = """
    UPDATE monster_list 
    SET ts_seq_leader = {ts_seq_leader}, 
        ts_seq_skill = {ts_seq_skill},
        tstamp = {tstamp}
    WHERE monster_no = {monster_no}
    """
    return sql.format(**sql_item.object_to_sql_params(args))


class MonsterSkillItem(SqlItem):
    def __init__(self, ts_seq: int, skill_jp: MonsterSkill, skill_na: MonsterSkill, calc_skill_desc: str):
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
        self.ts_desc_us_calculated = calc_skill_desc
        self.ts_name_jp = skill_jp.name
        self.ts_name_kr = 'unknown_{}'.format(skill_jp.skill_id)
        self.ts_name_us = skill_na.name
        self.turn_max = skill_jp.turn_max or 0
        self.turn_min = skill_jp.turn_min or 0

        self.search_data = '{} {}'.format(self.ts_name_jp, self.ts_name_us)

    def _table(self):
        return 'skill_list'

    def _key(self):
        return 'ts_seq'

    def _insert_columns(self):
        return [
            'mag_atk',
            'mag_hp',
            'mag_rcv',
            'order_idx',
            'reduce_dmg',
            'rta_seq_1',
            'rta_seq_2',
            'search_data',
            'ta_seq_1',
            'ta_seq_2',
            'tstamp',
            'ts_desc_jp',
            'ts_desc_kr',
            'ts_desc_us',
            'ts_desc_us_calculated',
            'ts_name_jp',
            'ts_name_kr',
            'ts_name_us',
            'ts_seq',
            'tt_seq_1',
            'tt_seq_2',
            'turn_max',
            'turn_min',
            't_condition',
        ]

    def _update_columns(self):
        return ['ts_desc_us_calculated', 'turn_max', 'turn_min']

    def __repr__(self):
        return 'MonsterSkillItem({} - {})'.format(self.ts_seq, self.search_data)


class MonsterSkillLeaderDataItem(SqlItem):
    def __init__(self, ts_seq: int, params: List[float]):
        # Primary key
        self.ts_seq = ts_seq

        # 4 pipe delimited fields, each field is a condition
        # Slashes separate effects for conditions
        # 1: Code 1=HP, 2=ATK, 3=RCV, 4=Reduction
        # 2: Multiplier
        # 3: Color restriction (coded)
        # 4: Type restriction (coded)
        # 5: Combo restriction
        leader_data_parts = []
        for i in range(4):
            code = i + 1
            mult = params[i]
            if (mult != 1.0 and code != 4) or (mult > 0 and code == 4):
                mult_fmt = '{:.4f}'.format(mult).rstrip('0').rstrip('.')
                leader_data_parts.append('{}/{}///'.format(code, mult_fmt))

        self.leader_data = '|'.join(leader_data_parts)

        self.tstamp = int(time.time()) * 1000

    def _table(self):
        return 'skill_leader_data_list'

    def _key(self):
        return 'ts_seq'

    def _insert_columns(self):
        return [
            'leader_data',
            'ts_seq',
            'tstamp',
        ]

    def _update_columns(self):
        return ['leader_data']

    def __repr__(self):
        return 'MonsterSkillLeaderDataItem({} - {})'.format(self.ts_seq, self.leader_data)
