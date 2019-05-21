from datetime import datetime
from typing import List

import pytz

from ..data import BookCard, MonsterSkill
from . import enemy_skillset
from ..common import pad_util


class MergedBonus(object):
    def __init__(self, server, bonus, dungeon, group):
        self.server = server
        self.bonus = bonus
        self.dungeon = dungeon
        self.group = group
        self.is_starter = group in ['red', 'green', 'blue']

        self.start_timestamp = pad_util.gh_to_timestamp(bonus.start_time_str, server)
        self.end_timestamp = pad_util.gh_to_timestamp(bonus.end_time_str, server)

    def __repr__(self):
        return 'MergedBonus({} {} - {} - {})'.format(
            self.server, self.group, repr(self.dungeon), repr(self.bonus))

    def open_duration(self):
        open_datetime_utc = datetime.fromtimestamp(self.start_timestamp, pytz.UTC)
        close_datetime_utc = datetime.fromtimestamp(self.end_timestamp, pytz.UTC)
        return close_datetime_utc - open_datetime_utc


class MergedCard(object):
    def __init__(self, card: BookCard,
                 active_skill: MonsterSkill,
                 leader_skill: MonsterSkill,
                 enemy_behavior: List[enemy_skillset.ESBehavior]):
        self.card = card
        self.active_skill = active_skill
        self.leader_skill = leader_skill
        self.enemy_behavior = enemy_behavior

    def __repr__(self):
        return 'MergedCard({} - {} - {})'.format(
            repr(self.card), repr(self.active_skill), repr(self.leader_skill))


class MergedEnemy(object):
    def __init__(self, enemy_id: int, behavior: List[enemy_skillset.ESBehavior]):
        self.enemy_id = enemy_id
        self.behavior = behavior


class CrossServerCard(object):
    def __init__(self, monster_no: int, jp_card: MergedCard, na_card: MergedCard):
        self.monster_no = monster_no
        self.jp_card = jp_card
        self.na_card = na_card
