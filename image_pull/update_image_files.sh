#!/bin/bash
#
# Updates the local cache of full monster pics / portraits from the JP server and
# uploads them to GCS, setting them public.

RUN_DIR=/home/tactical0retreat/rpad-cogs-utils/image_pull
IMG_DIR=/home/tactical0retreat/image_data
PROCESSED_DATA_DIR=/home/tactical0retreat/pad_data/processed

ALT_PROCESSOR_DIR=/home/tactical0retreat/git/pad-resources

yarn --cwd=${ALT_PROCESSOR_DIR} update

# Full pictures
python3 ${RUN_DIR}/PADTextureDownload.py --output_dir=${IMG_DIR}/na/full --server=NA
python3 ${RUN_DIR}/PADAnimatedGenerator.py --raw_dir=${IMG_DIR}/na/full/raw_data --working_dir=${ALT_PROCESSOR_DIR} --output_dir=${IMG_DIR}/na/full/corrected_data

python3 ${RUN_DIR}/PADTextureDownload.py --output_dir=${IMG_DIR}/jp/full --server=JP
python3 ${RUN_DIR}/PADAnimatedGenerator.py --raw_dir=${IMG_DIR}/jp/full/raw_data --working_dir=${ALT_PROCESSOR_DIR} --output_dir=${IMG_DIR}/jp/full/corrected_data

gsutil -m rsync -r ${IMG_DIR}/na/full/corrected_data gs://mirubot/padimages/na/full/
gsutil -m rsync -r ${IMG_DIR}/jp/full/corrected_data gs://mirubot/padimages/jp/full/

b2 sync ${IMG_DIR}/na/full/corrected_data b2://miru-data/padimages/na/full
b2 sync ${IMG_DIR}/jp/full/corrected_data b2://miru-data/padimages/jp/full

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

b2 sync ${IMG_DIR}/na/portrait/local b2://miru-data/padimages/na/portrait
b2 sync ${IMG_DIR}/jp/portrait/local b2://miru-data/padimages/jp/portrait
