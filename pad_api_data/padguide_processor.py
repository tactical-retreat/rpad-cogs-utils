"""
Loads the raw data files for NA/JP into intermediate structures, saves them,
then updates the database with the new data.  
"""
import argparse
from collections import defaultdict
import json
import logging
import os
from typing import DefaultDict

from pad_etl.common import padguide_values
from pad_etl.data import bonus, card, dungeon, skill
from pad_etl.processor import monster, monster_skill
from pad_etl.processor.db_util import DbWrapper
from pad_etl.processor.merged_data import MergedBonus, MergedCard, CrossServerCard
from pad_etl.processor.monster import awoken_name_id_sql
from pad_etl.processor.schedule_item import ScheduleItem


logging.basicConfig()
logger = logging.getLogger('processor')
fail_logger = logging.getLogger('processor_failures')

logging.getLogger().setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)
fail_logger.setLevel(logging.WARN)


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def parse_args():
    parser = argparse.ArgumentParser(description="Patches the PadGuide database.", add_help=False)
    parser.register('type', 'bool', str2bool)

    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--doupdates", default=False,
                            action="store_true", help="Enables actions")
    inputGroup.add_argument("--logsql", default=False,
                            action="store_true", help="Logs sql commands")
    inputGroup.add_argument("--skipintermediate", default=False,
                            action="store_true", help="Skips the slow intermediate storage")
    inputGroup.add_argument("--db_config", required=True, help="JSON database info")
    inputGroup.add_argument("--input_dir", required=True,
                            help="Path to a folder where the input data is")

    outputGroup = parser.add_argument_group("Output")
    outputGroup.add_argument("--output_dir", required=True,
                             help="Path to a folder where output should be saved")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")
    return parser.parse_args()


def load_event_lookups(db_wrapper):
    en_name_to_id = db_wrapper.load_to_key_value('event_name_us', 'event_seq', 'event_list')
    jp_name_to_id = db_wrapper.load_to_key_value('event_name_jp', 'event_seq', 'event_list')
    return en_name_to_id, jp_name_to_id


def load_dungeon_lookups(db_wrapper):
    en_name_to_id = db_wrapper.load_to_key_value('name_us', 'dungeon_seq', 'dungeon_list')
    jp_name_to_id = db_wrapper.load_to_key_value('name_jp', 'dungeon_seq', 'dungeon_list')
    return en_name_to_id, jp_name_to_id


