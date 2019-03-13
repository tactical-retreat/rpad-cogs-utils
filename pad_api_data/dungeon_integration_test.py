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
        dungeon_id_to_wavedata[w.dungeon_id].add((w.floor_id, w.stage, w.monster_id, w.monster_level))

    golden_dungeons = [
        # Currently no golden dungeons, put them here after verification
    ]

    for dungeon_id, wave_data in dungeon_id_to_wavedata.items():
        dungeon = db.dungeon_by_id(dungeon_id)
        if not dungeon:
            print('skipping', dungeon_id)
            continue
        print('processing', dungeon_id, dungeon.clean_name)
        if dungeon_id in split_dungeons:
            for floor in dungeon.floors:
                floor_id = floor.floor_number
                file_name = '{}_{}.txt'.format(dungeon_id, floor_id)
                with open(os.path.join(new_output_dir, file_name), encoding='utf-8', mode='w') as f:
                    f.write(flatten_data(wave_data, dungeon, db, limit_floor_id=floor_id))
        else:
            file_name = '{}.txt'.format(dungeon_id)
            with open(os.path.join(new_output_dir, file_name), encoding='utf-8', mode='w') as f:
                f.write(flatten_data(wave_data, dungeon, db))

    for file in os.listdir(new_output_dir):
        new_file = os.path.join(new_output_dir, file)
        golden_file = os.path.join(golden_output_dir, file)
        if not os.path.exists(golden_file):
            print('golden file does not exist, creating', golden_file)
            shutil.copy(new_file, golden_file)
            continue

        if not filecmp.cmp(new_file, golden_file, shallow=False):
            print('ERROR')
            print('golden file differs from new file for', file)
            print('ERROR')


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

        for floor_stage in sorted(floor_stage_to_monsters.keys()):
            stage = floor_stage[1]
            output += '\nstage {}\n'.format(stage)
            for monster_info in floor_stage_to_monsters[floor_stage]:
                monster_id = monster_info[0]
                monster_level = monster_info[1]
                card = db.raw_card_by_id(monster_id)
                output += '\n{} - {} @ level {}'.format(monster_id, card.name, monster_level)
                output += '\n{}'.format(esd.load_summary_as_dump_text(card, monster_level))

        output += '\n'

    return output


if __name__ == '__main__':
    args = parse_args()
    run_test(args)
    print('done')
