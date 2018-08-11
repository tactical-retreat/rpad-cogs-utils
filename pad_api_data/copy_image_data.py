"""
Copies PAD images to the expected PadGuide locations.
"""
import argparse
import os
import shutil
from PIL import Image

from pad_etl.common import monster_id_mapping


def parse_args():
    parser = argparse.ArgumentParser(
        description="Creates PadGuide image repository.", add_help=False)
    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--base_dir", required=True, help="Miru image base dir")

    outputGroup = parser.add_argument_group("Output")
    outputGroup.add_argument("--output_dir", required=True,
                             help="Dir to write padguide-formatted images to")

    return parser.parse_args()


def do_copy(src_dir, src_file, dest_dir, dest_file, resize=None):
    src_path = os.path.join(src_dir, src_file)
    dest_path = os.path.join(dest_dir, dest_file)
    if os.path.exists(src_path) and not os.path.exists(dest_path):
        if resize:
            im = Image.open(src_path)
            new_size = (im.size[0] * resize, im.size[1] * resize)
            im.thumbnail(new_size, Image.ANTIALIAS)
            im.save(dest_path)
        else:
            shutil.copy2(src_path, dest_path)


def copy_images(args):
    base_dir = args.base_dir
    output_dir = args.output_dir

    jp_icon_input_dir = os.path.join(base_dir, 'jp', 'portrait', 'local')
    na_icon_input_dir = os.path.join(base_dir, 'na', 'portrait', 'local')

    jp_portrait_input_dir = os.path.join(base_dir, 'jp', 'full', 'corrected_data')
    na_portrait_input_dir = os.path.join(base_dir, 'na', 'full', 'corrected_data')

    for jp_id in range(1, 6000):
        monster_no = monster_id_mapping.jp_id_to_monster_no(jp_id)
        monster_no_filled = str(monster_no).zfill(4)
        do_copy(jp_icon_input_dir, '{}.png'.format(jp_id),
                output_dir, 'icon_{}.png'.format(monster_no_filled))
        do_copy(jp_portrait_input_dir, '{}.png'.format(jp_id),
                output_dir, 'portrait_{}.png'.format(monster_no_filled),
                resize=.5)
        do_copy(jp_portrait_input_dir, '{}.png'.format(jp_id),
                output_dir, 'texture_{}.png'.format(monster_no_filled))

    for na_id in monster_id_mapping.NA_VOLTRON_IDS:
        monster_no = monster_id_mapping.na_id_to_monster_no(na_id)
        monster_no_filled = str(monster_no).zfill(4)
        do_copy(na_icon_input_dir, '{}.png'.format(na_id),
                output_dir, 'icon_{}.png'.format(monster_no_filled))
        do_copy(na_portrait_input_dir, '{}.png'.format(na_id),
                output_dir, 'portrait_{}.png'.format(monster_no_filled),
                resize=.5)
        do_copy(na_portrait_input_dir, '{}.png'.format(na_id),
                output_dir, 'texture_{}.png'.format(monster_no_filled))


if __name__ == '__main__':
    args = parse_args()
    copy_images(args)