def database_diff_events(db_wrapper, database):
    en_name_to_event_id, jp_name_to_event_id = load_event_lookups(db_wrapper)
    en_name_to_dungeon_id, jp_name_to_dungeon_id = load_dungeon_lookups(db_wrapper)

    schedule_events = []
    unmatched_events = []

    for merged_event in database.bonuses:
        event_id = None
        dungeon_id = None

        ignored_event_names = [
            'tournament_active',
            'tournament_closed',
            'score_announcement',
            'pem_event',
            'rem_event',
            'multiplayer_announcement',
            'monthly_quest_dungeon',
        ]

        bonus_name = merged_event.bonus.bonus_name
        bonus_message = merged_event.bonus.clean_message
        if bonus_name in ignored_event_names:
            fail_logger.debug('skipping announcement: %s - %s', bonus_name, bonus_message)
        elif bonus_name in en_name_to_event_id:
            event_id = en_name_to_event_id[bonus_name]
        elif bonus_message in en_name_to_event_id:
            event_id = en_name_to_event_id[bonus_message]
        elif bonus_message in jp_name_to_event_id:
            event_id = jp_name_to_event_id[bonus_message]
        elif bonus_name == 'dungeon' or 'daily_dragons':
            # No event expected
            # Currently not handling these
            pass
        elif bonus_name == 'dungeon_special_event':
            # Currently not handling these
            pass
        else:
            pad_event_value = merged_event.bonus.bonus_value
            pad_dungeon_name = merged_event.dungeon.clean_name if merged_event.dungeon else ''
            fail_logger.warn('failed to match bonus name/message: (%s, %s) - (%s - %s)',
                             bonus_name, pad_event_value,
                             bonus_message, pad_dungeon_name)

        if merged_event.dungeon:
            name_mapping = {
                '-Awoken Skills Invalid': ' [Awoken Skills Invalid]',
                '-Assists Invalid': ' [Assists Invalid]',
                '-Skills Invalid': ' [Skills Invalid]',
                '-All Att. Req.': ' [All Att. Req.]',
                '-No Continues': ' [No Continues]',
                '-No Dupes': ' [No Dupes]',
                '-No RCV': ' [No RCV]',
                '-No Fire': ' [No Fire]',
                '-No Water': ' [No Water]',
                '-No Wood': ' [No Wood]',
                '-No Light': ' [No Light]',
                '-No Dark': ' [No Dark]',
                '-Special': ' [Special]',
                '-7x6 Board': ' [7x6]',
                '-Tricolor': '-Tricolor [Fr/Wt/Wd Only]'
            }
            clean_name = merged_event.dungeon.clean_name
            for k, v in name_mapping.items():
                clean_name = clean_name.replace(k, v)
            dungeon_id = en_name_to_dungeon_id.get(clean_name, None)
            if dungeon_id is None:
                dungeon_id = jp_name_to_dungeon_id.get(clean_name, None)

            if dungeon_id is None:
                if merged_event.group:
                    fail_logger.warn('failed group lookup: %s', repr(merged_event))
                fail_logger.info('dungeon lookup failed: %s', repr(merged_event.dungeon))

        if not dungeon_id:
            fail_logger.info('unmatched record')
            unmatched_events.append(merged_event)
        else:
            schedule_item = ScheduleItem(merged_event, event_id, dungeon_id)
            if not schedule_item.is_valid():
                fail_logger.info('skipping item: %s - %s - %s',
                                 repr(merged_event), event_id, dungeon_id)
                continue
            else:
                schedule_events.append(schedule_item)

    next_id = db_wrapper.get_single_value(
        'SELECT 1 + COALESCE(MAX(CAST(schedule_seq AS SIGNED)), 30000) FROM schedule_list', op=int)

    logger.info('updating event db starting at %i', next_id)

    for se in schedule_events:
        if db_wrapper.check_existing(se.exists_sql()):
            logger.debug('event already exists, skipping')
        else:
            logger.debug('inserting item')
            db_wrapper.insert_item(se.insert_sql(next_id))
            next_id += 1


# Creates a CrossServerCard if appropriate.
# If the card cannot be created, provides an error message.
def make_cross_server_card(jp_card: MergedCard, na_card: MergedCard) -> (CrossServerCard, str):
    card_id = jp_card.card.card_id
    if card_id <= 0 or card_id > 6000:
        return None, 'crazy id: {}'.format(repr(card))

    if card_id < 3000:
        # ignoring older cards for now to get around the voltron issue
        # Eventually fix this using a hardcoded card mapping or something
        return None, None

    if '***' in jp_card.card.name or '???' in jp_card.card.name:
        return None, 'Skipping debug card: {}'.format(repr(card))

    if '***' in na_card.card.name or '???' in na_card.card.name:
        # Card probably exists in JP but not in NA
        na_card = jp_card

    return CrossServerCard(jp_card, na_card), None


