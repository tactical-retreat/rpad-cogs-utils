from datetime import datetime, timedelta
import time

from enum import Enum
import pytz

from . import db_util
from . import processor_util
from . import dungeon as dbdungeon
from ..data import dungeon as datadungeon
from .monster import SqlItem
import json

VERSION = 'dadguide 0.1'


def populate_dungeon(dungeon: dbdungeon.Dungeon, 
					 jp_dungeon: datadungeon.Dungeon,
					 na_dungeon: datadungeon.Dungeon
					 ):
	dungeon.comment_us = VERSION

	# Most dungeons are this type
	dungeon.dungeon_type = dbdungeon.SimpleDungeonType.CoinDailyOther.value

	# Need to merge in waves here, get the last monster
	# dungeon.icon_seq = ...

	dungeon.name_jp = jp_dungeon.clean_name
	dungeon.name_kr = na_dungeon.clean_name
	dungeon.name_us = na_dungeon.clean_name

	# Should maybe set an order_idx only if 0?
	# dungeon.order_idx = ...

	dungeon.show_yn = 1

	# Populate this with the right type if possible
	# dungeon.tdt_seq = dbdungeon.DungeonType.UNSORTED

	dungeon.tstamp = int(time.time()) * 1000

	stored_floor_count = len(dungeon.resolved_sub_dungeons)
	expected_floor_count = len(jp_dungeon.floors)

	if stored_floor_count and stored_floor_count != expected_floor_count:
		raise Exception('Altering dungeon size not supported')
	elif not stored_floor_count:
		dungeon.resolved_sub_dungeons = [dbdungeon.SubDungeon() for _ in range(expected_floor_count)]

	for idx in range(expected_floor_count):
		update_sub_dungeon(dungeon.resolved_sub_dungeons[idx], 
						   jp_dungeon.floors[idx],
						   na_dungeon.floors[idx])

def update_sub_dungeon(sub_dungeon: dbdungeon.SubDungeon, 
					   jp_dungeon_floor: datadungeon.DungeonFloor,
					   na_dungeon_floor: datadungeon.DungeonFloor
					   ):
	sub_dungeon.coin_max = 0
	sub_dungeon.coin_min = 0
	sub_dungeon.exp_max = 0
	sub_dungeon.exp_min = 0
	sub_dungeon.order_idx = jp_dungeon_floor.floor_number
	sub_dungeon.stage = jp_dungeon_floor.waves
	sub_dungeon.stamina = jp_dungeon_floor.stamina
	sub_dungeon.tsd_name_jp = jp_dungeon_floor.raw_name
	sub_dungeon.tsd_name_kr = na_dungeon_floor.raw_name
	sub_dungeon.tsd_name_us = na_dungeon_floor.raw_name
	sub_dungeon.tstamp = int(time.time()) * 1000

    # Need wave data for this
    # sub_dungeon.resolved_dungeon_monster = []

    # Not supported for now
    # sub_dungeon.resolved_sub_dungeon_score = None
    # sub_dungeon.resolved_sub_dungeon_reward = None
    # sub_dungeon.resolved_sub_dungeon_point = None



