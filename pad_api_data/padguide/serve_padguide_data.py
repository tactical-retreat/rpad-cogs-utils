import argparse
import json
import time

from encoding import encode, decode
from extract_utils import dump_table
import pymysql


def parse_args():
    parser = argparse.ArgumentParser(description="Echos PadGuide database data", add_help=False)

    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--db_config", help="JSON database info")
    inputGroup.add_argument("--db_table", help="PadGuide table name")
    inputGroup.add_argument("--data_arg", help="PadGuide API data param")

    inputGroup.add_argument("--raw_file", help="Raw JSON file")
    inputGroup.add_argument("--plain", action='store_true', help="Skip encryption and wrapping")

    inputGroup.add_argument("--no_items", action='store_true', help="Skip wrapping in items tag")

    inputGroup.add_argument("--map_key", help="Return key/value pair from table")
    inputGroup.add_argument("--map_value", help="Return key/value pair from table")

    inputGroup.add_argument("--timelimit", default=False, action='store_true',
                            help="Limits the timestamp field to 1m")

    return parser.parse_args()


def encode_data_response(data):
    output = {
        'resCode': '9000',
        'resMessage': 'OK',
        'data': encode(data),
    }
    return json.dumps(output)


def extract_tstamp(data_arg):
    decoded = decode(data_arg)
    decoded_js = json.loads(decoded)
    return int(decoded_js['TSTAMP'])


def load_file_json(file_name):
    with open(file_name) as f:
        return json.load(f)


def map_table(db_table, cursor, map_key, map_value):
    result = {}
    for row in cursor:
        result[row[map_key]] = row[map_value]
    return result


def load_from_db(db_config, db_table, data_arg, map_key=None, map_value=None, limit_tstamp=False):
    connection = pymysql.connect(host=db_config['host'],
                                 user=db_config['user'],
                                 password=db_config['password'],
                                 db=db_config['db'],
                                 charset=db_config['charset'],
                                 cursorclass=pymysql.cursors.DictCursor)

    sql = 'SELECT * FROM {}'.format(db_table)
    if data_arg:
        tstamp = extract_tstamp(data_arg)
        if limit_tstamp:
            tstamp = int(tstamp)
            m_ago = int((time.time() - 32 * 24 * 60 * 60) * 1000)
            tstamp = max(m_ago, tstamp)

        sql += ' WHERE tstamp >= {}'.format(tstamp)

        if limit_tstamp and db_table.lower() == 'schedule_list':
            sql += ' AND close_timestamp > UNIX_TIMESTAMP()'

        sql += ' ORDER BY tstamp ASC'

    with connection.cursor() as cursor:
        cursor.execute(sql)

        if map_key and map_value:
            data = map_table(db_table, cursor, map_key, map_value)
        else:
            data = dump_table(db_table, cursor)

    connection.close()
    return data


def main(args):
    if args.raw_file:
        data = load_file_json(args.raw_file)
    elif args.db_config and args.db_table:
        with open(args.db_config) as f:
            db_config = json.load(f)
        data = load_from_db(db_config, args.db_table, args.data_arg,
                            args.map_key, args.map_value, args.timelimit)
    else:
        raise RuntimeError('Incorrect arguments')

    if args.no_items:
        data = data['items']

    if args.plain:
        print(json.dumps(data, indent=4))
    else:
        print(encode_data_response(json.dumps(data)))


if __name__ == "__main__":
    args = parse_args()
    main(args)
