import argparse
import json
import os

from pad_etl.data import bonus as databonus
from pad_etl.data import card as datacard
from pad_etl.data import dungeon as datadungeon
from pad_etl.processor import db_util
from pad_etl.processor import dungeon
from pad_etl.processor import dungeon_processor

from pad_etl.processor.wave import WaveItem


def parse_args():
    parser = argparse.ArgumentParser(description="Updates PadGuide dungeons.", add_help=False)

    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--pad_dungeon_id", default=0, help="PAD Dungeon ID")
    inputGroup.add_argument("--dungeon_seq", default=0, help="PadGuide Dungeon ID")

    inputGroup.add_argument("--db_config", required=True, help="JSON database info")
    inputGroup.add_argument("--raw_input_dir", required=True,
                            help="Path to a folder where the input data is")

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


with open(args.db_config) as f:
    db_config = json.load(f)

dry_run = not args.doupdates
db_wrapper = db_util.DbWrapper(dry_run)
db_wrapper.connect(db_config)

if args.pad_dungeon_id:
    pad_dungeon_id = int(args.pad_dungeon_id)
    dungeon_seq = db_wrapper.get_single_value(
        "select dungeon_seq from etl_dungeon_map where pad_dungeon_id = {}".format(pad_dungeon_id), op=int)
elif args.dungeon_seq:
    dungeon_seq = int(args.dungeon_seq)
    pad_dungeon_id = db_wrapper.get_single_value(
        "select pad_dungeon_id from etl_dungeon_map where dungeon_seq = {}".format(dungeon_seq), op=int)
else:
    raise Exception('must specify pad_dungeon_id or dungeon_seq')

loader = dungeon.DungeonLoader(db_wrapper)

print(dungeon_seq, pad_dungeon_id)
dungeon = loader.load_dungeon(dungeon_seq)

jp_dir = os.path.join(args.raw_input_dir, 'jp')
na_dir = os.path.join(args.raw_input_dir, 'na')

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

jp_bonus_data = databonus.load_bonus_data(data_dir=jp_dir, data_group='red', server='jp')
na_bonus_data = databonus.load_bonus_data(data_dir=na_dir, data_group='red', server='na')

floor_text = {}
for bonus in jp_bonus_data + na_bonus_data:
    if bonus.bonus_name != 'dungeon_floor_text':
        continue
    if bonus.dungeon_id != jp_dungeon.dungeon_id:
        continue
    adj_floor_id = bonus.dungeon_floor_id - bonus.dungeon_id * 1000
    floor_text[adj_floor_id] = bonus.clean_message

cards = datacard.load_card_data(data_dir=jp_dir)
na_cards = datacard.load_card_data(data_dir=na_dir)

waves = db_wrapper.load_multiple_objects(WaveItem, pad_dungeon_id)
print('loaded', len(waves), 'waves')
dungeon_processor.populate_dungeon(dungeon, jp_dungeon, na_dungeon,
                                   waves=waves,
                                   cards=cards,
                                   na_cards=na_cards,
                                   floor_text=floor_text)

# print(dungeon)
loader.save_dungeon(dungeon)
