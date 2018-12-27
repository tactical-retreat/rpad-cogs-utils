"""
One-time load for dungeon mapping/ignore tables
"""
import argparse
from collections import defaultdict
import json
import logging
import os
import re

import feedparser
from pad_etl.common import monster_id_mapping
from pad_etl.data import bonus, card, dungeon, skill, extra_egg_machine
from pad_etl.processor import monster, monster_skill
from pad_etl.processor import skill_info
from pad_etl.processor.db_util import DbWrapper
from pad_etl.processor.merged_data import MergedBonus, MergedCard, CrossServerCard
from pad_etl.processor.news import NewsItem
from pad_etl.processor.schedule_item import ScheduleItem


logging.basicConfig()
logger = logging.getLogger('processor')
fail_logger = logging.getLogger('processor_failures')
fail_logger.setLevel(logging.INFO)

logging.getLogger().setLevel(logging.DEBUG)
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)


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
    inputGroup.add_argument("--dev", default=False, action="store_true", help="Should we run dev processes")
    inputGroup.add_argument("--input_dir", required=True,
                            help="Path to a folder where the input data is")

    outputGroup = parser.add_argument_group("Output")
    outputGroup.add_argument("--output_dir", required=True,
                             help="Path to a folder where output should be saved")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")
    return parser.parse_args()


def load_dungeon_lookups(db_wrapper):
    en_name_to_id = db_wrapper.load_to_key_value('name_us', 'dungeon_seq', 'dungeon_list', where_clause='show_yn=1')
    jp_name_to_id = db_wrapper.load_to_key_value('name_jp', 'dungeon_seq', 'dungeon_list', where_clause='show_yn=1')
    return en_name_to_id, jp_name_to_id


def normalize_dungeon_name(dungeon_name):
    dungeon_name = dungeon_name.lower()
    name_mapping = {
        'x1.5': '',
        'wood/dark': 'wd/dk',
        'no rcv/awoken skills': 'no rcv / awoken skills invalid',
    }
    for k, v in name_mapping.items():
        dungeon_name = dungeon_name.replace(k, v)
    dungeon_name = re.sub(r'[\W]+', ' ', dungeon_name).strip().upper()
    name_mapping = {
        'ALL THE SAME': '',
        'BOARD': ' ',
        'FR WT WD ONLY': ' '
    }
    for k, v in name_mapping.items():
        dungeon_name = dungeon_name.replace(k, v)
    dungeon_name = re.sub(r'[\W]+', ' ', dungeon_name).strip().upper()
    return dungeon_name

def find_dungeon_id(en_name_to_dungeon_id, jp_name_to_dungeon_id, clean_name):
    clean_name = normalize_dungeon_name(clean_name)
    dungeon_id = en_name_to_dungeon_id.get(clean_name, None)
    if dungeon_id is None:
        dungeon_id = jp_name_to_dungeon_id.get(clean_name, None)

    return dungeon_id

class MergedDungeon(object):
    def __init__(self, dungeon_id, jp_dungeon, na_dungeon):
        self.dungeon_id = dungeon_id
        self.jp_dungeon = jp_dungeon
        self.na_dungeon = na_dungeon or jp_dungeon
        self.pg_dungeon_id = None

