#!/bin/bash
#
# Rebuilds the PadGuide flattened DB file, and zips it in the large data folder.

set -e
set -x

DATA_DIR="/home/tactical0retreat/pad_large_data"
EXEC_DIR="/home/tactical0retreat/rpad-cogs-utils/pad_api_data"

echo "Building DB dump"
python3 ${EXEC_DIR}/padguide/build_padguide_db_file.py \
  --db_config=${EXEC_DIR}/db_config.json \
  --base_db=${DATA_DIR}/padguide_db/576-Panda.sql \
  --output_file=${DATA_DIR}/padguide_db/Panda.sql
                 
# echo "Zipping/copying DB dump"
rm ${DATA_DIR}/padguide_db/Panda.sql.zip
zip -j ${DATA_DIR}/padguide_db/Panda.sql.zip ${DATA_DIR}/padguide_db/Panda.sql
