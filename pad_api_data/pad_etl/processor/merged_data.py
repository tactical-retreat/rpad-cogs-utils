from ..common import pad_util


class MergedBonus(pad_util.JsonDictEncodable):
    def __init__(self, server, bonus, dungeon, group):
        self.server = server
        self.bonus = bonus
        self.dungeon = dungeon
        self.group = group

        self.start_timestamp = pad_util.gh_to_timestamp(bonus.start_time_str, server)
        self.end_timestamp = pad_util.gh_to_timestamp(bonus.end_time_str, server)

    def __repr__(self):
        return 'MergedBonus({} {} - {} - {})'.format(
            self.server, self.group, repr(self.dungeon), repr(self.bonus))


class MergedCard(pad_util.JsonDictEncodable):
    def __init__(self, card, active_skill, leader_skill):
        self.card = card
        self.active_skill = active_skill
        self.leader_skill = leader_skill

    def __repr__(self):
        return 'MergedCard({} - {} - {})'.format(
            repr(self.card), repr(self.active_skill), repr(self.leader_skill))


class CrossServerCard(object):
    def __init__(self, jp_card: MergedCard, na_card: MergedCard):
        self.card_id = jp_card.card.card_id
        self.jp_card = jp_card
        self.na_card = na_card
