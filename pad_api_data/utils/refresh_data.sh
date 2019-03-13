#!/usr/bin/env bash
mkdir pad_data
mkdir pad_data/raw
mkdir pad_data/processed
gsutil -m rsync -r -c gs://mirubot-data/paddata/raw pad_data/raw
gsutil -m rsync -x "(?!^wave_summary.csv$)" gs://mirubot-data/paddata/processed pad_data/processed