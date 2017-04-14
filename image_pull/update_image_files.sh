#!/bin/bash
#
# Updates the local cache of full monster pics / portraits from the JP server and
# uploads them to GCS, setting them public.

# Full pictures
python3 /home/tactical0retreatrpad-cogs-utils/image_pull/PADTextureDownload.py --output_dir=/home/tactical0retreat/image_data/full
gsutil -m rsync -r image_data/full/corrected_data gs://rpad-discord.appspot.com/pad/full/
gsutil -m acl ch -u AllUsers:R gs://rpad-discord.appspot.com/pad/full/*

# Portraits
python3 /home/tactical0retreat/rpad-cogs-utils/image_pull/PADPortraitsDownload.py --output_dir=/home/tactical0retreat/image_data/portrait
gsutil -m rsync -r image_data/portrait/corrected_data gs://rpad-discord.appspot.com/pad/portrait/
gsutil -m acl ch -u AllUsers:R gs://rpad-discord.appspot.com/pad/portrait/*