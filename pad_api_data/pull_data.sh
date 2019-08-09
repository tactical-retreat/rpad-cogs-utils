#!/bin/bash
#
# Expects an input config file formatted as:
# <[JP,NA]>,<[A,B,C,D,E]>,<uuid>,<int_id>,<RED,GREEN,BLUE>
#
# Group ID and starter color are not used, just for documentation
#
# If a second argument is supplied, it is used as the discord alerting URL
set -e
set -x

if [ $# -lt 1 ]; then
   echo "requires config file as input"
   exit
fi

echo "Processing $1"
IFS=","
DATA_DIR="/home/tactical0retreat/pad_data"
EXEC_DIR="/home/tactical0retreat/rpad-cogs-utils/pad_api_data"

DISCORD_WEBHOOK_URL=""
if [ $# -eq 2 ]; then
    DISCORD_WEBHOOK_URL="https://discordapp.com/api/webhooks/$2"
fi

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

function human_fixes_check {
    human_fixes_path="/tmp/pipeline_human_fixes.txt"
    if [ -s ${human_fixes_path} ]
    then
        echo "Alerting for human fixes"
        hook_alert "Pipeline requires human intervention"
        hook_file ${human_fixes_path}
    else
        echo "No fixes required"
    fi
}

function success_exit {
    echo "Pipeline finished"
    # Disabling; spammy
    # hook_alert "Pipeline finished"
}

if [ $DISCORD_WEBHOOK_URL != "" ]; then
	trap error_exit ERR
	trap success_exit EXIT
fi

function dl_data {
    while read server group uuid intid scolor
    do
        do_only_bonus=""
        if [ ${scolor^^} != "RED" ]
        then
            do_only_bonus="--only_bonus"
        fi

        echo "Processing ${server}/${scolor}/${uuid}/${intid} ${do_only_bonus}"
        python3 ${EXEC_DIR}/pad_data_pull.py \
            --output_dir=${DATA_DIR}/raw/${server,,} \
            --server=${server^^} \
            --user_uuid=${uuid} \
            --user_intid=${intid} \
            --user_group=${scolor} \
            ${do_only_bonus}
    done < $1
}

dl_data $1

echo "copying image data"
python3 ${EXEC_DIR}/copy_image_data.py \
  --base_dir=/home/tactical0retreat/image_data \
  --output_dir=/var/www/html/padguide/images/icons

echo "updating padguide"
python3 ${EXEC_DIR}/padguide_processor.py \
  --input_dir=${DATA_DIR}/raw \
  --output_dir=${DATA_DIR}/processed \
  --db_config=${EXEC_DIR}/db_config.json \
  --doupdates

human_fixes_check

#echo "exporting wave data"
#python3 ${EXEC_DIR}/dungeon_wave_exporter.py \
#  --db_config=${EXEC_DIR}/db_config.json \
#  --processed_dir=${DATA_DIR}/processed

#echo "updating padguide_dev"
#python3 ${EXEC_DIR}/padguide_processor.py \
#  --input_dir=${DATA_DIR}/raw \
#  --output_dir=${DATA_DIR}/processed \
#  --db_config=${EXEC_DIR}/db_config_dev.json \
#  --doupdates \
#  --dev \
#  --skipintermediate

echo "serializing padguide"
python3 ${EXEC_DIR}/extract_padguide_db.py \
  --db_config=${EXEC_DIR}/db_config.json  \
  --output_dir=${DATA_DIR}/padguide
  
# echo "Building DB dump"
# python3 ${EXEC_DIR}/build_padguide_db_file.py \
#   --db_config=${EXEC_DIR}/db_config.json \
#   --base_db=${DATA_DIR}/padguide_db/576-Panda.sql \
#   --output_file=${DATA_DIR}/padguide_db/Panda.sql
  
# echo "Zipping/copying DB dump"
# rm ${DATA_DIR}/padguide_db/Panda.sql.zip
# zip -j ${DATA_DIR}/padguide_db/Panda.sql.zip ${DATA_DIR}/padguide_db/Panda.sql
# cp ${DATA_DIR}/padguide_db/Panda.sql.zip /var/www/html/padguide/data

echo "Syncing"
gsutil -m rsync -r -c /home/tactical0retreat/pad_large_data/ gs://mirubot/paddata/
gsutil -m rsync -r -c /home/tactical0retreat/pad_data/ gs://mirubot-data/paddata/

# Make a public accessible copy for reni's blog
gsutil -m rsync -r -c gs://mirubot-data/paddata/ gs://mirubot/protic/paddata/

# Update B2 copy
b2 sync --compareVersions size /home/tactical0retreat/pad_data b2://miru-data/paddata
b2 sync --compareVersions size /home/tactical0retreat/pad_large_data/padguide_db b2://miru-data/padguide/db
b2 sync --compareVersions size /var/www/html/padguide/images b2://miru-data/padguide/images

