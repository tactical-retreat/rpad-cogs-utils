from datetime import datetime, timedelta
import time
from collections import defaultdict

from enum import Enum
import pytz

from . import db_util
from . import processor_util
from . import dungeon as dbdungeon
from ..data import dungeon as datadungeon
from .monster import SqlItem
import json

VERSION = 'dadguide 0.1'

class ProcessedFloor(object):
	def __init__(self, stage_count, example_waves):
		self.stages = [ProcessedStage(idx+1) for idx in range(stage_count)]
		self.invades = ProcessedStage(0)

		stage_groupings = defaultdict(list)
		for wave in example_waves:
			if wave.is_invade():
				self.invades.add_wave_group([wave])
			else:
				stage_groupings[(wave.stage, wave.entry_id)].append(wave)

		for k, v in stage_groupings.items():
			self.stages[k[0]].add_wave_group(v)


		self.result_stages = []
		if self.invades.count > 0:
			self.result_stages.append(ResultStage(self.invades))
		for stage in self.stages:
			self.result_stages.append(ResultStage(stage))


class ProcessedStage(object):
	def __init__(self, stage_idx):
		self.stage_idx = stage_idx
		self.count = 0
		self.bonus_coins = 0

		# TODO: prioritize order by slot
		# TODO: alternate drops
		# TODO: drop rates

		self.spawn_to_drop = defaultdict(set)
		self.spawn_to_slot = defaultdict(set)
		self.spawn_to_count = defaultdict(int)
		self.spawns_per_wave = defaultdict(int)

	def add_wave_group(self, waves):
		self.count += 1
		self.spawns_per_wave[len(waves)] += 1
		for wave in waves:
			if wave.get_drop():
				self.spawn_to_drop[wave.monster_id].add(wave.get_drop())
			self.spawn_to_slot[wave.monster_id].add(wave.slot)
			self.spawn_to_count[wave.monster_id] += 1
			self.bonus_coins += wave.get_coins()


class ResultFloor(object):
	def __init__(self):
		pass

class ResultStage(object):
	def __init__(self, processed_stage: ProcessedStage):
		self.stage_idx = processed_stage.stage_idx
		self.slots = []

		fixed_spawns = []
		random_spawns = []
		for spawn, count in processed_stage.spawn_to_count.items():
			if count == processed_stage.count:
				fixed_spawns.append(spawn)
			else:
				random_spawns.append(spawn)

		for spawn in fixed_spawns:
			drops = processed_stage.spawn_to_drop[spawn]
			order = min(processed_stage.spawn_to_slot[spawn])
			self.slots.append(ResultSlot(spawn, order, drops, None))

		if random_spawns:
			wave_sizes = processed_stage.spawns_per_wave.values()
			fixed_spawn_count = len(fixed_spawns)
			min_random_spawns = min(wave_sizes) - fixed_spawn_count
			max_random_spawns = max(wave_sizes) - fixed_spawn_count
			comment = 'Random {}'.format(min_random_spawns)
			if min_random_spawns != max_random_spawns:
				comment += ' to {}'.format(max_random_spawns)
			for spawn in random_spawns:
				drops = processed_stage.spawn_to_drop[spawn]
				order = min(processed_stage.spawn_to_slot[spawn])
				self.slots.append(ResultSlot(spawn, order, drops, comment))


class ResultSlot(object):
	def __init__(self, monster_id: int, order: int, drops: set, comment: str):
		self.monster_id = monster_id
		self.order = order
		self.drops = drops
		self.comment = comment
		

def populate_dungeon(dungeon: dbdungeon.Dungeon, 
					 jp_dungeon: datadungeon.Dungeon,
					 na_dungeon: datadungeon.Dungeon,
					 waves=[]
					 ):
	dungeon.comment_us = VERSION

	# Most dungeons are this type
	dungeon.dungeon_type = dbdungeon.SimpleDungeonType.CoinDailyOther.value

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

	floor_to_waves = defaultdict(list)
	for wave in waves:
		floor_to_waves[wave.floor_id].append(wave)

	for idx in range(expected_floor_count):
		update_sub_dungeon(dungeon.resolved_sub_dungeons[idx], 
						   jp_dungeon.floors[idx],
						   na_dungeon.floors[idx],
						   floor_to_waves[idx+1])

	dungeon.icon_seq = 0
	max_dungeon = dungeon.resolved_sub_dungeons[-1]
	if max_dungeon.resolved_dungeon_monsters:
		max_monsters = max_dungeon.resolved_dungeon_monsters
		max_floor = max(map(lambda dm: dm.floor, max_monsters))
		max_floor_monsters = filter(lambda dm: dm.floor == max_floor, max_monsters)
		dungeon.icon_seq = max(map(lambda dm: dm.monster_no, max_floor_monsters)) 

def update_sub_dungeon(sub_dungeon: dbdungeon.SubDungeon, 
					   jp_dungeon_floor: datadungeon.DungeonFloor,
					   na_dungeon_floor: datadungeon.DungeonFloor,
					   waves
					   ):
	# TODO: fill in from waves
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

	processed_floor = ProcessedFloor(jp_dungeon_floor.waves, waves)
	for stage in processed_floor.result_stages:
		existing = filter(lambda dm: dm.floor == stage.stage_idx, sub_dungeon.resolved_dungeon_monsters)
		existing_id_to_monster = {dm.monster_no: dm for dm in existing}
		for slot in stage.slots:
			monster = existing_id_to_monster.get(slot.monster_id)
			if not monster:
				monster = dbdungeon.DungeonMonster()
				sub_dungeon.resolved_dungeon_monsters.append(monster)
			# TODO: fix
			monster.amount = 1
			# TODO: add
			monster.atk = 1
			monster.defense = 1
			monster.hp = 1
			monster.turn = 1

			monster.tsd_seq = sub_dungeon.tsd_seq
			monster.floor = stage.stage_idx

			monster.monster_no = slot.monster_id
			monster.drop_no = min(slot.drops) if slot.drops else 0
			monster.order_idx = slot.order
			monster.comment_kr = slot.comment
			monster.comment_jp = slot.comment
			monster.comment_us = slot.comment

			monster.tstamp = int(time.time()) * 1000

    # Need wave data for this
    # sub_dungeon.resolved_dungeon_monster = []

    # Not supported for now
    # sub_dungeon.resolved_sub_dungeon_score = None
    # sub_dungeon.resolved_sub_dungeon_reward = None
    # sub_dungeon.resolved_sub_dungeon_point = None



