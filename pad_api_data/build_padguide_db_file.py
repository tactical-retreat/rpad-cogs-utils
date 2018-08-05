import argparse
import datetime
import json
import os
import shutil

from pad_etl.processor import db_util
from padguide.extract_utils import fix_table_name, fix_row
import pymysql
from padguide import encoding

import sqlite3 as lite


# The PadGuide SQLite database has a lot of stuff in it that I don't know what to do with.
# Just update the tables we're managing.
# The base database should have the updated tables empty.
# This maps MySql db table names to SQLite table names.
TBL_MAPPING = {
    'monster_list': 'TBL_MONSTER',
    'monster_info_list': 'TBL_MONSTER_INFO',
    'monster_price_list': 'TBL_MONSTER_PRICE',
    'awoken_skill_list': 'TBL_MONSTER_AWOKEN_SKILL',
    'evo_material_list': 'TBL_EVO_MATERIAL',
    'monster_add_info_list': 'TBL_MONSTER_ADD_INFO',
    'skill_list': 'TBL_SKILL',
    'skill_leader_data_list': 'TBL_SKILL_LEADER_DATA',
}

# Names of columns that should be encrypted
ENCRYPTED_COLUMNS = [
    'SELL_PRICE', 'FODDER_EXP',
    'TS_NAME_JP', 'TS_NAME_US', 'TS_NAME_KR',
    'TS_DESC_JP', 'TS_DESC_US', 'TS_DESC_KR',
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
    inputGroup.add_argument("--base_db", required=True, help="Base DB file to work with")

    outputGroup = parser.add_argument_group("Output")
    outputGroup.add_argument("--output_dir", required=True,
                             help="Path to a folder where output should be saved")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")

    return parser.parse_args()


def do_main(args):
    base_db = args.base_db
    # File must be named Panda.sql so remove this
    # Add zipping the sql
    timestamp = int(datetime.datetime.utcnow().timestamp())
    output_db = os.path.join(args.output_dir, 'padguide_{}.sql'.format(timestamp))
    shutil.copy(base_db, output_db)

    with open(args.db_config) as f:
        db_config = json.load(f)

    # Connect to the database
    mysql_conn = pymysql.connect(host=db_config['host'],
                                 user=db_config['user'],
                                 password=db_config['password'],
                                 db=db_config['db'],
                                 charset=db_config['charset'],
                                 cursorclass=pymysql.cursors.DictCursor)

    sqlite_conn = lite.connect(output_db, detect_types=lite.PARSE_DECLTYPES, isolation_level=None)
    sqlite_conn.row_factory = lite.Row
    sqlite_conn.execute('pragma foreign_keys=OFF')

    for src_tbl, dest_tbl in TBL_MAPPING.items():
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


def write_table_data(result_json, table_name, output_dir):
    reformatted_tn = fix_table_name(table_name)
    output_file = os.path.join(output_dir, '{}.json'.format(reformatted_tn))

    with open(output_file, 'w') as f:
        json.dump(result_json, f, sort_keys=True, indent=4)


if __name__ == '__main__':
    args = parse_args()
    do_main(args)
