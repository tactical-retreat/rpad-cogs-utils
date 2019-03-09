"""
Regenerates the flattened enemy skill list for all monsters.
"""

import argparse
import logging
import os

from pad_etl.data import database
from pad_etl.processor import enemy_skillset_processor
from pad_etl.processor import enemy_skillset_dump

fail_logger = logging.getLogger('processor_failures')
fail_logger.disabled = True


def parse_args():
    parser = argparse.ArgumentParser(description="Runs the integration test.", add_help=False)
    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--input_dir", required=True,
                            help="Path to a folder where the input data is")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")
    return parser.parse_args()


def process_card(card):
    print('processing', card.card.name)
    enemy_behavior = card.enemy_behavior
    if not enemy_behavior:
        return

    levels = enemy_skillset_processor.extract_levels(enemy_behavior)
    skill_listings = []
    for level in sorted(levels):
        skillset = enemy_skillset_processor.convert(enemy_behavior, level)
        flattened = enemy_skillset_dump.flatten_skillset(level, skillset)
        if not flattened.records:
            continue
        skill_listings.append(flattened)

    if not skill_listings:
        return

    entry_info = enemy_skillset_dump.EntryInfo(
        card.card.card_id, card.card.name, 'not yet populated')
    summary = enemy_skillset_dump.EnemySummary(entry_info, skill_listings)
    enemy_skillset_dump.dump_summary_to_file(summary, enemy_behavior)


def run(args):
    raw_input_dir = os.path.join(args.input_dir, 'raw')
    db = database.Database('na', raw_input_dir)
    print('loading')
    db.load_database(skip_skills=True, skip_bonus=True, skip_extra=True)

    for card in db.cards:
        try:
            process_card(card)
        except Exception as ex:
            print('failed to process', card.card.name)
            print(ex)


if __name__ == '__main__':
    args = parse_args()
    run(args)
