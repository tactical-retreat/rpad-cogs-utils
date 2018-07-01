#!/bin/bash
#
# Expects an input config file formatted as:
# <[JP,NA]>,<[A,B,C,D,E]>,<uuid>,<int_id>,<RED,GREEN,BLUE>
#
# Group ID and starter color are not used, just for documentation
set -e
set -x

if [ $# -ne 1 ]; then
   echo "requires config file as input"
   exit
fi

echo "Processing $1"
IFS=","
DATA_DIR="/home/tactical0retreat/pad_data"
EXEC_DIR="/home/tactical0retreat/rpad-cogs-utils/pad_api_data"


while read server group uuid intid scolor
do
    do_only_bonus=""
    if [ ${group^^} != "A" ]
    then
        do_only_bonus="--only_bonus"
    fi

    echo "Processing ${server}/${group}/${uuid}/${intid} ${do_only_bonus}"
    python3 ${EXEC_DIR}/pad_data_pull.py \
        --output_dir=${DATA_DIR}/raw/${server,,} \
        --server=${server^^} \
        --user_uuid=${uuid} \
        --user_intid=${intid} \
        ${do_only_bonus}
done < $1

python3 ${EXEC_DIR}/padguide_processor.py \
  --input_dir=${DATA_DIR}/raw \
  --output_dir=${DATA_DIR}/processed \
  --db_config=${EXEC_DIR}/db_config.json \
  --doupdates

python3 ${EXEC_DIR}/extract_padguide_db.py \
  --db_config=${EXEC_DIR}/db_config.json  \
  --output_dir=${DATA_DIR}/padguide

echo "Syncing"
gsutil -m rsync -r /home/tactical0retreat/pad_data/ gs://mirubot/paddata/

