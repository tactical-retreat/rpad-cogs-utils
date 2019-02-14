import argparse
import json
import shutil

import pymysql

import db_util
import encoding
from extract_utils import fix_row
import sqlite3 as lite


# The PadGuide SQLite database has a lot of stuff in it that I don't know what to do with.
# Just update the tables we're managing.
# The base database should have the updated tables empty.
# This maps MySql db table names to SQLite table names.
TBL_MAPPING = {
    'awoken_skill_list': 'TBL_MONSTER_AWOKEN_SKILL',
    'coin_rotation_list': 'TBL_COIN_ROTATION',
    'dungeon_list': 'TBL_DUNGEON',
    'dungeon_monster_list': 'TBL_DUNGEON_MONSTER',
    'dungeon_monster_drop_list': 'TBL_DUNGEON_MONSTER_DROP',
    'sub_dungeon_list': 'TBL_SUB_DUNGEON',
    'dungeon_skill_list': 'TBL_DUNGEON_SKILL',
    'dungeon_skill_damage_list': 'TBL_DUNGEON_SKILL_DAMAGE',
    'egg_monster_list': 'TBL_EGG_MONSTER',
    'egg_title_list': 'TBL_EGG_TITLE',
    'egg_title_name_list': 'TBL_EGG_TITLE_NAME',
    'evolution_list': 'TBL_EVOLUTION',
    'evo_material_list': 'TBL_EVO_MATERIAL',
    'monster_add_info_list': 'TBL_MONSTER_ADD_INFO',
    'monster_info_list': 'TBL_MONSTER_INFO',
    'monster_list': 'TBL_MONSTER',
    'monster_price_list': 'TBL_MONSTER_PRICE',
    'skill_leader_data_list': 'TBL_SKILL_LEADER_DATA',
    'skill_list': 'TBL_SKILL',
    'skill_rotation_list': 'TBL_SKILL_ROTATION_LIST',
    'sub_dungeon_point_list': 'TBL_SUB_DUNGEON_POINT',
    'sub_dungeon_reward_list': 'TBL_SUB_DUNGEON_REWARD',
    'sub_dungeon_score_list': 'TBL_SUB_DUNGEON_SCORE',
}

# Names of columns that should be encrypted
ENCRYPTED_COLUMNS = [
    'SELL_PRICE', 'FODDER_EXP',
    'TS_NAME_JP', 'TS_NAME_US', 'TS_NAME_KR',
    'TS_DESC_JP', 'TS_DESC_US', 'TS_DESC_KR',
    'COMMENT_JP', 'COMMENT_US', 'COMMENT_KR',
    'HISTORY_JP', 'HISTORY_US', 'HISTORY_KR',
    'TSD_NAME_JP', 'TSD_NAME_US', 'TSD_NAME_KR',
]


def encrypt_cols(row):
    fixed_row = {}
    for key, value in row.items():
        fixed_row[key] = encoding.encode(value) if key in ENCRYPTED_COLUMNS else value
    return fixed_row


def parse_args():
    parser = argparse.ArgumentParser(
        description="Converts PadGuide data to SQLite.", add_help=False)

    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--db_config", required=True, help="JSON database info")
    inputGroup.add_argument("--base_db", required=True, help="Base SQLite file to work with")

    outputGroup = parser.add_argument_group("Output")
    outputGroup.add_argument("--output_file", required=True, help="SQLite file to write to")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")

    return parser.parse_args()


def do_main(args):
    # File must be named Panda.sql
    # Add zipping the sql
    output_file = args.output_file
    shutil.copy(args.base_db, output_file)

    with open(args.db_config) as f:
        db_config = json.load(f)

    # Connect to the database
    mysql_conn = pymysql.connect(host=db_config['host'],
                                 user=db_config['user'],
                                 password=db_config['password'],
                                 db=db_config['db'],
                                 charset=db_config['charset'],
                                 cursorclass=pymysql.cursors.DictCursor)

    sqlite_conn = lite.connect(output_file, detect_types=lite.PARSE_DECLTYPES, isolation_level=None)
    sqlite_conn.row_factory = lite.Row
    sqlite_conn.execute('pragma foreign_keys=OFF')

    for src_tbl, dest_tbl in TBL_MAPPING.items():
        dest_truncate_sql = 'DELETE FROM {}'.format(dest_tbl)
        sqlite_conn.execute(dest_truncate_sql)

        dest_select_sql = 'SELECT * FROM {}'.format(dest_tbl)
        dest_cols = set([desc[0].lower()
                         for desc in sqlite_conn.execute(dest_select_sql).description])

        with mysql_conn.cursor() as cursor:
            src_select_sql = 'SELECT * FROM {}'.format(src_tbl)
            cursor.execute(src_select_sql)
            src_cols = set([desc[0].lower() for desc in cursor.description])

            skipped_src_cols = src_cols - dest_cols
            skipped_dest_cols = dest_cols - src_cols
            print("for", src_tbl, 'skipping', skipped_src_cols)
            print("for", dest_tbl, 'skipping', skipped_dest_cols)
            for row in cursor:
                fixed_row = fix_row(src_tbl, row)
                encrypted_row = encrypt_cols(fixed_row)
                insert_cols = set(encrypted_row.keys()).intersection(map(str.upper, dest_cols))
                insert_sql = db_util.generate_insert_sql(dest_tbl, insert_cols, encrypted_row)
                sqlite_conn.execute(insert_sql)

    sqlite_conn.close()
    mysql_conn.close()


if __name__ == '__main__':
    args = parse_args()
    do_main(args)
