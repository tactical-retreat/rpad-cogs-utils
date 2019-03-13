import argparse
import logging
from collections import defaultdict

from pad_etl.data import database
from pad_etl.data import wave
from pad_etl.processor import enemy_skillset_processor, enemy_skillset, enemy_skillset_dump

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

dungeon_id_to_wavedata = defaultdict(list)
wave_summary_data = wave.load_wave_summary(args.processed_input_dir)
for wave in wave_summary_data:
    dungeon_id_to_wavedata[wave.dungeon_id].append(wave)

if not dungeon_id:
    print('no dungeon_id param specified; dumping all dungeons')
    for wave_dungeon_id in sorted(dungeon_id_to_wavedata.keys()):
        dungeon = na_database.dungeon_by_id(wave_dungeon_id)
        if dungeon:
            print(wave_dungeon_id, '->', dungeon.clean_name)
    exit()


dungeon = na_database.dungeon_by_id(dungeon_id)
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
    floor_id = wave.floor_id
    stage = wave.stage
    monster_id = wave.monster_id
    monster_level = wave.monster_level

    if floor_id != floor.floor_number:
        continue
    if wave.spawn_type == 2:
        continue

    stage_to_monsters[stage].append((monster_id, monster_level))

for stage in sorted(stage_to_monsters.keys()):
    print('\nstage', stage)
    for monster_info in stage_to_monsters[stage]:
        monster_id = monster_info[0]
        monster_level = monster_info[1]
        card = na_database.raw_card_by_id(monster_id)
        print(enemy_skillset_dump.load_summary_as_dump_text(card, monster_level))
