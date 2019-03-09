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
from pad_etl.processor import enemy_skillset_dump
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

    dungeons = [
        # Amnel
        2707,
        # Ogres, Tyranos are good, valhalla is busted, i&i is close, nidhogg's magic before/after hp bullshit is
        # impossible.
        3607,
        # Quetzal
        3655
    ]

    for dungeon_id in dungeons:
        file_name = '{}.txt'.format(dungeon_id)
        dungeon = db.dungeon_by_id(dungeon_id)
        with open(os.path.join(new_output_dir, file_name), encoding='utf-8', mode='w') as f:
            f.write('{} {}\n'.format(dungeon_id, dungeon.clean_name))
            for data in sorted(dungeon_id_to_wavedata.get(dungeon_id)):
                f.write(','.join(map(str, data)) + '\n')
                monster_id = data[2]
                monster_level = data[3]
                card = db.raw_card_by_id(monster_id)
                f.write('{} - {} @ level {}\n'.format(monster_id, card.name, monster_level))
                f.write(enemy_skillset_dump.load_summary_as_dump_text(card, monster_id, monster_level))
                f.write('\n\n')


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


if __name__ == '__main__':
    args = parse_args()
    run_test(args)
    print('done')
