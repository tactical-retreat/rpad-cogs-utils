"""
Computes the dungeon skill info and compares it against golden files.

You should run this once to populate new golden files before making any
changes to the dungeon parsing code.
"""

import argparse
import filecmp
import logging
import os
import pathlib

import shutil
from collections import defaultdict

from pad_etl.data import database
from pad_etl.processor import enemy_skillset_dump as esd
from pad_etl.data import wave

fail_logger = logging.getLogger('processor_failures')
fail_logger.disabled = True

def parse_args():
    parser = argparse.ArgumentParser(description="Runs the integration test.", add_help=False)
    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--input_dir", required=True,
                            help="Path to a folder where the input data is")

    outputGroup = parser.add_argument_group("Output")
    outputGroup.add_argument("--output_dir", required=True,
                             help="Path to a folder where output should be saved")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")
    return parser.parse_args()


def run_test(args):
    raw_input_dir = os.path.join(args.input_dir, 'raw')
    processed_input_dir = os.path.join(args.input_dir, 'processed')

    output_dir = args.output_dir
    new_output_dir = os.path.join(output_dir, 'new')
    pathlib.Path(new_output_dir).mkdir(parents=True, exist_ok=True)
    golden_output_dir = os.path.join(output_dir, 'golden')
    pathlib.Path(golden_output_dir).mkdir(parents=True, exist_ok=True)

    db = database.Database('na', raw_input_dir)
    print('loading')
    db.load_database(skip_skills=True, skip_bonus=True, skip_extra=True)

    dungeon_id_to_wavedata = defaultdict(set)
    wave_summary_data = wave.load_wave_summary(processed_input_dir)
    for w in wave_summary_data:
        dungeon_id_to_wavedata[w.dungeon_id].add(w)

    split_dungeons = [
        # Marks dungeons which are enormous and should be broken into subfiles
        110, # Endless Corridors
    ]

    golden_dungeons = [
        116, # Gunma
        158, # Goemon
        172, # Taiko
        176, # Valkyrie
        307, # Hera-Is
        308, # Gung-ho
        318, # Zeus-Dios
        317, # ECO
        331, # Hera-Ur
        337, # Dragon Zombie
        354, # Takeminakata
    ]

    for dungeon_id, wave_data in dungeon_id_to_wavedata.items():
        dungeon = db.dungeon_by_id(dungeon_id)
        if not dungeon:
            print('skipping', dungeon_id)
            continue

        print('processing', dungeon_id, dungeon.clean_name)
        file_output_dir = golden_output_dir if dungeon_id in golden_dungeons else new_output_dir

        if dungeon_id in split_dungeons:
            # Disable endless for now it takes a long time to run
            continue
            for floor in dungeon.floors:
                floor_id = floor.floor_number
                file_name = '{}_{}.txt'.format(dungeon_id, floor_id)
                with open(os.path.join(file_output_dir, file_name), encoding='utf-8', mode='w') as f:
                    f.write(flatten_data(wave_data, dungeon, db, limit_floor_id=floor_id))
        else:
            file_name = '{}.txt'.format(dungeon_id)
            with open(os.path.join(file_output_dir, file_name), encoding='utf-8', mode='w') as f:
                f.write(flatten_data(wave_data, dungeon, db))


def flatten_data(wave_data, dungeon_data, db, limit_floor_id=None):
    output = ''
    floor_stage_to_monsters = defaultdict(list)
    for w in wave_data:
        floor_id = w.floor_id
        stage = w.stage
        monster_id = w.monster_id
        monster_level = w.monster_level
        if w.spawn_type == 2:
            continue
        floor_stage_to_monsters[(floor_id, stage)].append((monster_id, monster_level))

    for floor in reversed(dungeon_data.floors):
        if limit_floor_id is not None and limit_floor_id != floor.floor_number:
            continue
        header = '{} - {}\n'.format(dungeon_data.clean_name, floor.clean_name)
        print(header)
        output += header

        for floor_stage in sorted([x for x in floor_stage_to_monsters.keys() if x[0] == floor.floor_number]):
            stage = floor_stage[1]
            output += '\nstage {}\n'.format(stage)
            for monster_info in sorted(floor_stage_to_monsters[floor_stage], key=lambda x: x[0]):
                monster_id = monster_info[0]
                monster_level = monster_info[1]
                card = db.raw_card_by_id(monster_id)
                if not card:
                    output += '\nCould not find monster {} @ level {}'.format(monster_id, monster_level)
                    continue
                output += '\n{} - {} @ level {}'.format(monster_id, card.name, monster_level)
                output += '\n{}'.format(esd.load_summary_as_dump_text(card, monster_level, floor.modifiers_clean['atk']))

        output += '\n'

    return output


if __name__ == '__main__':
    args = parse_args()
    run_test(args)
    print('done')