def database_diff_cards(db_wrapper, jp_database, na_database):
    jp_card_ids = [mc.card.card_id for mc in jp_database.cards]
    jp_id_to_card = {mc.card.card_id: mc for mc in jp_database.cards}
    na_id_to_card = {mc.card.card_id: mc for mc in na_database.cards}

    if len(jp_card_ids) != len(jp_id_to_card):
        logger.error('Mismatched sizes: %s %s', len(jp_card_ids), len(jp_id_to_card))

    # This is the list of cards we could potentially update
    combined_cards = []  # List[CrossServerCard]
    for card_id in jp_card_ids:
        jp_card = jp_id_to_card.get(card_id)
        na_card = na_id_to_card.get(card_id, jp_card)

        csc, err_msg = make_cross_server_card(jp_card, na_card)
        if csc:
            combined_cards.append(csc)
        elif err_msg:
            fail_logger.debug('Skipping card, %s', err_msg)

    for csc in combined_cards:
        if db_wrapper.check_existing(monster.get_monster_exists_sql(csc.jp_card)):
            # Skipping existing card updates for now, inserts only
            fail_logger.debug('Skipping existing card: %s', repr(card))
        else:
            # This is a new card, so populate it
            new_monster = monster.MonsterItem(csc.jp_card, csc.na_card)
            logger.warn('Inserting new card: %s', repr(new_monster))
            db_wrapper.insert_item(new_monster.insert_sql())

    for csc in combined_cards:
        monster_info = monster.MonsterInfoItem(csc.jp_card)
        if db_wrapper.check_existing(monster_info.exists_sql()):
            fail_logger.debug('Skipping existing monster info: %s', repr(monster_info))
            pass
        else:
            logger.warn('Inserting new monster info: %s', repr(monster_info))
            db_wrapper.insert_item(monster_info.insert_sql())

    for csc in combined_cards:
        monster_price = monster.MonsterPriceItem(csc.jp_card.card)
        if db_wrapper.check_existing(monster_price.exists_sql()):
            fail_logger.debug('Skipping existing monster price: %s', repr(monster_price))
            pass
        else:
            logger.warn('Inserting new monster price: %s', repr(monster_price))
            db_wrapper.insert_item(monster_price.insert_sql())

    awakening_name_and_id = db_wrapper.fetch_data(monster.awoken_name_id_sql())
    awoken_name_to_id = {row['name']: row['ts_seq'] for row in awakening_name_and_id}

    next_awakening_id = db_wrapper.get_single_value(
        'SELECT 1 + COALESCE(MAX(CAST(tma_seq AS SIGNED)), 20000) FROM awoken_skill_list', op=int)

    # Awakenings
    for csc in combined_cards:
        awakenings = monster.card_to_awakenings(awoken_name_to_id, csc.jp_card.card)
        for item in awakenings:
            if db_wrapper.check_existing(item.exists_sql()):
                # Skipping existing card updates for now, inserts only
                fail_logger.debug('Skipping existing awakening: %s', repr(item))
            else:
                logger.warn('Inserting new awakening: %s', repr(item))
                db_wrapper.insert_item(item.insert_sql(next_awakening_id))
                next_awakening_id += 1

    next_skill_id = db_wrapper.get_single_value(
        'SELECT 1 + COALESCE(MAX(CAST(ts_seq AS SIGNED)), 20000) FROM skill_list', op=int)

    # Create a list of SkillIds to CardIds
    skill_id_to_card_ids = defaultdict(list)  # type DefaultDict<SkillId, List[CardId]>
    for merged_card in jp_database.cards:
        for skill in [merged_card.active_skill, merged_card.leader_skill]:
            if skill is None:
                continue
            skill_id_to_card_ids[skill.skill_id].append(merged_card.card.card_id)

    for csc in combined_cards:
        merged_card = csc.jp_card

        info = db_wrapper.get_single_or_no_row(monster_skill.get_monster_skill_ids(merged_card))
        if not info:
            fail_logger.warn('Unexpected empty skill lookup: %s', repr(merged_card))
            continue

        ts_seq_leader = info['ts_seq_leader']
        ts_seq_skill = info['ts_seq_skill']

        # Refactor this garbage code
        updated = False
        if ts_seq_leader is None and merged_card.leader_skill:
            alt_monster_no = min(skill_id_to_card_ids[merged_card.leader_skill.skill_id])

            if alt_monster_no < merged_card.card.card_id:
                # An existing card already has this skill, look it up
                ts_seq_leader = db_wrapper.get_single_value(
                    "select ts_seq_leader from monster_list where monster_no = {}".format(alt_monster_no), op=int)
                logger.warn('Looked up existing skill id %s from %s for %s',
                            ts_seq_leader, alt_monster_no, merged_card)
            else:
                skill_item = monster_skill.MonsterSkillItem(
                    next_skill_id, csc.jp_card.leader_skill, csc.na_card.leader_skill)
                logger.warn('Inserting new monster skill: %s - %s',
                            repr(merged_card), repr(skill_item))
                db_wrapper.insert_item(skill_item.insert_sql())
                ts_seq_leader = next_skill_id
                next_skill_id += 1
            updated = True

        if ts_seq_skill is None and merged_card.active_skill:
            alt_monster_no = min(skill_id_to_card_ids[merged_card.active_skill.skill_id])

            if alt_monster_no < merged_card.card.card_id:
                # An existing card already has this skill, look it up
                ts_seq_skill = db_wrapper.get_single_value(
                    "select ts_seq_skill from monster_list where monster_no = {}".format(alt_monster_no), op=int)
                logger.warn('Looked up existing skill id %s from %s for %s',
                            ts_seq_skill, alt_monster_no, merged_card)
            else:
                skill_item = monster_skill.MonsterSkillItem(
                    next_skill_id, csc.jp_card.active_skill, csc.na_card.active_skill)
                logger.warn('Inserting new monster skill: %s - %s',
                            repr(merged_card), repr(skill_item))
                db_wrapper.insert_item(skill_item.insert_sql())
                ts_seq_skill = next_skill_id
                next_skill_id += 1
            updated = True

        if updated:
            logger.warn('Updating monster skill info: %s - %s - %s',
                        repr(merged_card), ts_seq_leader, ts_seq_skill)
            db_wrapper.insert_item(monster_skill.get_update_monster_skill_ids(
                merged_card, ts_seq_leader, ts_seq_skill))


