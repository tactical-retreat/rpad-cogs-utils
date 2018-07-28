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

DISCORD_WEBHOOK_URL="https://discordapp.com/api/webhooks/472472663416373269/BZ_5NM_f1WENIzTvwfPKJlq-39ZwE2UIwcYEustCJly2eJDHIm4WYw0p9TvJ0rMnBuPW"

function hook_alert {
    echo "Pipeline failed"
    data="{\"username\": \"pipeline\", \"content\": \"$1\"}"
    curl -H "Content-Type: application/json" \
        -X POST \
        -d "$data" $DISCORD_WEBHOOK_URL
}

function hook_file {
  curl -F "data=@$1" $DISCORD_WEBHOOK_URL
}

function error_exit {
    echo "Pipeline failed"
    hook_alert "Pipeline failed"
    hook_file "/tmp/pad_data_update_log.txt"
}

function success_exit {
    echo "Pipeline finished"
    hook_alert "Pipeline finished"
}

trap error_exit ERR
trap success_exit EXIT

function dl_data {
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
}

dl_data $1

python3 ${EXEC_DIR}/padguide_processor.py \
  --input_dir=${DATA_DIR}/raw \
  --output_dir=${DATA_DIR}/processed \
  --db_config=${EXEC_DIR}/db_config.json \
  --doupdates

python3 ${EXEC_DIR}/extract_padguide_db.py \
  --db_config=${EXEC_DIR}/db_config.json  \
  --output_dir=${DATA_DIR}/padguide
  
  
# Temporary!
echo "Starting NA processing"
python3 ${EXEC_DIR}/pad_data_processing.py \
  --input_dir=${DATA_DIR}/raw/na \
  --output_dir=${DATA_DIR}/raw/na \
  --server=NA

echo "Starting JP processing"
python3 ${EXEC_DIR}/pad_data_processing.py \
  --input_dir=${DATA_DIR}/raw/jp \
  --output_dir=${DATA_DIR}/raw/jp \
  --server=JP

echo "Merging data"
python3 ${EXEC_DIR}/json_merge.py \
  --left=${DATA_DIR}/raw/na/guerrilla_data.json \
  --right=${DATA_DIR}/raw/jp/guerrilla_data.json \
  --output=${DATA_DIR}/merged/guerrilla_data.json

echo "Syncing"
gsutil -m rsync -r -c /home/tactical0retreat/pad_data/ gs://mirubot/paddata/

