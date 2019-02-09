from datetime import datetime

import pytz

from ..common import pad_util


class MergedBonus(pad_util.JsonDictEncodable):
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


class MergedCard(pad_util.JsonDictEncodable):
    def __init__(self, card, active_skill, leader_skill):
        self.card = card
        self.active_skill = active_skill
        self.leader_skill = leader_skill

    def __repr__(self):
        return 'MergedCard({} - {} - {})'.format(
            repr(self.card), repr(self.active_skill), repr(self.leader_skill))


class MergedEnemySkillset(pad_util.JsonDictEncodable):
    def __init__(self, enemy_skill_ref, enemy_skill, enemy_skill_set=None):
        self.enemy_skill_id = enemy_skill_ref.enemy_skill_id
        self.enemy_skill_ref = {'ai': enemy_skill_ref.enemy_ai, 'rnd': enemy_skill_ref.enemy_rnd}
        self.enemy_skill_info = {'name': enemy_skill.name,
                                 'type': enemy_skill.type, 'params': enemy_skill.params}

        self.enemy_skill_set = []
        if enemy_skill_set:
            self.enemy_skill_set = [{'name': es.name, 'type': es.type,
                                     'params': es.params} for es in enemy_skill_set]


class MergedEnemy(pad_util.JsonDictEncodable):
    def __init__(self, enemy_id: int, behavior):
        self.enemy_id = enemy_id
        self.behavior = behavior  # List[ESAction or ESLogic or ESPassive]


class CrossServerCard(object):
    def __init__(self, monster_no: int, jp_card: MergedCard, na_card: MergedCard):
        self.monster_no = monster_no
        self.jp_card = jp_card
        self.na_card = na_card
