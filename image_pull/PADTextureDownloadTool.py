import argparse
import os
import re
import sys
import urllib.request

from PIL import Image
import padtools


def getOutputFileName(suggestedFileName):
    outputFileName = suggestedFileName
    # If the file is a "monster file" then pad the ID out with extra zeroes.
    try:
        prefix, mId, suffix = getOutputFileName.monsterFileNameRegex.match(suggestedFileName).groups()
        outputFileName = prefix + mId.zfill(5) + suffix
    except AttributeError:
        pass

    return outputFileName

getOutputFileName.monsterFileNameRegex = re.compile(r'^(MONS_)(\d+)(\..+)$', flags=re.IGNORECASE)


parser = argparse.ArgumentParser(description="Downloads and extracts P&D textures.", add_help=False)

outputGroup = parser.add_argument_group("Output")
outputGroup.add_argument("--output_dir", help="Path to a folder where output should be saved")

helpGroup = parser.add_argument_group("Help")
helpGroup.add_argument("-h", "--help", action="help", help="Displays this help message and exits.")
args = parser.parse_args()


jp_server = padtools.regions.japan.server
jp_assets = jp_server.assets

output_dir = args.output_dir

def download_file(url, file_path):
    response_object = urllib.request.urlopen(url)
    with response_object as response:
        file_data = response.read()
        with open(file_path, "wb") as f:
            f.write(file_data)

print('Found', len(jp_assets), 'assets total')


raw_dir = os.path.join(output_dir, 'raw_data')
extract_dir = os.path.join(output_dir, 'extract_data')
corrected_dir = os.path.join(output_dir, 'corrected_data')

python_exec = sys.executable
# tool_path = os.path.join('image_pull', 'PADTextureTool.py')
tool_path = os.path.join(os.getcwd(), 'src', 'image_pull', 'PADTextureTool.py')

IMAGE_SIZE = (640, 388)

for asset in jp_assets:
    asset_url = asset.url
    raw_file_name = os.path.basename(asset_url)

    if not raw_file_name.endswith('.bc'):
        continue

    raw_file_path = os.path.join(raw_dir, raw_file_name)

    if os.path.exists(raw_file_path):
        print('file exists', raw_file_path)
    else:
        print('downloading', asset.url, 'to', raw_file_path)
        download_file(asset_url, raw_file_path)


    extract_file_name = getOutputFileName(raw_file_name).upper().replace('BC', 'PNG')
    extract_file_path = os.path.join(extract_dir, extract_file_name)

    if os.path.exists(extract_file_path):
        print('skipping existing file', extract_file_path)
    else:
        print('processing', raw_file_path, 'to', extract_dir, 'with name', extract_file_name)
        os.system('{python} {tool} -nb -o={output} {input}'.format(
                      python=python_exec,
                      tool=tool_path,
                      input=raw_file_path,
                      output=extract_dir))


    corrected_file_path = os.path.join(corrected_dir, extract_file_name)

    if os.path.exists(corrected_file_path):
        print('skipping existing file', corrected_file_path)
    else:
        img = Image.open(extract_file_path)
        old_size = img.size

        new_img = Image.new("RGBA", IMAGE_SIZE)
        new_img.paste(img,
                      (int((IMAGE_SIZE[0] - old_size[0]) / 2),
                       int((IMAGE_SIZE[1] - old_size[1]) / 2)))

        new_img.save(corrected_file_path)
        print('done saving', corrected_file_path)
