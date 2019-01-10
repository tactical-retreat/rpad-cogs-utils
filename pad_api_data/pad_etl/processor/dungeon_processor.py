from collections import defaultdict
from statistics import mean
import time

from . import dungeon as dbdungeon
from ..common.padguide_values import SpecialIcons
from ..data import dungeon as datadungeon

VERSION = 'dadguide 0.3'
# Version log:
#  0.1 - initial version
#  0.2 - points, wave data, fixed card info
#  0.3 - drops, alt drops, rewards


class ProcessedFloor(object):
    def __init__(self, stage_count, example_waves, monster_id_to_card):
        self.stages = [ProcessedStage(idx + 1) for idx in range(stage_count)]
        self.invades = ProcessedStage(0)

        stage_groupings = defaultdict(list)
        for wave in example_waves:
            if wave.is_invade():
                self.invades.add_wave_group([wave], monster_id_to_card)
            else:
                stage_groupings[(wave.stage, wave.entry_id)].append(wave)

        for k, v in stage_groupings.items():
            self.stages[k[0]].add_wave_group(v, monster_id_to_card)

        self.result_stages = []
        if self.invades.count > 0:
            self.result_stages.append(ResultStage(self.invades))
        for stage in self.stages:
            self.result_stages.append(ResultStage(stage))


class ProcessedStage(object):
    def __init__(self, stage_idx):
        self.stage_idx = stage_idx
        self.count = 0
        self.coins = []
        self.xp = []
        self.mp = []

        # TODO: alternate drops
        # TODO: drop rates

        self.spawn_to_drop = defaultdict(set)
        self.spawn_to_level = {}
        self.spawn_to_slot = defaultdict(set)
        self.spawn_to_count = defaultdict(int)
        self.spawns_per_wave = defaultdict(int)

    def add_wave_group(self, waves, monster_id_to_card):
        """A wave group represents all the spawns encountered on a stage instance."""
        self.count += 1
        self.spawns_per_wave[len(waves)] += 1
        coins = 0
        xp = 0
        mp = 0
        for wave in waves:
            drop = wave.get_drop()
            if drop:
                self.spawn_to_drop[wave.monster_id].add(drop)
                data_card_data = monster_id_to_card[drop]
                mp += data_card_data.sell_mp

            self.spawn_to_level[wave.monster_id] = wave.monster_level
            self.spawn_to_slot[wave.monster_id].add(wave.slot)
            self.spawn_to_count[wave.monster_id] += 1

            enemy_data = monster_id_to_card[wave.monster_id].enemy()
            enemy_level = wave.monster_level
            coins += wave.get_coins()
            coins += enemy_data.coin.value_at(enemy_level)
            xp += enemy_data.xp.value_at(enemy_level)

        self.coins.append(coins)
        self.xp.append(xp)
        self.mp.append(mp)


class ResultFloor(object):
    def __init__(self):
        pass


class ResultStage(object):
    def __init__(self, processed_stage: ProcessedStage):
        self.stage_idx = processed_stage.stage_idx
        self.slots = []

        self.coins_min = min(processed_stage.coins) if processed_stage.coins else 0
        self.coins_max = max(processed_stage.coins) if processed_stage.coins else 0
        self.xp_min = min(processed_stage.xp) if processed_stage.xp else 0
        self.xp_max = max(processed_stage.xp) if processed_stage.xp else 0
        self.mp_avg = mean(processed_stage.mp) if processed_stage.mp else 0

        fixed_spawns = []
        random_spawns = []
        for spawn, count in processed_stage.spawn_to_count.items():
            if count == processed_stage.count:
                fixed_spawns.append(spawn)
            else:
                random_spawns.append(spawn)

        for spawn in fixed_spawns:
            level = processed_stage.spawn_to_level[spawn]
            drops = processed_stage.spawn_to_drop[spawn]
            order = min(processed_stage.spawn_to_slot[spawn])
            self.slots.append(ResultSlot(spawn, level, order, drops, None))

        if random_spawns:
            wave_sizes = processed_stage.spawns_per_wave.values()
            fixed_spawn_count = len(fixed_spawns)
            min_random_spawns = min(wave_sizes) - fixed_spawn_count
            max_random_spawns = max(wave_sizes) - fixed_spawn_count
            comment = 'Random {}'.format(min_random_spawns)
            if min_random_spawns != max_random_spawns:
                comment += ' to {}'.format(max_random_spawns)
            for spawn in random_spawns:
                level = processed_stage.spawn_to_level[spawn]
                drops = processed_stage.spawn_to_drop[spawn]
                order = min(processed_stage.spawn_to_slot[spawn])
                self.slots.append(ResultSlot(spawn, level, order, drops, comment))


