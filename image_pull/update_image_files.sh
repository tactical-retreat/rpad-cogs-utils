#!/bin/bash
#
# Updates the local cache of full monster pics / portraits from the JP server and
# uploads them to GCS, setting them public.

# Full pictures
python3 /home/tactical0retreat/rpad-cogs-utils/image_pull/PADTextureDownload.py --output_dir=/home/tactical0retreat/image_data/na/full --server=NA
python3 /home/tactical0retreat/rpad-cogs-utils/image_pull/PADTextureDownload.py --output_dir=/home/tactical0retreat/image_data/jp/full --server=JP
gsutil -m rsync -r image_data/na/full/corrected_data gs://rpad-discord.appspot.com/pad/na/full/
gsutil -m rsync -r image_data/jp/full/corrected_data gs://rpad-discord.appspot.com/pad/jp/full/
gsutil -m acl ch -u AllUsers:R gs://rpad-discord.appspot.com/pad/na/full/*
gsutil -m acl ch -u AllUsers:R gs://rpad-discord.appspot.com/pad/jp/full/*

# Portraits
python3 /home/tactical0retreat/rpad-cogs-utils/image_pull/PADPortraitsDownload.py --output_dir=/home/tactical0retreat/image_data/na/portrait --server=NA
python3 /home/tactical0retreat/rpad-cogs-utils/image_pull/PADPortraitsDownload.py --output_dir=/home/tactical0retreat/image_data/jp/portrait --server=JP
gsutil -m rsync -r image_data/portrait/na/corrected_data gs://rpad-discord.appspot.com/pad/na/portrait/
gsutil -m rsync -r image_data/portrait/jp/corrected_data gs://rpad-discord.appspot.com/pad/jp/portrait/
gsutil -m acl ch -u AllUsers:R gs://rpad-discord.appspot.com/pad/portrait/*