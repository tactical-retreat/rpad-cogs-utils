import argparse
import json
import logging
import csv
import os
from collections import defaultdict

from pad_etl.data import database
from pad_etl.processor import enemy_skillset_processor

fail_logger = logging.getLogger('processor_failures')
fail_logger.disabled = True


def parse_args():
    parser = argparse.ArgumentParser(description="Dumps dungeon data.", add_help=False)

    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--dungeon_id", default=0, help="PAD Dungeon ID")

    inputGroup.add_argument("--raw_input_dir", required=True,
                            help="Path to a folder where the raw input data is")
    inputGroup.add_argument("--processed_input_dir", required=True,
                            help="Path to a folder where the processed input data is")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")

    return parser.parse_args()


args = parse_args()
dungeon_id = int(args.dungeon_id) if args.dungeon_id else None

na_database = database.Database('na', args.raw_input_dir)
na_database.load_database(skip_skills=True, skip_bonus=True, skip_extra=True)

na_dungeons = na_database.dungeons
na_cards = na_database.raw_cards
na_enemies = na_database.enemies

dungeon_id_to_dungeon = {d.dungeon_id: d for d in na_dungeons}
card_id_to_card = {c.card_id: c for c in na_cards}
enemy_id_to_enemy = {e.enemy_id: e for e in na_enemies}

dungeon_id_to_wavedata = defaultdict(list)
wave_summary_file = os.path.join(args.processed_input_dir, 'wave_summary.csv')
with open(wave_summary_file) as f:
    csvreader = csv.reader(f, delimiter=',', quotechar='"')
    next(csvreader)
    for row in csvreader:
        dungeon_id_to_wavedata[int(row[0])].append(row)

if not dungeon_id:
    print('no dungeon_id param specified; dumping all dungeons')
    for wave_dungeon_id in sorted(dungeon_id_to_wavedata.keys()):
        dungeon = dungeon_id_to_dungeon.get(wave_dungeon_id, None)
        if dungeon:
            print(wave_dungeon_id, '->', dungeon.clean_name)
    exit()


dungeon = dungeon_id_to_dungeon.get(dungeon_id, None)
if not dungeon:
    print('dungeon not found')
    exit()

waves = dungeon_id_to_wavedata.get(dungeon_id)
if not waves:
    print('no waves found for', dungeon.clean_name)
    exit()

floor = dungeon.floors[-1]
print(dungeon.clean_name, '-', floor.clean_name)

stage_to_monsters = defaultdict(list)
for wave in waves:
    floor_id = int(wave[1])
    stage = int(wave[2])
    spawn_type = int(wave[3])
    monster_id = int(wave[4])
    monster_level = int(wave[5])

    if floor_id != floor.floor_number:
        continue
    if spawn_type == 2:
        continue

    stage_to_monsters[stage].append((monster_id, monster_level))

for stage in sorted(stage_to_monsters.keys()):
    print('\nstage', stage)
    for monster_info in stage_to_monsters[stage]:
        monster_id = monster_info[0]
        monster_level = monster_info[1]
        card = card_id_to_card[monster_id]
        enemy = enemy_id_to_enemy.get(monster_id, None)
        if not enemy:
            print('\nError! failed to find enemy data for', card.name, monster_id)
            continue
        
        print('\n', monster_id, '-', card.name, '@ level', monster_level, '\n')
        ss = enemy_skillset_processor.convert(enemy, monster_level)
        print(ss.dump())


