"""
Loads the raw data files for NA/JP into intermediate structures, saves them,
then updates the database with the new data.  
"""
from collections import defaultdict
import json
import logging
import os

import argparse
import feedparser
from pad_etl.common import monster_id_mapping
from pad_etl.data import bonus, card, dungeon, skill
from pad_etl.processor import monster, monster_skill
from pad_etl.processor import skill_info
from pad_etl.processor.db_util import DbWrapper
from pad_etl.processor.merged_data import MergedBonus, MergedCard, CrossServerCard
from pad_etl.processor.schedule_item import ScheduleItem

from pad_etl.processor.news import NewsItem


logging.basicConfig()
logger = logging.getLogger('processor')
fail_logger = logging.getLogger('processor_failures')
fail_logger.setLevel(logging.INFO)

logging.getLogger().setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)


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
                    fail_logger.error('failed group lookup: %s', repr(merged_event))
                fail_logger.info('dungeon lookup failed: %s', repr(merged_event.dungeon))

        if not dungeon_id:
            fail_logger.info('unmatched record')
            unmatched_events.append(merged_event)
        else:
            schedule_item = ScheduleItem(merged_event, event_id, dungeon_id)
            if not schedule_item.is_valid():
                fail_logger.debug('skipping item: %s - %s - %s',
                                  repr(merged_event), event_id, dungeon_id)
                continue
            else:
                schedule_events.append(schedule_item)

    next_id = db_wrapper.get_single_value(
        'SELECT 1 + COALESCE(MAX(CAST(schedule_seq AS SIGNED)), 30000) FROM schedule_list', op=int)

    logger.info('updating event db starting at %i', next_id)

    for se in schedule_events:
        if db_wrapper.check_existing(se.exists_sql()):
            logger.debug('event already exists, skipping, %s', repr(se))
        else:
            logger.warn('inserting item: %s', repr(se))
            db_wrapper.insert_item(se.insert_sql(next_id))
            next_id += 1


