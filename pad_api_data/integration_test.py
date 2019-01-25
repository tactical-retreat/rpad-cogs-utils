"""
Loads the raw data files and dumps the intermediate ones.
If no golden files exist, copies them into place.
If golden files exist, compares the data and reports on differences.

You should run this once to populate new golden files before making any
changes to the raw data parsers.
"""

import argparse
import difflib
import json
import os
import pathlib

import shutil

from pad_etl.data import database


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
    input_dir = args.input_dir

    output_dir = args.output_dir
    new_output_dir = os.path.join(output_dir, 'new')
    pathlib.Path(new_output_dir).mkdir(parents=True, exist_ok=True)
    golden_output_dir = os.path.join(output_dir, 'golden')
    pathlib.Path(golden_output_dir).mkdir(parents=True, exist_ok=True)

    for server in ['na', 'jp']:
        print('starting {} checks'.format(server))
        db = database.Database(server, input_dir)

        print('loading')
        db.load_database()

        print('saving')
        db.save_all(new_output_dir, True)

        print('diffing')
        files = {
            '{}_raw_cards.json'.format(server): db.raw_cards,
            '{}_dungeons.json'.format(server): db.dungeons,
            '{}_skills.json'.format(server): db.skills,
            '{}_enemy_skills.json'.format(server): db.enemy_skills,
            '{}_bonuses.json'.format(server): db.bonuses,
            '{}_cards.json'.format(server): db.cards,
            '{}_exchange.json'.format(server): db.exchange,
        }
        for file, data in files.items():
            new_file = os.path.join(new_output_dir, file)
            golden_file = os.path.join(golden_output_dir, file)
            if not os.path.exists(golden_file):
                print('golden file does not exist, creating', golden_file)
                shutil.copy(new_file, golden_file)
                continue

            with open(golden_file) as f:
                golden_data = json.load(f)

            if len(golden_data) != len(data):
                print('ERROR')
                print('ERROR: file lengths differed, indicates old golden data for', file)
                print('ERROR')
                continue

            failures = []
            for i in range(len(golden_data)):
                gold_row = golden_data[i]
                new_row = data[i]

                gold_str = json.dumps(gold_row, indent=4, sort_keys=True,
                                      default=lambda x: x.__dict__)
                new_str = json.dumps(new_row, indent=4, sort_keys=True,
                                     default=lambda x: x.__dict__)

                if gold_str != new_str:
                    failures.append([gold_str, new_str])

            if not failures:
                continue

            fail_count = len(failures)
            disp_count = min(fail_count, 3)
            print('encountered', fail_count, 'errors, displaying the first', disp_count)

            for i in range(disp_count):
                gold_str = failures[i][0]
                new_str = failures[i][1]

                id_text = '\n'.join(filter(lambda x: '_id' in x, gold_str.split('\n')))
                print('row identifiers:\n{}\n'.format(id_text))
                diff_lines = difflib.context_diff(
                    gold_str.split('\n'), new_str.split('\n'), fromfile='golden', tofile='new', n=1)
                print('\n'.join(diff_lines))


if __name__ == '__main__':
    args = parse_args()
    run_test(args)
