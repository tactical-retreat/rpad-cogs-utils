"""
Loads the raw data files for NA/JP into intermediate structures, saves them,
then updates the database with the new data.  
"""
import argparse
from collections import defaultdict
from datetime import timedelta
import json
import logging
import os
import time

import feedparser
from pad_etl.common import monster_id_mapping
from pad_etl.data import card, skill
from pad_etl.data import database
from pad_etl.processor import skill_info
from pad_etl.processor.merged_data import MergedCard, CrossServerCard
from pad_etl.storage import egg
from pad_etl.storage import egg_processor
from pad_etl.storage import monster
from pad_etl.storage import monster_skill
from pad_etl.storage import skill_data
from pad_etl.storage import timestamp_processor

from pad_etl.storage.db_util import DbWrapper
from pad_etl.storage.news import NewsItem
from pad_etl.storage.schedule_item import ScheduleItem


logging.basicConfig()
logger = logging.getLogger('processor')
fail_logger = logging.getLogger('processor_failures')
fail_logger.setLevel(logging.INFO)

logging.getLogger().setLevel(logging.DEBUG)
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

human_fix_logger = logging.getLogger('human_fix')
if os.name != 'nt':
    human_fix_logger.addHandler(logging.FileHandler('/tmp/pipeline_human_fixes.txt', mode='w'))
human_fix_logger.setLevel(logging.INFO)


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
    inputGroup.add_argument("--dev", default=False, action="store_true",
                            help="Should we run dev processes")
    inputGroup.add_argument("--input_dir", required=True,
                            help="Path to a folder where the input data is")

    outputGroup = parser.add_argument_group("Output")
    outputGroup.add_argument("--output_dir", required=True,
                             help="Path to a folder where output should be saved")
    outputGroup.add_argument("--pretty", default=False, action="store_true",
                             help="Controls pretty printing of results")

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


def load_dungeon_mappings(db_wrapper):
    pad_id_to_dungeon_seq = db_wrapper.load_to_key_value(
        'pad_dungeon_id', 'dungeon_seq', 'etl_dungeon_map')
    pad_id_ignore = db_wrapper.load_to_key_value(
        'pad_dungeon_id', 'pad_dungeon_id', 'etl_dungeon_ignore')
    return pad_id_to_dungeon_seq, pad_id_ignore


def filter_events(bonuses):
    filtered_events = []
    for merged_event in bonuses:
        ignored_event_names = [
            'tournament_active',
            'tournament_closed',
            'score_announcement',
            'pem_event',
            'rem_event',
            'multiplayer_announcement',
            'monthly_quest_dungeon',
            'monthly_quest_info',
        ]
        allowed_nondungeon_events = [
            'Feed Skill-Up Chance',
            'Feed Exp Bonus Chance',
        ]
        bonus_name = merged_event.bonus.bonus_name
        bonus_message = merged_event.bonus.clean_message
        if bonus_name in ignored_event_names:
            fail_logger.debug('skipping ignored event: %s - %s', bonus_name, bonus_message)
        elif merged_event.open_duration() > timedelta(days=60):
            # No event should last this long
            fail_logger.debug('skipping long event: %s - %s', bonus_name, bonus_message)
        elif bonus_name in allowed_nondungeon_events:
            filtered_events.append(merged_event)
        elif not merged_event.dungeon:
            fail_logger.debug('skipping non-dungeon: %s - %s', bonus_name, bonus_message)
        else:
            filtered_events.append(merged_event)

    return filtered_events


