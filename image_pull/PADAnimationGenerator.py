import argparse
import os
import tempfile


parser = argparse.ArgumentParser(
    description="Generates animated for pad monsters.", add_help=False)

inputGroup = parser.add_argument_group("Input")
inputGroup.add_argument("--raw_dir", required=True, help="Path to input BC files")
inputGroup.add_argument("--working_dir", required=True, help="Path to pad-resources project")

outputGroup = parser.add_argument_group("Output")
outputGroup.add_argument("--output_dir", required=True,
                         help="Path to a folder where output should be saved")

helpGroup = parser.add_argument_group("Help")
helpGroup.add_argument("-h", "--help", action="help", help="Displays this help message and exits.")
args = parser.parse_args()


def generate_resized_image(source_file, dest_file):
    ffmpg_cmd = 'ffmpeg -i {} -pix_fmt yuv420p -r 24 -c:v libx264 -filter:v "crop=640:390:0:60" {}'.format(
        source_file, dest_file)

    print('running', ffmpg_cmd)
    os.system(ffmpg_cmd)
    print('done')


def process_animated(working_dir, pad_id, file_path):
    bin_file = 'mons_{}.bin'.format(pad_id)
    bin_path = os.path.join('data', 'HT', 'bin', bin_file)
    xvfb_prefix = 'xvfb-run -s "-ac -screen 0 640x640x24"'
    yarn_cmd = 'yarn --cwd={} render --bin {} --out {} --nobg --video'.format(
        working_dir, bin_path, file_path)

    full_cmd = '{} {}'.format(xvfb_prefix, yarn_cmd)
    print('running', full_cmd)
    os.system(full_cmd)
    print('done')


raw_dir = args.raw_dir
working_dir = args.working_dir
output_dir = args.output_dir

for file_name in sorted(os.listdir(raw_dir)):
    if 'isanimated' not in file_name:
        continue

    pad_id = file_name.rstrip('.isanimated').lstrip('mons_').lstrip('0')
    final_image_name = '{}.mp4'.format(pad_id)
    corrected_file_path = os.path.join(output_dir, final_image_name)

    if os.path.exists(corrected_file_path):
        print('skipping', corrected_file_path)
        continue

    print('processing', corrected_file_path)
    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_corrected_file_path = os.path.join(temp_dir, final_image_name)
        process_animated(working_dir, pad_id, tmp_corrected_file_path)
        generate_resized_image(tmp_corrected_file_path, corrected_file_path)

print('done')
