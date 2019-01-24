#!/bin/bash
#
# Updates the local cache of full monster pics / portraits from the JP server and
# uploads them to GCS, setting them public.

RUN_DIR=/home/tactical0retreat/rpad-cogs-utils/image_pull
IMG_DIR=/home/tactical0retreat/image_data
PROCESSED_DATA_DIR=/home/tactical0retreat/pad_data/processed

# Full pictures
python3 ${RUN_DIR}/PADTextureDownload.py --output_dir=${IMG_DIR}/na/full --server=NA
python3 ${RUN_DIR}/PADImageDownload.py --output_dir=${IMG_DIR}/na/full

python3 ${RUN_DIR}/PADTextureDownload.py --output_dir=${IMG_DIR}/jp/full --server=JP
python3 ${RUN_DIR}/PADImageDownload.py --output_dir=${IMG_DIR}/jp/full

gsutil -m rsync -r ${IMG_DIR}/na/full/corrected_data gs://mirubot/padimages/na/full/
gsutil -m rsync -r ${IMG_DIR}/jp/full/corrected_data gs://mirubot/padimages/jp/full/

# Portraits
python3 ${RUN_DIR}/PADPortraitsGenerator.py \
  --input_dir=${IMG_DIR}/na/full/extract_data \
  --data_dir=${PROCESSED_DATA_DIR} \
  --card_templates_file=${RUN_DIR}/wide_cards.png \
  --server=na \
  --output_dir=${IMG_DIR}/na/portrait/local_tmp

python3 ${RUN_DIR}/PADPortraitsGenerator.py \
  --input_dir=${IMG_DIR}/jp/full/extract_data \
  --data_dir=${PROCESSED_DATA_DIR} \
  --card_templates_file=${RUN_DIR}/wide_cards.png \
  --server=jp \
  --output_dir=${IMG_DIR}/jp/portrait/local

python3 ${RUN_DIR}/PADPortraitsCombiner.py \
  --na_dir=${IMG_DIR}/na/portrait/local_tmp \
  --jp_dir=${IMG_DIR}/jp/portrait/local \
  --output_dir=${IMG_DIR}/na/portrait/local

gsutil -m rsync -r ${IMG_DIR}/na/portrait/local gs://mirubot/padimages/na/portrait/
gsutil -m rsync -r ${IMG_DIR}/jp/portrait/local gs://mirubot/padimages/jp/portrait/
