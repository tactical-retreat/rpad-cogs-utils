#!/bin/bash
#
# Updates the local cache of hq monster pics and uploads them to GCS.

RUN_DIR=/home/tactical0retreat/rpad-cogs-utils/image_pull
IMG_DIR=/home/tactical0retreat/image_data

python3 ${RUN_DIR}/PADImageDownload.py --alt_input_dir=${IMG_DIR}/jp/full/raw_data --output_dir=${IMG_DIR}/hq_images

gsutil -m rsync -r ${IMG_DIR}/hq_images gs://mirubot/padimages/hq_images
b2 sync ${IMG_DIR}/hq_images gs://miru-data/padimages/hq_images
