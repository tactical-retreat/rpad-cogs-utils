#!/bin/bash
#
# Updates the local cache of voice files, fixes them, and uploads them to gcs.

RUN_DIR=/home/tactical0retreat/rpad-cogs-utils/orb_styles_pull
OUTPUT_DIR=/home/tactical0retreat/pad_data/orb_styles
DATA_DIR=/home/tactical0retreat/pad_data/processed

# Pull raws
python3 ${RUN_DIR}/PADOrbStylesDownload.py --output_dir=${OUTPUT_DIR} --data_dir=${DATA_DIR} --server=na
python3 ${RUN_DIR}/PADOrbStylesDownload.py --output_dir=${OUTPUT_DIR} --data_dir=${DATA_DIR} --server=jp
