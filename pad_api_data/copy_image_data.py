"""
Copies PAD images to the expected PadGuide locations.
"""
import argparse
import os
import shutil

from pad_etl.common import monster_id_mapping


def parse_args():
    parser = argparse.ArgumentParser(
        description="Creates PadGuide image repository.", add_help=False)
    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--base_dir", required=True, help="Miru image base dir")

    outputGroup = parser.add_argument_group("Output")
    outputGroup.add_argument("--output_dir", required=True,
                             help="Dir to write padguide-formatted images to")


def copy_images(args):
    base_dir = args.base_dir
    output_dir = args.output_dir

    jp_icon_input_dir = os.path.join(base_dir, 'jp', 'portraits', 'local')
    na_icon_input_dir = os.path.join(base_dir, 'na', 'portraits', 'local')

    jp_portrait_input_dir = os.path.join(base_dir, 'jp', 'full', 'corrected_data')
    na_portrait_input_dir = os.path.join(base_dir, 'na', 'full', 'corrected_data')

    for jp_id in range(1, 6000):
        monster_no = monster_id_mapping.jp_id_to_monster_no(jp_id)
        shutil.copy2(os.path.join(jp_icon_input_dir, '{}.png'.format(jp_id)),
                     os.path.join(output_dir, 'icon_{}.png'.format(monster_no)))
        shutil.copy2(os.path.join(jp_portrait_input_dir, '{}.png'.format(jp_id)),
                     os.path.join(output_dir, 'portrait_{}.png'.format(monster_no)))

    for na_id in monster_id_mapping.NA_VOLTRON_IDS:
        monster_no = monster_id_mapping.na_id_to_monster_no(na_id)
        shutil.copy2(os.path.join(na_icon_input_dir, '{}.png'.format(na_id)),
                     os.path.join(output_dir, 'icon_{}.png'.format(monster_no)))
        shutil.copy2(os.path.join(na_portrait_input_dir, '{}.png'.format(na_id)),
                     os.path.join(output_dir, 'portrait_{}.png'.format(monster_no)))


if __name__ == '__main__':
    args = parse_args()
    copy_images(args)