def find_event_id(en_name_to_event_id, jp_name_to_event_id, merged_event):
    bonus_name = merged_event.bonus.bonus_name
    bonus_value = merged_event.bonus.bonus_value
    bonus_message = merged_event.bonus.clean_message

    message_replacements = {
        'Bosses drop 10 + Points!': '+10 Drop',
        'Bosses drop 30 + Points!': '+30 Drop',
        'Bosses drop 50 + Points!': '+50 Drop',
        'Bosses drop 99 + Points!': '+99 Drop',
        '※[+99] will be added to + Points': '+99 Drop',
    }

    for msg_in, msg_out in message_replacements.items():
        if bonus_message == msg_in:
            bonus_message = msg_out
            break

    # Disabled for now; this is putting in stuff like 'domain of the war dragons xp boost'
    message_builders = {
        #'Exp Boost': 'Exp x {}!',
        #'Coin Boost': 'Coin x {}!',
        #'Drop Boost': 'Drop% x {}!',
        #'Stamina Reduction': 'Stamina {}!',
    }

    if bonus_name in message_builders:
        bonus_message = message_builders[bonus_name].format(bonus_value)

    if bonus_name in en_name_to_event_id:
        return en_name_to_event_id[bonus_name]
    elif bonus_message in en_name_to_event_id:
        return en_name_to_event_id[bonus_message]
    elif bonus_message in jp_name_to_event_id:
        return jp_name_to_event_id[bonus_message]
    elif bonus_name == 'dungeon_special_event' and bonus_value == 10000:
        # These are PADR and other delayed dungeons
        fail_logger.debug('skipping unsupported padr/mail event: %s - %s - %s',
                          bonus_name, bonus_value, bonus_message)
    elif bonus_name == 'dungeon_special_event':
        # Random other text that I'm not parsing now (e.g. invade info, rank xp,
        # coins, stuff in mail)
        fail_logger.debug('skipping unsupported event text : %s - %s - %s',
                          bonus_name, bonus_value, bonus_message)
    elif bonus_name in ['daily_dragons']:
        fail_logger.info('skipping unsupported event: %s - %s - %s',
                         bonus_name, bonus_value, bonus_message)
        fail_logger.info('event: %s', repr(merged_event))
    elif bonus_name in ['dungeon']:
        # It's acceptable for a dungeon to not have an associated event
        return 0
    else:
        pad_dungeon_name = merged_event.dungeon.clean_name if merged_event.dungeon else ''
        fail_logger.warn('failed to match bonus name/message: (%s, %s) - (%s - %s)',
                         bonus_name, bonus_value,
                         bonus_message, pad_dungeon_name)
    return None


def find_dungeon_id(pad_id_to_dungeon_seq, pad_id_ignore, en_name_to_dungeon_id, jp_name_to_dungeon_id, merged_event):
    dungeon = merged_event.dungeon
    if dungeon:
        if dungeon.dungeon_id in pad_id_ignore:
            fail_logger.warn('current dungeon in ignore list: %s', repr(dungeon))
            return None
        elif dungeon.dungeon_id not in pad_id_to_dungeon_seq:
            fail_logger.warn('current dungeon has no mapping: %s', repr(dungeon))
            return None
        else:
            return pad_id_to_dungeon_seq[dungeon.dungeon_id]

    clean_name = None

    # Special processing for weird events
    if merged_event.bonus.bonus_name in ['Feed Skill-Up Chance', 'Feed Exp Bonus Chance']:
        clean_name = 'x{} Skill Up, Great/Super Chance'.format(merged_event.bonus.bonus_value)
    else:
        fail_logger.debug('skipping event with no dungeon and no override: %s', repr(merged_event))
        return None

    dungeon_id = en_name_to_dungeon_id.get(clean_name, None)
    if dungeon_id is None:
        dungeon_id = jp_name_to_dungeon_id.get(clean_name, None)

    if dungeon_id:
        return dungeon_id

    human_fix_logger.warn('critical failure, mapped event not found: %s', repr(merged_event))
    return None


