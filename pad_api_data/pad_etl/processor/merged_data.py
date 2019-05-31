import logging
from datetime import datetime
from typing import List

import pytz

from . import enemy_skillset
from ..common import pad_util, monster_id_mapping
from ..data import BookCard, MonsterSkill, Dungeon

fail_logger = logging.getLogger('processor_failures')


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


def build_ownable_cross_server_cards(jp_database, na_database) -> List[CrossServerCard]:
    all_cards = build_cross_server_cards(jp_database, na_database)
    return list(filter(lambda c: c.monster_no > 0 and c.monster_no < 9000, all_cards))


def build_cross_server_cards(jp_database, na_database) -> List[CrossServerCard]:
    jp_card_ids = [mc.card.card_id for mc in jp_database.cards]
    jp_id_to_card = {mc.card.card_id: mc for mc in jp_database.cards}
    na_id_to_card = {mc.card.card_id: mc for mc in na_database.cards}

    # This is the list of cards we could potentially update
    combined_cards = []  # type: List[CrossServerCard]
    for card_id in jp_card_ids:
        jp_card = jp_id_to_card.get(card_id)
        na_card = na_id_to_card.get(monster_id_mapping.jp_id_to_na_id(card_id), jp_card)

        csc, err_msg = make_cross_server_card(jp_card, na_card)
        if csc:
            combined_cards.append(csc)
        elif err_msg:
            fail_logger.debug('Skipping card, %s', err_msg)

    return combined_cards


# Creates a CrossServerCard if appropriate.
# If the card cannot be created, provides an error message.
def make_cross_server_card(jp_card: MergedCard, na_card: MergedCard) -> (CrossServerCard, str):
    card_id = jp_card.card.card_id

    if '***' in jp_card.card.name or '???' in jp_card.card.name:
        return None, 'Skipping debug card: {}'.format(repr(jp_card))

    if '***' in na_card.card.name or '???' in na_card.card.name:
        # Card probably exists in JP but not in NA
        na_card = jp_card

    # Apparently some monsters can be ported to NA before their skills are
    if jp_card.leader_skill and not na_card.leader_skill:
        na_card.leader_skill = jp_card.leader_skill

    if jp_card.active_skill and not na_card.active_skill:
        na_card.active_skill = jp_card.active_skill

    if len(jp_card.enemy_behavior) != len(na_card.enemy_behavior):
        na_card.enemy_behavior = jp_card.enemy_behavior

    for idx in range(len(jp_card.enemy_behavior)):
        if type(jp_card.enemy_behavior[idx]) != type(na_card.enemy_behavior[idx]):
            na_card.enemy_behavior[idx] = jp_card.enemy_behavior[idx]
        else:
            # Fill the JP name in as a hack.
            na_card.enemy_behavior[idx].jp_name = jp_card.enemy_behavior[idx].name or na_card.enemy_behavior[idx].name

    monster_no = monster_id_mapping.jp_id_to_monster_no(card_id)
    return CrossServerCard(monster_no, jp_card, na_card), None


class CrossServerDungeon(object):
    def __init__(self, jp_dungeon: Dungeon, na_dungeon: Dungeon):
        self.dungeon_id = jp_dungeon.dungeon_id
        self.jp_dungeon = jp_dungeon
        self.na_dungeon = na_dungeon


def build_cross_server_dungeons(jp_database, na_database) -> List[CrossServerDungeon]:
    jp_dungeon_ids = [dungeon.dungeon_id for dungeon in jp_database.dungeons]
    jp_id_to_dungeon = {dungeon.dungeon_id: dungeon for dungeon in jp_database.dungeons}
    na_id_to_dungeon = {dungeon.dungeon_id: dungeon for dungeon in na_database.dungeons}

    # This is the list of dungeons we could potentially update
    combined_dungeons = []  # type: List[CrossServerDungeon]
    for dungeon_id in jp_dungeon_ids:
        jp_dungeon = jp_id_to_dungeon.get(dungeon_id)
        na_dungeon = na_id_to_dungeon.get(dungeon_id) # Might need a mapping like cards

        csc, err_msg = make_cross_server_dungeon(jp_dungeon, na_dungeon)
        if csc:
            combined_dungeons.append(csc)
        elif err_msg:
            fail_logger.debug('Skipping dungeon, %s', err_msg)

    return combined_dungeons


def make_cross_server_dungeon(jp_dungeon: Dungeon, na_dungeon: Dungeon) -> (CrossServerDungeon, str):
    jp_dungeon = jp_dungeon or na_dungeon
    na_dungeon = na_dungeon or jp_dungeon

    if '***' in jp_dungeon.clean_name or '???' in jp_dungeon.clean_name:
        return None, 'Skipping debug dungeon: {}'.format(repr(jp_dungeon))

    if '***' in na_dungeon.clean_name or '???' in na_dungeon.clean_name:
        # dungeon probably exists in JP but not in NA
        na_dungeon = jp_dungeon

    return CrossServerDungeon(jp_dungeon, na_dungeon), None
