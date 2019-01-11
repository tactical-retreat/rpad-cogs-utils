#!/bin/bash
#
# Builds the OBB file that is used with DadGuide releases.
# Contains images zipped up without compression.
# Run this before every release and attach it to the APK.
set -e
set -x

rm -f /tmp/dadguide.obb
(cd /var/www/html/padguide/images/ && zip -r -0 - icons/icon* icons/awoken* icons/type* wicons) > /tmp/dadguide.obb
gsutil cp /tmp/dadguide.obb gs://mirubot/paddata/padguide_db/
