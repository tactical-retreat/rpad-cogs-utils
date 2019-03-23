"""
Regenerates the flattened enemy skill list for all monsters.
"""

import argparse
import logging
import os

from pad_etl.data import database
from pad_etl.processor import debug_utils
from pad_etl.processor import enemy_skillset_processor
from pad_etl.processor import enemy_skillset_dump
from pad_etl.processor.enemy_skillset import ESAction

fail_logger = logging.getLogger('processor_failures')
fail_logger.disabled = True


def parse_args():
    parser = argparse.ArgumentParser(description="Runs the integration test.", add_help=False)
    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--input_dir", required=True,
                            help="Path to a folder where the input data is")
    inputGroup.add_argument("--card_id", required=False,
                            help="Process only this card")
    inputGroup.add_argument("--interactive", required=False,
                            help="Lets you specify a card id on the command line")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")
    return parser.parse_args()


def process_card(mcard):
    enemy_behavior = mcard.enemy_behavior
    card = mcard.card
    enemy_skill_effect = card.enemy_skill_effect
    enemy_skill_effect_type = card.enemy_skill_effect_type
    if not enemy_behavior:
        return

    levels = enemy_skillset_processor.extract_levels(enemy_behavior)
    skill_listings = []
    used_actions = []
    for level in sorted(levels):
        skillset = enemy_skillset_processor.convert(card, enemy_behavior, level, enemy_skill_effect, enemy_skill_effect_type)
        flattened = enemy_skillset_dump.flatten_skillset(level, skillset)
        if not flattened.records:
            continue
        used_actions.extend(debug_utils.extract_used_skills(skillset))
        skill_listings.append(flattened)

    if not skill_listings:
        return

    unused_actions = []
    for b in enemy_behavior:
        if issubclass(type(b), ESAction) and b not in used_actions and b not in unused_actions:
            unused_actions.append(b)

    entry_info = enemy_skillset_dump.EntryInfo(
        card.card_id, card.name, 'not yet populated')
    if unused_actions:
        entry_info.warnings.append('Found {} unused actions'.format(len(unused_actions)))

    summary = enemy_skillset_dump.EnemySummary(entry_info, skill_listings)

    enemy_skillset_dump.dump_summary_to_file(card, summary, enemy_behavior, unused_actions)


def run(args):
    raw_input_dir = os.path.join(args.input_dir, 'raw')
    db = database.Database('na', raw_input_dir)
    db.load_database(skip_skills=True, skip_bonus=True, skip_extra=True)

    fixed_card_id = args.card_id
    if args.interactive:
        fixed_card_id = input("enter a card id:").strip()

    count = 0
    for card in db.cards:
        if fixed_card_id and card.card.card_id != int(fixed_card_id):
            continue
        try:
            count += 1
            if count % 50 == 0:
                print('processing {} of {}'.format(count, len(db.cards)))
            process_card(card)
        except Exception as ex:
            print('failed to process', card.card.name)
            print(ex)
            if 'unsupported operation' not in str(ex):
                import traceback
                traceback.print_exc()


if __name__ == '__main__':
    args = parse_args()
    run(args)
