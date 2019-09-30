#!/bin/bash
#
# Updates the local cache of story files and uploads them to gcs.

RUN_DIR=/home/tactical0retreat/rpad-cogs-utils/story_pull
#TOOL_DIR=/home/tactical0retreat/rpad-cogs-utils/image_pull
TOOL_DIR=${RUN_DIR}
OUTPUT_DIR=/home/tactical0retreat/pad_data/story
DATA_DIR=/home/tactical0retreat/pad_data/processed

# Pull raws
# python3 ${RUN_DIR}/PADStoryDownload.py --tool_dir=${TOOL_DIR} --output_dir=${OUTPUT_DIR} --data_dir=${DATA_DIR} --server=na
python3 ${RUN_DIR}/PADStoryDownload.py --tool_dir=${TOOL_DIR} --output_dir=${OUTPUT_DIR} --data_dir=${DATA_DIR} --server=jp
