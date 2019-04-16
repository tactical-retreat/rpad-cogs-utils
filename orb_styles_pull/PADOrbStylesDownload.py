import argparse
import json
import os
import re
import sys
import urllib.request

from collections import defaultdict

import padtools

parser = argparse.ArgumentParser(
    description="Downloads P&D Orb Styles (alternate skins)", add_help=False)

inputGroup = parser.add_argument_group("Input")
inputGroup.add_argument("--server", required=True, help="na or jp")
inputGroup.add_argument("--data_dir", required=True, help="Path to processed pad data files")

outputGroup = parser.add_argument_group("Output")
outputGroup.add_argument("--output_dir", help="Path to a folder where output should be saved")

helpGroup = parser.add_argument_group("Help")
helpGroup.add_argument("-h", "--help", action="help", help="Displays this help message and exits.")
args = parser.parse_args()

server = args.server.lower()

extras = []
if args.server == 'na':
    extras = padtools.regions.north_america.server.extras
elif args.server == 'jp':
    extras = padtools.regions.japan.server.extras


output_dir = args.output_dir

def download_file(url, file_path):
    response_object = urllib.request.urlopen(url)
    with response_object as response:
        file_data = response.read()
        with open(file_path, "wb") as f:
            f.write(file_data)

print('Found', len(extras), 'extras total')

raw_dir = os.path.join(output_dir, 'raw')
extract_dir = os.path.join(output_dir, 'extract')
os.makedirs(raw_dir, exist_ok=True)
os.makedirs(extract_dir, exist_ok=True)

raw_dir = os.path.join(raw_dir, server)
extract_dir = os.path.join(extract_dir, server)
os.makedirs(raw_dir, exist_ok=True)
os.makedirs(extract_dir, exist_ok=True)

python_exec = sys.executable
cur_file_path = os.path.dirname(os.path.realpath(__file__))
tool_path = os.path.join(cur_file_path, '..', 'image_pull', 'PADTextureTool.py')

should_always_process = False

for extra in extras:
    raw_file_name = extra.file_name
    if not raw_file_name.startswith('block') or not raw_file_name.endswith('.btex'):
        print('skipping', raw_file_name)
        continue

    raw_file_path = os.path.join(raw_dir, raw_file_name)    
    if os.path.exists(raw_file_path) and not should_always_process:
        print('file exists', raw_file_path)
    else:
        print('downloading', extra.url, 'to', raw_file_path)
        download_file(extra.url, raw_file_path)

    extract_file_name = raw_file_name.upper().replace('BTEX', 'PNG')
    extract_file_path = os.path.join(extract_dir, extract_file_name)

    if os.path.exists(extract_file_path) and not should_always_process:
        print('skipping existing file', extract_file_path)
    else:
        print('processing', raw_file_path, 'to', extract_dir, 'with name', extract_file_name)
        os.system('{python} {tool} -o={output} {input}'.format(
            python=python_exec,
            tool=tool_path,
            input=raw_file_path,
            output=extract_dir))
print('done')
