import argparse
import csv
import json
import os
import tempfile
import zipfile

from pad_etl.storage import db_util


def parse_args():
    parser = argparse.ArgumentParser(description="Dumps processed dungeon data.", add_help=False)

    inputGroup = parser.add_argument_group("Input")

    inputGroup.add_argument("--db_config", required=True, help="JSON database info")
    inputGroup.add_argument("--processed_dir", required=True,
                            help="Path to a folder where the input data is")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")

    return parser.parse_args()


def dump_cursor_to_csv(cursor, f):
    writer = csv.writer(f,
                        delimiter=',',
                        quotechar='"',
                        quoting=csv.QUOTE_MINIMAL)
    column_names = [i[0] for i in cursor.description]
    writer.writerow(column_names)
    for row in cursor.fetchall():
        writer.writerow([row[c] for c in column_names])


args = parse_args()

with open(args.db_config) as f:
    db_config = json.load(f)

db_wrapper = db_util.DbWrapper(dry_run=False)
db_wrapper.connect(db_config)


SELECT_QUERY = 'SELECT * FROM wave_data'
with db_wrapper.connection.cursor() as cursor:
    output_file = os.path.join(args.processed_dir, 'wave_data.zip')
    print('writing full wave data to', output_file)

    raw_file = None
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
        cursor.execute(SELECT_QUERY)
        dump_cursor_to_csv(cursor, tmp_file)
        raw_file = tmp_file.name

    print('finished dumping to', raw_file)

    with zipfile.ZipFile(output_file, mode='w', compression=zipfile.ZIP_DEFLATED) as wave_zip:
        wave_zip.write(raw_file, arcname='wave_data.csv')

    os.remove(raw_file)


SELECT_QUERY = """
SELECT dungeon_id, floor_id, stage,
       spawn_type, monster_id, monster_level,
       COUNT(*) AS row_count
FROM wave_data
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY 1, 2, 3
"""
with db_wrapper.connection.cursor() as cursor:
    output_file = os.path.join(args.processed_dir, 'wave_summary.csv')
    print('writing summary wave data to', output_file)

    cursor.execute(SELECT_QUERY)
    with open(output_file, 'w') as wave_file:
        dump_cursor_to_csv(cursor, wave_file)
