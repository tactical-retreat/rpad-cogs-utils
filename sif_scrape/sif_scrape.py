import argparse
import json
import os
import re
import sys
import urllib.request

from PIL import Image


parser = argparse.ArgumentParser(description="Downloads SIF images.", add_help=False)

outputGroup = parser.add_argument_group("Output")
outputGroup.add_argument("--output_dir", help="Path to a folder where output should be saved")

helpGroup = parser.add_argument_group("Help")
helpGroup.add_argument("-h", "--help", action="help", help="Displays this help message and exits.")
args = parser.parse_args()


output_dir = args.output_dir
raw_dir = os.path.join(output_dir, 'raw')
processed_dir = os.path.join(output_dir, 'processed')

os.makedirs(raw_dir, exist_ok=True)
os.makedirs(processed_dir, exist_ok=True)


def download_file(url, file_path):
    print('downloading {} to {}'.format(url, file_path))
    response_object = urllib.request.urlopen(url)
    with response_object as response:
        file_data = response.read()
        with open(file_path, "wb") as f:
            f.write(file_data)


def load_json(url):
    response_object = urllib.request.urlopen(url)
    with response_object as response:
        file_data = response.read()
        return json.loads(file_data)


FIRST_REQ = 'https://schoolido.lu/api/cards/?page_size=100'
ID_FIELD = 'id'
IMAGE_FIELD = 'transparent_image'
IDOL_IMAGE_FIELD = 'transparent_idolized_image'

card_data = []

next_req = FIRST_REQ
while next_req:
    print('loading ' + next_req)
    js_resp = load_json(next_req)
    next_req = js_resp['next']
    card_data.extend(js_resp['results'])

print('done retrieving cards: {}'.format(len(card_data)))


def maybe_download_field(c, field):
    cid = c[ID_FIELD]
    image_url = c[field]
    if image_url:
        image_url = 'http:' + image_url
        image_path = os.path.join(raw_dir, '{}_{}.png'.format(cid, field))
        if not os.path.exists(image_path):
            download_file(image_url, image_path)


for c in card_data:
    cid = c[ID_FIELD]
    maybe_download_field(c, IMAGE_FIELD)
    maybe_download_field(c, IDOL_IMAGE_FIELD)


def autocrop(image):
    bbox = image.getbbox()
    image = image.crop(bbox)
    return image


for f in os.listdir(raw_dir):
    raw_file = os.path.join(raw_dir, f)
    processed_file = os.path.join(processed_dir, f)
    image = Image.open(raw_file)
    image = autocrop(image)
    image.save(processed_file)
