#!/bin/bash
#
# Downloads Azure Lane images and data.

python3 /home/tactical0retreat/rpad-cogs-utils/azure_scrape/image_download.py --output_dir=/home/tactical0retreat/al_image_data/
gsutil -m rsync -r /home/tactical0retreat/al_image_data gs://mirubot/alimages/raw
gsutil -m acl ch -u AllUsers:R gs://mirubot/alimages/raw/*
