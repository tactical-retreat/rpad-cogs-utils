import argparse
import json
import logging
import os
import time

from pad_etl.processor import db_util
from pad_etl.processor import egg
from pad_etl.processor import egg_processor


def parse_args():
    parser = argparse.ArgumentParser(description="Updates PadGuide egg machines.", add_help=False)

    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--db_config", required=True, help="JSON database info")
    inputGroup.add_argument("--raw_input_dir", required=True,
                            help="Path to a folder where the input data is")

    outputGroup = parser.add_argument_group("Output")
    outputGroup.add_argument("--doupdates", default=False,
                             action="store_true", help="Apply updates")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")

    return parser.parse_args()


args = parse_args()

logging.basicConfig()
logger = logging.getLogger('database')
logger.setLevel(logging.DEBUG)

with open(args.db_config) as f:
    db_config = json.load(f)

dry_run = not args.doupdates
db_wrapper = db_util.DbWrapper(dry_run)
db_wrapper.connect(db_config)

loader = egg.EggLoader(db_wrapper)

loader.hide_outdated_machines()

jp_egg_file = os.path.join(args.raw_input_dir, 'jp', 'egg_machines.json')
na_egg_file = os.path.join(args.raw_input_dir, 'na', 'egg_machines.json')

with open(jp_egg_file) as f:
    jp_egg_machines = json.load(f)

with open(na_egg_file) as f:
    na_egg_machines = json.load(f)

processor = egg_processor.EggProcessor()
for em_json in jp_egg_machines + na_egg_machines:
    if em_json['end_timestamp'] < time.time():
        print('Skipping machine; looks closed', em_json['clean_name'])
        continue
    egg_title_list = processor.convert_from_json(em_json)
    loader.save_egg_title_list(egg_title_list)
