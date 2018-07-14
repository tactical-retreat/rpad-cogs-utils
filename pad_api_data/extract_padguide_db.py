import argparse
from datetime import datetime
from decimal import Decimal
import json
import os

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

# Tables that use 1/0 instead of Y/N?
ALT_YN_TABLES = [
    'dungeon_list',
]

# Tables that use full datetimes
ALT_DATETIME_TABLES = [
    'egg_title_list',
    'monster_list',
]

# Hour/Minute fields that shouldn't be zformat(2)
ALT_HR_MIN_COLS = [
    'SERVER_OPEN_HOUR',
]

# Tables that don't exist, just dump them empty
EMPTY_FILES = [
    'coin_rotation_list',
    'shop_lineup_list',
    'sub_dungeon_alias_list',
    'sub_dungeon_malias_list',
]

with open(args.db_config) as f:
    db_config = json.load(f)

output_dir = args.output_dir


def fix_table_name(table_name):
    parts = table_name.split('_')
    return ''.join([parts[0]] + [p.capitalize() for p in parts[1:]])


def dump_table(table_name, output_dir, cursor):
    print('processing', table_name)
    reformatted_tn = fix_table_name(table_name)
    output_file = os.path.join(output_dir, '{}.json'.format(reformatted_tn))

    result_json = {'items': []}
    for row in cursor:
        row_data = {}
        for col in row:
            fixed_col = col.upper()
            if fixed_col.startswith('_'):
                fixed_col = fixed_col[1:]
            data = row[col]
            if data is None:
                fixed_data = ''
            elif '_YN' in fixed_col:
                if table_name in ALT_YN_TABLES:
                    fixed_data = '1' if data else '0'
                else:
                    fixed_data = 'Y' if data else 'N'
            elif type(data) is Decimal:
                first = '{}'.format(float(data))
                second = '{:.1f}'.format(float(data))
                fixed_data = max((first, second), key=len)
            elif type(data) is datetime:
                if table_name in ALT_DATETIME_TABLES:
                    fixed_data = data.isoformat(' ')
                else:
                    fixed_data = data.date().isoformat()
            elif 'HOUR' in fixed_col or 'MINUTE' in fixed_col:
                if fixed_col in ALT_HR_MIN_COLS:
                    fixed_data = str(data)
                else:
                    fixed_data = str(data).zfill(2)
            else:
                fixed_data = str(data)

            row_data[fixed_col] = fixed_data
        result_json['items'].append(row_data)

    with open(output_file, 'w') as f:
        json.dump(result_json, f, sort_keys=True, indent=4)


# Connect to the database
connection = pymysql.connect(host=db_config['host'],
                             user=db_config['user'],
                             password=db_config['password'],
                             db=db_config['db'],
                             charset=db_config['charset'],
                             cursorclass=pymysql.cursors.DictCursor)

with connection.cursor() as cursor:
    sql = "SELECT table_name FROM information_schema.tables where table_schema='padguide'"
    cursor.execute(sql)
    tables = list(cursor.fetchall())

    for table in tables:
        table_name = table['table_name']
        sql = 'select * from {}'.format(table_name)
        cursor.execute(sql)
        dump_table(table_name, output_dir, cursor)

    for table_name in EMPTY_FILES:
        dump_table(table_name, output_dir, [])

connection.close()