# Creates a CrossServerCard if appropriate.
# If the card cannot be created, provides an error message.
def make_cross_server_card(jp_card: MergedCard, na_card: MergedCard) -> (CrossServerCard, str):
    card_id = jp_card.card.card_id
    if card_id <= 0 or card_id > 6000:
        return None, 'crazy id: {}'.format(repr(card))

    if '***' in jp_card.card.name or '???' in jp_card.card.name:
        return None, 'Skipping debug card: {}'.format(repr(card))

    if '***' in na_card.card.name or '???' in na_card.card.name:
        # Card probably exists in JP but not in NA
        na_card = jp_card

    # Apparently some monsters can be ported to NA before their skills are
    if jp_card.leader_skill and not na_card.leader_skill:
        na_card.leader_skill = jp_card.leader_skill

    if jp_card.active_skill and not na_card.active_skill:
        na_card.active_skill = jp_card.active_skill

    monster_no = monster_id_mapping.jp_id_to_monster_no(card_id)
    return CrossServerCard(monster_no, jp_card, na_card), None


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
        na_card = na_id_to_card.get(monster_id_mapping.jp_id_to_na_id(card_id), jp_card)

        csc, err_msg = make_cross_server_card(jp_card, na_card)
        if csc:
            combined_cards.append(csc)
        elif err_msg:
            fail_logger.debug('Skipping card, %s', err_msg)

    def insert_or_update(item: monster.SqlItem):
        # Check if the item exists by key
        if db_wrapper.check_existing(item.exists_sql()):
            # It exists, check if the updatable values have changed
            update_sql = item.needs_update_sql()
            if update_sql and not db_wrapper.check_existing(update_sql):
                logger.warn('Updating: %s', repr(item))
                db_wrapper.insert_item(item.update_sql())
            else:
                fail_logger.debug('Skipping existing item that needs no updates: %s', repr(item))
        else:
            # This is a new item, so populate it
            logger.warn('Inserting new item: %s', repr(item))
            db_wrapper.insert_item(item.insert_sql())

    # Base monster
    for csc in combined_cards:
        insert_or_update(monster.MonsterItem(csc.jp_card.card, csc.na_card.card))

    # Monster info
    for csc in combined_cards:
        insert_or_update(monster.MonsterInfoItem(csc.jp_card.card, csc.na_card.card))

    # Additional monster info
    for csc in combined_cards:
        insert_or_update(monster.MonsterAddInfoItem(csc.jp_card.card))

    # Monster prices
    for csc in combined_cards:
        insert_or_update(monster.MonsterPriceItem(csc.jp_card.card))

    # Awakenings
    awakening_name_and_id = db_wrapper.fetch_data(monster.awoken_name_id_sql())
    awoken_name_to_id = {row['name']: row['ts_seq'] for row in awakening_name_and_id}

    next_awakening_id = db_wrapper.get_single_value(
        'SELECT 1 + COALESCE(MAX(CAST(tma_seq AS SIGNED)), 20000) FROM awoken_skill_list', op=int)

    for csc in combined_cards:
        awakenings = monster.card_to_awakenings(awoken_name_to_id, csc.jp_card.card)
        for item in awakenings:
            tma_seq = db_wrapper.check_existing_value(item.exists_by_values_sql())
            if tma_seq:
                item.tma_seq = tma_seq
            else:
                item.tma_seq = next_awakening_id
                next_awakening_id += 1
            insert_or_update(item)

    # Evolutions
    next_evo_id = db_wrapper.get_single_value(
        'SELECT 1 + COALESCE(MAX(CAST(tv_seq AS SIGNED)), 4000) FROM evolution_list', op=int)

    for csc in combined_cards:
        evolution = monster.EvolutionItem(csc.jp_card.card)
        if not evolution.is_valid():
            continue
        if db_wrapper.check_existing(evolution.exists_sql()):
            fail_logger.debug('Skipping existing evolution: %s', repr(evolution))
        else:
            logger.warn('Inserting new evolution: %s', repr(evolution))
            db_wrapper.insert_item(evolution.insert_sql(next_evo_id))
            next_evo_id += 1

    # Try to populate series if missing.

    # First stage.
    # 1) Pull the list of monster_no -> series_id from the DB.
    # 2) For monsters with tsr_seq = 42, find the series of it's ancestor
    # 3) If that monster has a series != 42, apply it and save.
    monster_no_to_series_id = db_wrapper.load_to_key_value(
        'monster_no', 'tsr_seq', 'monster_info_list')  # type Map<int, int>

    for csc in combined_cards:
        if monster_no_to_series_id[csc.monster_no] != 42:
            continue
        ancestor_id = csc.jp_card.card.ancestor_id
        if ancestor_id == 0:
            continue
        ancestor_monster_no = monster_id_mapping.jp_id_to_monster_no(ancestor_id)
        ancestor_series = monster_no_to_series_id[ancestor_monster_no]
        if ancestor_series != 42:
            logger.warn('Detected new group ID for %s, %s', repr(csc.na_card.card), ancestor_series)
            db_wrapper.insert_item(monster.update_series_by_monster_no_sql(
                csc.monster_no, ancestor_series))

    # Second stage.
    # 1) Pull the list of monster_no -> series_id from the DB (again, may have been updated in step 1)
    # 2) Compile a list of group_id -> series_id (excluding premium, tsr_seq=42).
    # 3) Discard any group_id with more than one series_id.
    # 4) Iterate over every monster with series_id = 42. If the group_id has a series_id mapped,
    #    assign it and save.
    monster_no_to_series_id = db_wrapper.load_to_key_value(
        'monster_no', 'tsr_seq', 'monster_info_list')  # type Map<int, int>

    group_id_to_cards = defaultdict(list)  # type DefaultDict<GroupId, List[CrossServerCard]>
    for csc in combined_cards:
        group_id_to_cards[csc.jp_card.card.group_id].append(csc)

    group_id_to_series_id = {}  # type Map<int, int
    for group_id, card_list in group_id_to_cards.items():
        series_id = None
        for card in card_list:
            new_series_id = monster_no_to_series_id[card.monster_no]
            if new_series_id == 42:
                continue  # Skip premium
            if series_id != new_series_id:
                if series_id is None:
                    series_id = new_series_id
                else:
                    series_id = None
                    break
        if series_id is not None:
            group_id_to_series_id[group_id] = series_id

    for csc in combined_cards:
        series_id = monster_no_to_series_id[csc.monster_no]
        if series_id != 42:
            continue
        group_id = csc.jp_card.card.group_id
        if group_id in group_id_to_series_id:
            new_series_id = group_id_to_series_id[group_id]
            logger.warn('Detected new group ID for %s, %s', repr(csc.na_card.card), new_series_id)
            db_wrapper.insert_item(monster.update_series_by_monster_no_sql(
                csc.monster_no, new_series_id))

    # Evo mats
    next_evo_mat_id = db_wrapper.get_single_value(
        'SELECT 1 + COALESCE(MAX(CAST(tem_seq AS SIGNED)), 15000) FROM evo_material_list', op=int)

    for csc in combined_cards:
        card = csc.jp_card.card
        if not card.ancestor_id:
            continue
        tv_seq = db_wrapper.get_single_value(monster.lookup_evo_id_sql(card), op=int)
        evo_mat_items = monster.card_to_evo_mats(card, tv_seq)
        for item in evo_mat_items:
            tem_seq = db_wrapper.check_existing_value(item.exists_by_values_sql())
            if tem_seq:
                item.tem_seq = tem_seq
            else:
                item.tem_seq = next_evo_mat_id
                next_evo_mat_id += 1
            insert_or_update(item)

    # Skills
    next_skill_id = db_wrapper.get_single_value(
        'SELECT 1 + COALESCE(MAX(CAST(ts_seq AS SIGNED)), 20000) FROM skill_list', op=int)

    # Compute English skill text
    calc_skills = skill_info.reformat_json_info(jp_database.raw_skills)

    # Create a list of SkillIds to CardIds
    skill_id_to_card_ids = defaultdict(list)  # type DefaultDict<SkillId, List[CardId]>
    for merged_card in jp_database.cards:
        for skill in [merged_card.active_skill, merged_card.leader_skill]:
            if skill is None:
                continue
            skill_id_to_card_ids[skill.skill_id].append(merged_card.card.card_id)

    for csc in combined_cards:
        merged_card = csc.jp_card
        merged_card_na = csc.na_card
        monster_no = csc.monster_no

        info = db_wrapper.get_single_or_no_row(monster_skill.get_monster_skill_ids(merged_card))
        if not info:
            fail_logger.warn('Unexpected empty skill lookup: %s', repr(merged_card))
            continue

        def lookup_existing_skill_id(field_name, skill_id):
            alt_monster_no = monster_id_mapping.jp_id_to_monster_no(
                min(skill_id_to_card_ids[skill_id]))

            if alt_monster_no == monster_no:
                # No existing monster (by monster id order) has this skill
                return

            # An existing card already has this skill, look it up
            ts_seq = db_wrapper.get_single_value(
                "select {} from monster_list where monster_no = {}".format(field_name, alt_monster_no), op=int)
            logger.warn('Looked up existing skill id %s from %s for %s',
                        ts_seq, alt_monster_no, merged_card)
            return ts_seq

        def find_or_create_skill(monster_field_name, skill_value, na_skill_value, calc_skill_description):
            # Try to look up another monster with that skill
            ts_seq = lookup_existing_skill_id(monster_field_name, skill_value.skill_id)

            if ts_seq is None:
                # Lookup failed, insert a new skill
                nonlocal next_skill_id
                item = monster_skill.MonsterSkillItem(
                    next_skill_id, skill_value, na_skill_value, calc_skill_description)

                logger.warn('Inserting new monster skill: %s - %s',
                            repr(merged_card), repr(item))
                db_wrapper.insert_item(item.insert_sql())
                ts_seq = next_skill_id
                next_skill_id += 1

            return ts_seq

        def maybe_update_skill(ts_seq, skill_value, na_skill_value, calc_skill_description):
            # Skill exists, check if it needs an update
            item = monster_skill.MonsterSkillItem(
                ts_seq, skill_value, na_skill_value, calc_skill_description)

            if not db_wrapper.check_existing(item.exists_sql()):
                fail_logger.fatal('Unexpected empty skill lookup: %s', repr(item))
                exit()

            # It exists, check if the updatable values have changed
            if not db_wrapper.check_existing(item.needs_update_sql()):
                logger.warn('Updating: %s', repr(item))
                db_wrapper.insert_item(item.update_sql())
            else:
                fail_logger.debug(
                    'Skipping existing item that needs no updates: %s', repr(item))

        update_monster = False

        ts_seq_leader = info['ts_seq_leader']
        if merged_card.leader_skill:
            calc_ls_skill = calc_skills.get(merged_card.leader_skill.skill_id, '')
            calc_ls_skill_description = calc_ls_skill.description.strip() or None if calc_ls_skill else None
            if ts_seq_leader:
                # Monster already has a skill attached, see if it needs to be updated
                maybe_update_skill(ts_seq_leader, merged_card.leader_skill,
                                   merged_card_na.leader_skill, calc_ls_skill_description)
            else:
                # Skill needs to be attached
                ts_seq_leader = find_or_create_skill(
                    'ts_seq_leader', merged_card.leader_skill, merged_card_na.leader_skill, calc_ls_skill_description)
                update_monster = True

            if calc_ls_skill:
                leader_data_item = monster_skill.MonsterSkillLeaderDataItem(
                    ts_seq_leader, calc_ls_skill.params)
                if leader_data_item.leader_data:
                    insert_or_update(leader_data_item)

        ts_seq_skill = info['ts_seq_skill']
        if merged_card.active_skill:
            calc_as_skill = calc_skills.get(merged_card.active_skill.skill_id, '')
            calc_as_skill_description = calc_as_skill.description.strip() or None if calc_as_skill else None

            if ts_seq_skill:
                # Monster already has a skill attached, see if it needs to be updated
                maybe_update_skill(ts_seq_skill, merged_card.active_skill,
                                   merged_card_na.active_skill, calc_as_skill_description)
            else:
                ts_seq_skill = find_or_create_skill(
                    'ts_seq_skill', merged_card.active_skill, merged_card_na.active_skill, calc_as_skill_description)
                update_monster = True

        if update_monster:
            logger.warn('Updating monster skill info: %s - %s - %s',
                        repr(merged_card), ts_seq_leader, ts_seq_skill)
            db_wrapper.insert_item(monster_skill.get_update_monster_skill_ids(
                merged_card, ts_seq_leader, ts_seq_skill))