def database_dungeon_match(db_wrapper, jp_database, na_database):
    en_name_to_dungeon_id_raw, jp_name_to_dungeon_id = load_dungeon_lookups(db_wrapper)
    
    normalized_en_names = [normalize_dungeon_name(x) for x in en_name_to_dungeon_id_raw.keys()]
    en_name_to_dungeon_id = {normalize_dungeon_name(x): y for x,y in en_name_to_dungeon_id_raw.items()}

    print('these should match')
    print('normalized names:', len(normalized_en_names))
    print('unique names:', len(en_name_to_dungeon_id))

    na_missing = []
    jp_missing = []
    ignored = []
    matched = []
    failed = []

    jp_dungeon_map = {x.dungeon_id: x for x in jp_database.dungeons}
    na_dungeon_map = {x.dungeon_id: x for x in na_database.dungeons}

    ignored_dungeon_names = [
        'start tower',
        'gift', '贈り物',
        'tournament', '杯',
        'challenge', 'チャレンジ',
        'プレゼン', # being present?
        'one-shot', '度きり',
        '-expert',
        '00 000', # Ignores coin dungeons from PG
        'anniversary', 'stream reward',
    ]

    dungeons = []
    for dungeon_id in sorted(jp_dungeon_map.keys()):
        jp_dungeon = jp_dungeon_map[dungeon_id]
        na_dungeon = na_dungeon_map.get(dungeon_id, None)
        if not na_dungeon:
            na_missing.append((dungeon_id, jp_dungeon))
        dungeons.append(MergedDungeon(dungeon_id, jp_dungeon, na_dungeon))
    

    for dungeon_id in sorted(na_dungeon_map.keys()):
        if dungeon_id not in jp_dungeon_map:
            jp_missing.append((dungeon_id, na_dungeon_map[dungeon_id]))

    pg_dungeon_ids_used = set()

    for dungeon in dungeons:
        skip = False
        if (dungeon.jp_dungeon.dungeon_comment == 'Retired Special Dungeons' or
            dungeon.jp_dungeon.alt_dungeon_type == 'Gift Dungeon'):
            ignored.append(dungeon)
            continue        

        for idn in ignored_dungeon_names:
            if idn in dungeon.na_dungeon.clean_name.lower() or idn in dungeon.jp_dungeon.clean_name:
                ignored.append(dungeon)
                skip = True 
                break;
        if skip:
            continue

        pg_dungeon_id = find_dungeon_id(en_name_to_dungeon_id, jp_name_to_dungeon_id, dungeon.jp_dungeon.clean_name)
        if not pg_dungeon_id:
            pg_dungeon_id = find_dungeon_id(en_name_to_dungeon_id, jp_name_to_dungeon_id, dungeon.na_dungeon.clean_name)
        
        if not pg_dungeon_id:
            failed.append(dungeon)
        else:
            pg_dungeon_ids_used.add(pg_dungeon_id)
            dungeon.pg_dungeon_id = pg_dungeon_id
            matched.append(dungeon)
               
    unmatched_pg = {}
    for name, pg_dungeon_id in en_name_to_dungeon_id_raw.items():
        if pg_dungeon_id in pg_dungeon_ids_used:
            continue
        clean_name = normalize_dungeon_name(name)
        skip = False    
        for idn in ignored_dungeon_names:
            if idn in clean_name.lower():
                skip = True
                break;
        if skip:
            continue
        unmatched_pg[pg_dungeon_id] = name

    print('\n\nsummary\n\n')
    print('na missing:', len(na_missing))
    print('jp_missing:', len(jp_missing))
    print('ignored:', len(ignored))
    print('matched:', len(matched))
    print('failed:', len(failed))
    print('unmatched_pg:', len(unmatched_pg))

    for data in na_missing:
        print('NA missing dungeon:', data[0], repr(data[1]))
    for data in jp_missing:
        print('JP missing dungeon:', data[0], repr(data[1]))
    for dungeon in ignored:
        print('ignored', dungeon.na_dungeon.clean_name)
    for dungeon in matched:
        print('matched', dungeon.na_dungeon.clean_name, 'to', dungeon.pg_dungeon_id)

    print('\n\nfailures\n\n')

    for dungeon in failed:
        print('lookup failed:', dungeon.dungeon_id)
        print('\t', repr(dungeon.na_dungeon))
        print('\t', repr(dungeon.jp_dungeon))
    
    for dungeon_id, name in unmatched_pg.items():
        print('unmatched_pg', name)


    for dungeon in matched:
        sql = 'insert into etl_dungeon_map (pad_dungeon_id, dungeon_seq) values ({}, {})'
        db_wrapper.insert_item(sql.format(dungeon.jp_dungeon.dungeon_id, dungeon.pg_dungeon_id))

    for dungeon in failed:
        sql = 'insert into etl_dungeon_ignore (pad_dungeon_id) values ({})' 
        db_wrapper.insert_item(sql.format(dungeon.jp_dungeon.dungeon_id))

def load_data(args):
    if args.logsql:
        logging.getLogger('database').setLevel(logging.DEBUG)
    dry_run = not args.doupdates

    input_dir = args.input_dir
    output_dir = args.output_dir

    logger.info('Loading data')
    jp_database = load_database(os.path.join(input_dir, 'jp'), 'jp')
    na_database = load_database(os.path.join(input_dir, 'na'), 'na')

    logger.info('Connecting to database')
    with open(args.db_config) as f:
        db_config = json.load(f)

    db_wrapper = DbWrapper(dry_run)
    db_wrapper.connect(db_config)

    logger.info('Starting JP event diff')
    database_dungeon_match(db_wrapper, jp_database, na_database)

    print('done')


def load_database(base_dir, pg_server):
    return Database(
        pg_server,
        dungeon.load_dungeon_data(data_dir=base_dir))


class Database(object):
    def __init__(self, pg_server, dungeons):
        self.pg_server = pg_server
        self.dungeons = dungeons


if __name__ == '__main__':
    args = parse_args()
    load_data(args)