def database_diff_events(db_wrapper, database):
    filtered_events = filter_events(database.bonuses)

    en_name_to_event_id, jp_name_to_event_id = load_event_lookups(db_wrapper)
    pad_id_to_dungeon_seq, pad_id_ignore = load_dungeon_mappings(db_wrapper)
    en_name_to_dungeon_id, jp_name_to_dungeon_id = load_dungeon_lookups(db_wrapper)

    schedule_events = []
    unmatched_events = []
    debug_events = []

    for merged_event in filtered_events:
        if merged_event.bonus.dungeon_floor_id:
            fail_logger.debug('skipping event for dungeon floor: %s', repr(merged_event))
            continue

        event_id = find_event_id(en_name_to_event_id, jp_name_to_event_id, merged_event)
        if event_id is None:
            fail_logger.debug('bailing early; event not found')
            continue
        dungeon_id = find_dungeon_id(pad_id_to_dungeon_seq, pad_id_ignore,
                                     en_name_to_dungeon_id, jp_name_to_dungeon_id, merged_event)

        if not dungeon_id:
            if merged_event.group:
                human_fix_logger.error('failed group lookup: %s', repr(merged_event))
            else:
                human_fix_logger.info('dungeon failed lookup: %s', repr(merged_event))
            unmatched_events.append(merged_event)
            continue

        schedule_item = ScheduleItem(merged_event, event_id, dungeon_id)
        if not schedule_item.is_valid():
            fail_logger.debug('skipping item: %s - %s', repr(merged_event), repr(schedule_item))
            continue
        else:
            debug_events.append((schedule_item, merged_event))
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

    print('dumping all events\n')
    for de in debug_events:
        print(repr(de[0]), repr(de[1]))


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

        def update_skill_data(ts_seq, as_desc=None, ls_desc=None):
            if not ts_seq or not (as_desc or ls_desc):
                return
            skill_data_item = db_wrapper.load_single_object(skill_data.SkillData, ts_seq)
            if not skill_data_item:
                skill_data_item = skill_data.SkillData(ts_seq=ts_seq)
            if as_desc:
                conditions = skill_data.parse_as_conditions(as_desc)
            else:
                conditions = skill_data.parse_ls_conditions(ls_desc)
            skill_data_item.type_data = skill_data.format_conditions(conditions)
            db_wrapper.insert_or_update(skill_data_item)

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

            update_skill_data(ts_seq_leader, ls_desc=calc_ls_skill_description)

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

            update_skill_data(ts_seq_skill, as_desc=calc_as_skill_description)

        if update_monster:
            logger.warn('Updating monster skill info: %s - %s - %s',
                        repr(merged_card), ts_seq_leader, ts_seq_skill)
            db_wrapper.insert_item(monster_skill.get_update_monster_skill_ids(
                merged_card, ts_seq_leader, ts_seq_skill))


def database_update_egg_machines(db_wrapper, jp_database, na_database):
    loader = egg.EggLoader(db_wrapper)
    loader.hide_outdated_machines()

    processor = egg_processor.EggProcessor()
    for em_json in jp_database.egg_machines + na_database.egg_machines:
        if em_json['end_timestamp'] < time.time():
            print('Skipping machine; looks closed', em_json['clean_name'])
            continue
        egg_title_list = processor.convert_from_json(em_json)
        loader.save_egg_title_list(egg_title_list)


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
    jp_database = database.Database('jp', input_dir)
    jp_database.load_database()

    na_database = database.Database('na', input_dir)
    na_database.load_database()

    if not args.skipintermediate:
        logger.info('Storing intermediate data')
        jp_database.save_all(output_dir, args.pretty)
        na_database.save_all(output_dir, args.pretty)

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

    logger.info('Starting egg machine update')
    try:
        database_update_egg_machines(db_wrapper, jp_database, na_database)
    except Exception as ex:
        print('updating egg machines failed', str(ex))

    logger.info('Starting news update')
    try:
        database_update_news(db_wrapper)
    except Exception as ex:
        print('updating news failed', str(ex))

    logger.info('Starting tstamp update')
    timestamp_processor.update_timestamps(db_wrapper)

    print('done')

if __name__ == '__main__':
    args = parse_args()
    load_data(args)