def database_update_news(db_wrapper):
    RENI_NEWS_JP = 'https://pad.protic.site/news/category/pad-jp/feed'
    jp_feed = feedparser.parse(RENI_NEWS_JP)
    next_id = db_wrapper.get_single_value(
        'SELECT 1 + COALESCE(MAX(CAST(tn_seq AS SIGNED)), 10000) FROM news_list', op=int)
    for entry in jp_feed.entries:
        item = NewsItem('JP', entry.title, entry.link)
        if db_wrapper.check_existing(item.exists_sql()):
            logger.debug('news already exists, skipping, %s', repr(item))
        else:
            logger.warn('inserting item: %s', repr(item))
            db_wrapper.insert_item(item.insert_sql(next_id))
            next_id += 1


def database_update_timestamps(db_wrapper):
    get_tables_sql = 'SELECT `internal_table` FROM get_timestamp'
    tables = list(map(lambda x: x['internal_table'], db_wrapper.fetch_data(get_tables_sql)))
    for table in tables:
        get_tstamp_sql = 'SELECT MAX(tstamp) as tstamp FROM `{}`'.format(table.lower() + '_list')
        try:
            tstamp_row = db_wrapper.get_single_or_no_row(get_tstamp_sql)
            if tstamp_row:
                tstamp = tstamp_row['tstamp']
                update_tstamp_sql = 'UPDATE get_timestamp SET tstamp = {} WHERE internal_table = "{}"'.format(
                    tstamp, table)
                db_wrapper.insert_item(update_tstamp_sql)
        except:
            pass  # table probably didn't exist


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

    logger.info('Starting news update')
    try:
        database_update_news(db_wrapper)
    except Exception as ex:
        print('updating news failed', str(ex))

    logger.info('Starting tstamp update')
    database_update_timestamps(db_wrapper)

    print('done')


