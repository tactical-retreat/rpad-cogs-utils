#!/bin/bash

echo "Downloading"
python3 /home/tactical0retreat/rpad-cogs-utils/pad_api_data/padguide/download_files.py \
  --output_dir=/home/tactical0retreat/pad_data/padguide

echo "Syncing"
gsutil -m rsync -r /home/tactical0retreat/pad_data/padguide/*.jsp.json gs://mirubot/paddata/padguide