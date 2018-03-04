import argparse
import csv
import os
import re
import sys
import time

from PIL import Image


parser = argparse.ArgumentParser(description="Generates P&D portraits.", add_help=False)

inputGroup = parser.add_argument_group("Input")
inputGroup.add_argument("--input_dir", help="Path to a folder where CARD files are")
inputGroup.add_argument("--server", help="Either na or jp")
inputGroup.add_argument("--card_types_file", help="Path to card type CSV file")
inputGroup.add_argument("--card_templates_file", help="Path to card templates png")


outputGroup = parser.add_argument_group("Output")
outputGroup.add_argument("--output_dir", help="Path to a folder where output should be saved")

helpGroup = parser.add_argument_group("Help")
helpGroup.add_argument("-h", "--help", action="help", help="Displays this help message and exits.")
args = parser.parse_args()


input_dir = args.input_dir
server = args.server
card_types_file = args.card_types_file
card_templates_file = args.card_templates_file
output_dir = args.output_dir

templates_img = Image.open(card_templates_file)
attr_imgs = {}
sattr_imgs = {}
for idx, t in enumerate(['r', 'b', 'g', 'l', 'd']):
    pwidth = 100
    pheight = 100
    xstart = idx * (pwidth + 2)
    ystart = 0

    xend = xstart + pwidth
    yend = ystart + pheight

    attr_imgs[t] = templates_img.crop(box=(xstart, ystart, xend, yend))

    ystart = ystart + pheight + 5
    yend = ystart + pheight - 1 - 1  # Stops one short of full height

    sattr_imgs[t] = templates_img.crop(box=(xstart, ystart, xend, yend))


card_types = []
with open(card_types_file) as csvfile:
    for row in csv.reader(csvfile):
        if row[1] == server:
            card_types.append([int(row[0]), row[2], row[3]])


def idx_for_id(card_id: int):
    """Computes the (card_file, row, col) for a card."""
    card_id -= 1  # offset to 0
    card_file_idx = int(card_id / 100) + 1

    sub_idx = card_id % 100
    col = sub_idx % 10
    row = int(sub_idx / 10)

    card_file = 'CARDS_{}.PNG'.format(str(card_file_idx).zfill(3))
    return (card_file, row, col)


card_imgs = {}


def get_portraits_img(file_name):
    if file_name not in card_imgs:
        file_path = os.path.join(input_dir, file_name)
        card_imgs[file_name] = Image.open(file_path)
    return card_imgs[file_name]


def get_card_img(portraits, row, col):
    card_dim = 96
    spacer = 6
    xstart = (card_dim + spacer) * col
    ystart = (card_dim + spacer) * row

    xend = xstart + card_dim
    yend = ystart + card_dim
    return portraits.crop(box=(xstart, ystart, xend, yend))


for card_id, card_attr, card_sattr in card_types:
    card_file, row, col = idx_for_id(card_id)
    portraits = get_portraits_img(card_file)
    card_img = get_card_img(portraits, row, col)

    # Create a grey image to overlay the portrait on, filling in the background
    grey_img = Image.new("RGBA", card_img.size, color=(68, 68, 68, 255))
    card_img = Image.alpha_composite(grey_img, card_img)

    attr_img = attr_imgs[card_attr]

    # Adjust the card image to fit the portrait
    new_card_img = Image.new("RGBA", attr_img.size)
    new_card_img.paste(card_img, (2, 2))

    # Merge the attribute border on to the portrait
    merged_img = Image.alpha_composite(new_card_img, attr_img)

    if card_sattr:
        sattr_img = sattr_imgs[card_sattr]
        # Adjust the subattribute image to the attribute image size
        new_sattr_img = Image.new("RGBA", attr_img.size)
        # There's a slight offset needed for the subattribute border
        new_sattr_img.paste(sattr_img, (0, 1))

        # Merge the subattribute on top
        merged_img = Image.alpha_composite(merged_img, new_sattr_img)

    # Save
    merged_img.save(os.path.join(output_dir, '{}.png'.format(card_id)), 'PNG')