def load_database(base_dir, pg_server):
    return Database(
        pg_server,
        card.load_card_data(data_dir=base_dir),
        dungeon.load_dungeon_data(data_dir=base_dir),
        {x: bonus.load_bonus_data(data_dir=base_dir, data_group=x) for x in 'abcde'},
        skill.load_skill_data(data_dir=base_dir),
        skill.load_raw_skill_data(data_dir=base_dir))


class Database(object):
    def __init__(self, pg_server, cards, dungeons, bonus_sets, skills, raw_skills):
        self.pg_server = pg_server
        self.raw_cards = cards
        self.dungeons = dungeons
        self.bonus_sets = bonus_sets
        self.skills = skills

        # This is temporary for the integration of calculated skills
        self.raw_skills = raw_skills

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

    # Shitty hack but I'm lazy and don't care
    if pg_server.upper() == 'NA':
        GROUP_TO_COLOR = {
            'A': 'RED',
            'B': 'GREEN',
            'C': 'RED',
            'D': 'RED',
            'E': 'BLUE',
        }
        SELECTED_STARTER_GROUPS = ['A', 'B', 'E']
    elif pg_server.upper() == 'JP':
        GROUP_TO_COLOR = {
            'A': 'RED',
            'B': 'RED',
            'C': 'GREEN',
            'D': 'BLUE',
            'E': 'BLUE',
        }
        SELECTED_STARTER_GROUPS = ['A', 'C', 'D']

    merged_bonuses = []
    for data_group, bonus_set in bonus_sets.items():
        starter = GROUP_TO_COLOR[data_group.upper()]

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
                merged_bonuses.append(MergedBonus(
                    pg_server, bonus, dungeon, guerrilla_group, starter))

    # Hacks for overriding guerrilla to starter
    # Figure out which guerrillas are starter based.
    # A bit awkward since we only have dupes for Red mostly, and an uneven number.
    starter_string_to_bonus = defaultdict(list)
    for bonus in merged_bonuses:
        starter_string_to_bonus[bonus.starter_unique_string].append(bonus)

    # Pick out the names for those guerrillas
    starter_guerrilla_dungeon_names = set()
    for bonus_list in starter_string_to_bonus.values():
        if len(bonus_list) > 1:
            dungeon = bonus_list[0].dungeon
            if dungeon and dungeon.dungeon_type == 'guerrilla':
                starter_guerrilla_dungeon_names.add(dungeon.clean_name)

    # Loop over the guerrillas checking against the names; if it's in the list
    # and from the selected 'normal' group, use it. If it's not in the list,
    # use it.
    final_bonuses = []
    for bonus in merged_bonuses:
        dungeon = bonus.dungeon
        if dungeon and dungeon.dungeon_type == 'guerrilla' and dungeon.clean_name in starter_guerrilla_dungeon_names:
            if bonus.group.upper() in SELECTED_STARTER_GROUPS:
                bonus.group = None
                final_bonuses.append(bonus)
        else:
            bonus.starter = None
            final_bonuses.append(bonus)

    return final_bonuses


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