class ResultSlot(object):
    def __init__(self,
                 monster_id: int,
                 monster_level: int,
                 order: int,
                 drops: set,
                 comment: str):
        self.monster_id = monster_id
        self.monster_level = monster_level
        self.order = order
        self.drops = drops
        self.comment = comment


def make_tree_from_cards(cards):
    tree = defaultdict(set)
    for card in cards:
        if card.ancestor_id == 0:
            continue
        ancestor_set = tree[card.ancestor_id]
        ancestor_set.add(card.card_id)
        tree[card.card_id] = ancestor_set
    return tree


def populate_dungeon(dungeon: dbdungeon.Dungeon,
                     jp_dungeon: datadungeon.Dungeon,
                     na_dungeon: datadungeon.Dungeon,
                     waves=[],
                     cards=[],
                     na_cards=[],
                     floor_text={}
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
        dungeon.resolved_sub_dungeons = [dbdungeon.SubDungeon()
                                         for _ in range(expected_floor_count)]

    floor_to_waves = defaultdict(list)
    for wave in waves:
        floor_to_waves[wave.floor_id].append(wave)

    monster_name_to_id = {x.name.lower(): x for x in cards + na_cards if x.card_id < 9999}

    monster_id_to_card = {c.card_id: c for c in cards}
    for idx in range(expected_floor_count):
        update_sub_dungeon(dungeon.resolved_sub_dungeons[idx],
                           jp_dungeon.floors[idx],
                           na_dungeon.floors[idx],
                           floor_to_waves[idx + 1],
                           monster_id_to_card,
                           floor_text.get(idx + 1, ''),
                           monster_name_to_id)

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
                       waves,
                       monster_id_to_card,
                       floor_text,
                       monster_name_to_id
                       ):
    sub_dungeon.order_idx = jp_dungeon_floor.floor_number
    sub_dungeon.stage = jp_dungeon_floor.waves
    sub_dungeon.stamina = jp_dungeon_floor.stamina
    sub_dungeon.tsd_name_jp = jp_dungeon_floor.clean_name
    sub_dungeon.tsd_name_kr = na_dungeon_floor.clean_name
    sub_dungeon.tsd_name_us = na_dungeon_floor.clean_name
    sub_dungeon.tstamp = int(time.time()) * 1000

    processed_floor = ProcessedFloor(jp_dungeon_floor.waves, waves, monster_id_to_card)
    result_stages = processed_floor.result_stages

    sub_dungeon.coin_max = int(sum([rs.coins_max for rs in result_stages]))
    sub_dungeon.coin_min = int(sum([rs.coins_min for rs in result_stages]))
    sub_dungeon.exp_max = int(sum([rs.xp_min for rs in result_stages]))
    sub_dungeon.exp_min = int(sum([rs.xp_max for rs in result_stages]))

    if jp_dungeon_floor.score:
        if sub_dungeon.resolved_sub_dungeon_score is None:
            sub_dungeon.resolved_sub_dungeon_score = dbdungeon.SubDungeonScore()
        sub_dungeon.resolved_sub_dungeon_score.score = jp_dungeon_floor.score

    if sub_dungeon.resolved_sub_dungeon_point is None:
        sub_dungeon.resolved_sub_dungeon_point = dbdungeon.SubDungeonPoint()
    total_avg_mp = round(sum([rs.mp_avg for rs in result_stages]), 4)
    sub_dungeon.resolved_sub_dungeon_point.tot_point = total_avg_mp

    floor_text = floor_text.lower()
    reward_value = None
    if 'reward' in floor_text or 'first time clear' in floor_text or '初クリア報酬' in floor_text:
        if 'coins' in floor_text or '万コイン' in floor_text:
            reward_value = SpecialIcons.Coin.value
        elif 'pal points' in floor_text or '友情ポイント' in floor_text:
            reward_value = SpecialIcons.Point.value
        elif 'dungeon' in floor_text:
            reward_value = SpecialIcons.QuestionMark.value
        elif '+ points' in floor_text or '+ポイント' in floor_text:
            reward_value = SpecialIcons.StarPlusEgg.value
        elif 'magic stone' in floor_text:
            reward_value = SpecialIcons.MagicStone.value
        else:
            matched_monsters = set()
            for m_name in monster_name_to_id.keys():
                if m_name in floor_text:
                    matched_monsters.add(m_name)
            if matched_monsters:
                best_match = max(matched_monsters, key=len)
                reward_value = monster_name_to_id[best_match].card_id

        if reward_value is None:
            reward_value = SpecialIcons.RedX.value

    if reward_value:
        # TODO: support 1/2 reward types?
        reward_text = '0/{}'.format(reward_value)
        if sub_dungeon.resolved_sub_dungeon_reward is None:
            sub_dungeon.resolved_sub_dungeon_reward = dbdungeon.SubDungeonReward()
        sub_dungeon.resolved_sub_dungeon_reward.data = reward_text

    monster_tree = make_tree_from_cards(monster_id_to_card.values())

    for stage in result_stages:
        existing = filter(lambda dm: dm.floor == stage.stage_idx,
                          sub_dungeon.resolved_dungeon_monsters)
        existing_id_to_monster = {dm.monster_no: dm for dm in existing}
        for slot in stage.slots:
            card = monster_id_to_card[slot.monster_id]

            # TODO: this might need mapping due to na/jp skew for monster_no
            monster_id = slot.monster_id
            monster_id = monster_id % 10000 if monster_id > 9999 else monster_id

            if monster_id <= 0:
                raise Exception('Bad monster ID', slot.monster_id, card.card_id, card.base_id)

            monster = existing_id_to_monster.get(monster_id)
            if not monster:
                monster = dbdungeon.DungeonMonster()
                monster.monster_no = monster_id
                sub_dungeon.resolved_dungeon_monsters.append(monster)

            enemy_data = card.enemy()
            enemy_level = slot.monster_level

            # TODO: fix
            monster.amount = 1

            modifiers = jp_dungeon_floor.modifiers_clean
            monster.atk = int(round(modifiers['atk'] * enemy_data.atk.value_at(enemy_level)))
            monster.defense = int(
                round(modifiers['def'] * enemy_data.defense.value_at(enemy_level)))
            monster.hp = int(round(modifiers['hp'] * enemy_data.hp.value_at(enemy_level)))
            monster.turn = enemy_data.turns

            monster.tsd_seq = sub_dungeon.tsd_seq
            monster.floor = stage.stage_idx

            monster.drop_no = 0
            if slot.drops:
                monster_drops = set()
                other_drops = set()
                for drop in slot.drops:
                    if drop in monster_tree[monster_id]:
                        # Drop is an evo of the current monster
                        monster_drops.add(drop)
                    else:
                        # Drop is an alternate, like collab mats
                        other_drops.add(drop)

                if len(monster_drops) > 1:
                    raise Exception('expected at most one monster drop', monster_drops)

                # Sort the other drops for indexing purposes
                other_drops = list(sorted(other_drops))

                if monster_drops:
                    monster.drop_no = next(iter(monster_drops))
                elif other_drops:
                    # We need drop_no to be set; since the monster didn't drop itself, set the
                    # first other drop
                    monster.drop_no = other_drops.pop(0)

                existing_drops = {
                    int(ed.monster_no): ed for ed in monster.resolved_dungeon_monster_drops}

                for drop in other_drops:
                    if int(drop) in existing_drops:
                        dmd = existing_drops.pop(drop)
                    else:
                        dmd = dbdungeon.DungeonMonsterDrop()
                        monster.resolved_dungeon_monster_drops.append(dmd)
                    dmd.monster_no = drop
                    dmd.order_idx = drop
                    dmd.status = 0

                if existing_drops:
                    raise Exception('unmatched drop records remain:', existing_drops)

            monster.order_idx = slot.order
            monster.comment_kr = slot.comment
            monster.comment_jp = slot.comment
            monster.comment_us = slot.comment

            monster.tstamp = int(time.time()) * 1000

    # Not supported for now
    # sub_dungeon.resolved_sub_dungeon_score = None
    # sub_dungeon.resolved_sub_dungeon_reward = None
    # sub_dungeon.resolved_sub_dungeon_point = None
