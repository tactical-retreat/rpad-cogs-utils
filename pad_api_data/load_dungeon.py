from pad_etl.processor import db_util
from pad_etl.processor import dungeon
from pad_etl.processor import dungeon_processor
from pad_etl.data import dungeon as datadungeon
from pad_etl.data import card as datacard
from pad_etl.processor.wave import WaveItem
import json
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Updates PadGuide dungeons.", add_help=False)

    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--pad_dungeon_id", default=0, help="PAD Dungeon ID")
    inputGroup.add_argument("--dungeon_seq", default=0, help="PadGuide Dungeon ID")

    outputGroup = parser.add_argument_group("Output")
    outputGroup.add_argument("--doprod", default=False,
                             action="store_true", help="Run against prod")
    outputGroup.add_argument("--doupdates", default=False,
                             action="store_true", help="Apply updates")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")

    return parser.parse_args()

args = parse_args()


db_config_prod = '/home/tactical0retreat/rpad-cogs-utils/pad_api_data/db_config.json'
db_config_dev = '/home/tactical0retreat/rpad-cogs-utils/pad_api_data/db_config_dev.json'

db_config = db_config_prod if args.doprod else db_config_dev

with open(db_config) as f:
    db_config = json.load(f)

dry_run = not args.doupdates
db_wrapper = db_util.DbWrapper(dry_run)
db_wrapper.connect(db_config)

if args.pad_dungeon_id:
	pad_dungeon_id = int(args.pad_dungeon_id)
	dungeon_seq = db_wrapper.get_single_value("select dungeon_seq from etl_dungeon_map where pad_dungeon_id = {}".format(pad_dungeon_id), op=int)
elif args.dungeon_seq:
	dungeon_seq = int(args.dungeon_seq)
	pad_dungeon_id = db_wrapper.get_single_value("select pad_dungeon_id from etl_dungeon_map where dungeon_seq = {}".format(dungeon_seq), op=int)
else:
	raise Exception('must specify pad_dungeon_id or dungeon_seq')

loader = dungeon.DungeonLoader(db_wrapper)

print(dungeon_seq, pad_dungeon_id)
dungeon = loader.load_dungeon(dungeon_seq)

jp_dir = '/home/tactical0retreat/pad_data/raw/jp'
na_dir = '/home/tactical0retreat/pad_data/raw/na'

jp_data = datadungeon.load_dungeon_data(data_dir=jp_dir)
na_data = datadungeon.load_dungeon_data(data_dir=na_dir)

for d in jp_data:
    if d.dungeon_id == pad_dungeon_id:
        jp_dungeon = d
        break

na_dungeon = None
for d in na_data:
    if d.dungeon_id == pad_dungeon_id:
        na_dungeon = d
        break

if not na_dungeon:
    na_dungeon = jp_dungeon

cards = datacard.load_card_data(data_dir=jp_dir)

waves = db_wrapper.load_multiple_objects(WaveItem, pad_dungeon_id)
print('loaded', len(waves), 'waves')
dungeon_processor.populate_dungeon(dungeon, jp_dungeon, na_dungeon, waves, cards)

# print(dungeon)
loader.save_dungeon(dungeon)
