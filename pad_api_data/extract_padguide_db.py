import argparse
import json
import os
from padguide.extract_utils import dump_table, fix_table_name

import pymysql


parser = argparse.ArgumentParser(description="Download PadGuide database as JSON.", add_help=False)

inputGroup = parser.add_argument_group("Input")
inputGroup.add_argument("--db_config", required=True, help="JSON database info")

outputGroup = parser.add_argument_group("Output")
outputGroup.add_argument("--output_dir", required=True,
                         help="Path to a folder where output should be saved")

helpGroup = parser.add_argument_group("Help")
helpGroup.add_argument("-h", "--help", action="help", help="Displays this help message and exits.")

args = parser.parse_args()


# Tables that don't exist, just dump them empty
EMPTY_FILES = [
    'coin_rotation_list',
    'shop_lineup_list',
    'sub_dungeon_alias_list',
    'sub_dungeon_malias_list',
]

SKIP_TABLES = [
    'wave_data',
]

with open(args.db_config) as f:
    db_config = json.load(f)

output_dir = args.output_dir

# Connect to the database
connection = pymysql.connect(host=db_config['host'],
                             user=db_config['user'],
                             password=db_config['password'],
                             db=db_config['db'],
                             charset=db_config['charset'],
                             cursorclass=pymysql.cursors.DictCursor)


def write_table_data(result_json, table_name, output_dir):
    reformatted_tn = fix_table_name(table_name)
    output_file = os.path.join(output_dir, '{}.json'.format(reformatted_tn))

    with open(output_file, 'w') as f:
        json.dump(result_json, f, sort_keys=True, indent=4)


with connection.cursor() as cursor:
    sql = "SELECT table_name FROM information_schema.tables where table_schema='padguide'"
    cursor.execute(sql)
    tables = list(cursor.fetchall())

    for table in tables:
        table_name = table['table_name']
        if table_name in SKIP_TABLES:
            print('skipping', table_name)
            continue
        print('processing', table_name)
        sql = 'select * from {}'.format(table_name)
        cursor.execute(sql)
        result_json = dump_table(table_name, cursor)
        write_table_data(result_json, table_name, output_dir)

    for table_name in EMPTY_FILES:
        result_json = dump_table(table_name, [])
        write_table_data(result_json, table_name, output_dir)

connection.close()
