#!/bin/bash
#
# Copies the configs from Private Miru (the master) to Public Miru

PUBLIC=/home/tactical0retreat/hosted_services/bots/Red-DiscordBot-PublicMiru/data
PRIVATE=/home/tactical0retreat/hosted_services/bots/Red-DiscordBot-PrivateMiru/data

cp -r ${PRIVATE}/donations/* ${PUBLIC}/donations
# cp -r ${PRIVATE}/padboard/* ${PUBLIC}/padboard
# cp -r ${PRIVATE}/padglobal/* ${PUBLIC}/padglobal
# cp -r ${PRIVATE}/stickers/* ${PUBLIC}/stickers
# cp -r ${PRIVATE}/streamcopy/* ${PUBLIC}/streamcopy