def load_data(args):
    if args.logsql:
        logging.getLogger('database').setLevel(logging.DEBUG)
    dry_run = not args.doupdates

    input_dir = args.input_dir
    output_dir = args.output_dir

    logger.info('Loading data')
    jp_database = load_database(os.path.join(input_dir, 'jp'), 'jp')
    na_database = load_database(os.path.join(input_dir, 'na'), 'na')

    if not args.skipintermediate:
        logger.info('Storing intermediate data')
        jp_database.save_all(output_dir)
        na_database.save_all(output_dir)

    logger.info('Connecting to database')
    with open(args.db_config) as f:
        db_config = json.load(f)

    db_wrapper = DbWrapper(dry_run)
    db_wrapper.connect(db_config)

    logger.info('Starting JP event diff')
    database_diff_events(db_wrapper, jp_database)

    logger.info('Starting NA event diff')
    database_diff_events(db_wrapper, na_database)

    logger.info('Starting card diff')
    database_diff_cards(db_wrapper, jp_database, na_database)

    print('done')


def load_database(base_dir, pg_server):
    return Database(
        pg_server,
        card.load_card_data(data_dir=base_dir),
        dungeon.load_dungeon_data(data_dir=base_dir),
        {x: bonus.load_bonus_data(data_dir=base_dir, data_group=x) for x in 'abcde'},
        skill.load_skill_data(data_dir=base_dir))


class Database(object):
    def __init__(self, pg_server, cards, dungeons, bonus_sets, skills):
        self.pg_server = pg_server
        self.raw_cards = cards
        self.dungeons = dungeons
        self.bonus_sets = bonus_sets
        self.skills = skills

        self.bonuses = clean_bonuses(pg_server, bonus_sets, dungeons)
        self.cards = clean_cards(cards, skills)

    def save_all(self, output_dir: str):
        def save(file_name: str, obj: object):
            output_file = os.path.join(output_dir, '{}_{}.json'.format(self.pg_server, file_name))
            with open(output_file, 'w') as f:
                json.dump(obj, f, indent=4, sort_keys=True, default=lambda x: x.__dict__)
        save('raw_cards', self.raw_cards)
        save('dungeons', self.dungeons)
        save('skills', self.skills)
        save('bonuses', self.bonuses)
        save('cards', self.cards)


def clean_bonuses(pg_server, bonus_sets, dungeons):
    dungeons_by_id = {d.dungeon_id: d for d in dungeons}

    merged_bonuses = []
    for data_group, bonus_set in bonus_sets.items():
        for bonus in bonus_set:
            dungeon = None
            guerrilla_group = None
            if bonus.dungeon_id:
                dungeon = dungeons_by_id.get(bonus.dungeon_id, None)
                if dungeon is None:
                    fail_logger.critical('Dungeon lookup failed for bonus: %s', repr(bonus))
                else:
                    guerrilla_group = data_group if dungeon.dungeon_type == 'guerrilla' else None

            if guerrilla_group or data_group == 'a':
                merged_bonuses.append(MergedBonus(pg_server, bonus, dungeon, guerrilla_group))

    return merged_bonuses


def clean_cards(cards, skills):
    skills_by_id = {s.skill_id: s for s in skills}

    merged_cards = []
    for card in cards:
        active_skill = None
        leader_skill = None

        if card.active_skill_id:
            active_skill = skills_by_id.get(card.active_skill_id, None)
            if active_skill is None:
                fail_logger.critical('Active skill lookup failed: %s - %s',
                                     repr(card), card.active_skill_id)

        if card.leader_skill_id:
            leader_skill = skills_by_id.get(card.leader_skill_id, None)
            if leader_skill is None:
                fail_logger.critical('Leader skill lookup failed: %s - %s',
                                     repr(card), card.leader_skill_id)

        merged_cards.append(MergedCard(card, active_skill, leader_skill))
    return merged_cards


if __name__ == '__main__':
    args = parse_args()
    load_data(args)
