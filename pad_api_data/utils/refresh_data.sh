mkdir pad_data
mkdir pad_data/raw
gsutil -m rsync -r -c gs://mirubot-data/paddata/raw pad_data/raw