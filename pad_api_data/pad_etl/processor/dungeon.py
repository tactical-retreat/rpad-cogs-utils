import json
import time

from enum import Enum

from . import db_util
from .monster import SqlItem


def full_columns(o: SqlItem, remove_cols=[], add_cols=[]):
    cols = set(vars(o).keys())
    if o.uses_local_primary_key():
        cols.discard(o._key())
    cols.discard('tstamp')
    # Do something about tstamp in SqlItem insert or update
    cols = set([x for x in cols if not x.startswith('resolved')])
    cols = cols.difference(remove_cols)
    cols = cols.union(add_cols)

    if hasattr(type(o), 'COL_MAPPINGS'):
        mappings = type(o).COL_MAPPINGS
        for k, v in mappings.items():
            cols.discard(v)
            cols.add(k)

    return list(cols)


def dump_helper(x):
    if isinstance(x, Enum):
        return str(x)
    elif hasattr(x, '__dict__'):
        return vars(x)
    else:
        return repr(x)


def dump(obj):
    return json.dumps(obj, indent=4, sort_keys=True, default=dump_helper)


class Icon(SqlItem):
    """Does not seem to be necessary.

    Looks like the icon loading works fine without actually having a ref to an entry
    in this table, seems to assume that icon_1234.

    If we ever add a foreign key to this table, there's a 0000 icon that we can map 0 to (blank questionmark).
    Some other dungeons in the dungeon table don't have valid mappings though, they need to be fixed too.

    Created this class but not bothering to populate for now.
    """
    NOT_SET = 0
    TABLE = 'icon_list'
    KEY_COL = 'icon_seq'

    def __init__(self,
                 icon_seq: int=None,
                 icon_url: str=None,
                 tstamp: int=None):
        self.icon_seq = icon_seq
        self.icon_url = icon_url
        self.tstamp = tstamp or (int(time.time()) * 1000)

    def __repr__(self):
        return dump(self)

    def _table(self):
        return Icon.TABLE

    def _key(self):
        return Icon.KEY_COL

    def _insert_columns(self):
        return full_columns(self)

    def _update_columns(self):
        return full_columns(self)


class SimpleDungeonType(Enum):
    """This is used for the 'dungeon_type' field"""
    Normal = 0
    CoinDailyOther = 1
    Technical = 2
    Etc = 3


class DungeonType(SqlItem):
    """Dungeon type, used as part of filtering.

    An 'unsorted' entry exists as a placeholder at tdt_seq=41
    """
    UNSORTED = 41
    TABLE = 'dungeon_type_list'
    KEY_COL = 'tdt_seq'

    def __init__(self,
                 order_idx: int=None,
                 tdt_name_jp: str=None,
                 tdt_name_kr: str=None,
                 tdt_name_us: str=None,
                 tdt_seq: int=None,
                 tstamp: int=None):
        self.order_idx = order_idx
        self.tdt_name_jp = tdt_name_jp
        self.tdt_name_kr = tdt_name_kr or tdt_name_us
        self.tdt_name_us = tdt_name_us
        self.tdt_seq = tdt_seq  # Primary Key
        self.tstamp = tstamp or (int(time.time()) * 1000)

    def __repr__(self):
        return dump(self)

    def _table(self):
        return DungeonType.TABLE

    def _key(self):
        return DungeonType.KEY_COL

    def _insert_columns(self):
        return full_columns(self)

    def _update_columns(self):
        return full_columns(self)


class Dungeon(SqlItem):
    """The dungeon object."""
    TABLE = 'dungeon_list'
    KEY_COL = 'dungeon_seq'

    def __init__(self,
                 app_version: str=None,
                 comment_jp: str=None,
                 comment_kr: str=None,
                 comment_us: str=None,
                 dungeon_seq: int=None,
                 dungeon_type: int=None,
                 dungeon_type_enum: SimpleDungeonType=None,
                 icon_seq: int=None,
                 name_jp: str=None,
                 name_kr: str=None,
                 name_us: str=None,
                 order_idx: int=None,
                 show_yn: int=None,
                 tdt_seq: int=None,
                 tstamp: int=None):
        self.app_version = app_version  # Unused
        self.comment_jp = comment_jp  # Unused
        self.comment_kr = comment_kr  # Unused
        self.comment_us = comment_us  # Unused
        self.dungeon_seq = dungeon_seq  # Primary Key
        self.dungeon_type = dungeon_type or (dungeon_type_enum.value if dungeon_type_enum else None)
        self.dungeon_type_enum = dungeon_type_enum or (
            SimpleDungeonType(dungeon_type) if dungeon_type is not None else None)
        self.icon_seq = icon_seq  # FK to Icon but seems not to be necessary
        self.name_jp = name_jp
        self.name_kr = name_kr or name_us
        self.name_us = name_us
        self.order_idx = order_idx
        self.show_yn = show_yn
        self.tdt_seq = tdt_seq  # FK to DungeonType
        self.tstamp = tstamp or int(time.time()) * 1000

        self.resolved_dungeon_type = None
        self.resolved_icon = None
        self.resolved_sub_dungeons = []

    def __repr__(self):
        return dump(self)

    def _table(self):
        return Dungeon.TABLE

    def _key(self):
        return Dungeon.KEY_COL

    def _insert_columns(self):
        return full_columns(self, remove_cols=['dungeon_type_enum'])

    def _update_columns(self):
        return full_columns(self, remove_cols=['dungeon_type_enum'])


class DungeonSkillDamage(SqlItem):
    """Only present on attacks."""

    def __init__(self,
                 damage: int=None,
                 tds_seq: int=None,
                 tstamp: int=None):
        self.damage = damage  # Damage dealt
        self.tds_seq = tds_seq  # Primary Key
        self.tstamp = tstamp or int(time.time()) * 1000

    def __repr__(self):
        return dump(self)

    def _table(self):
        return 'dungeon_skill_damage_list'

    def _key(self):
        return 'tds_seq'

    def _insert_columns(self):
        return full_columns(self)

    def _update_columns(self):
        return full_columns(self)


class SubDungeon(SqlItem):
    """Stages of a dungeon."""
    TABLE = 'sub_dungeon_list'
    KEY_COL = 'tsd_seq'
    LIST_COL = 'dungeon_seq'

    def __init__(self,
                 coin_max: int=None,
                 coin_min: int=None,
                 dungeon_seq: int=None,
                 exp_max: int=None,
                 exp_min: int=None,
                 order_idx: int=None,
                 stage: int=None,
                 stamina: int=None,
                 tsd_name_jp: str=None,
                 tsd_name_kr: str=None,
                 tsd_name_us: str=None,
                 tsd_seq: int=None,
                 tstamp: int=None):
        self.coin_max = coin_max  # Populate as 0 for now
        self.coin_min = coin_min  # Populate as 0 for now
        self.dungeon_seq = dungeon_seq  # FK to Dungeon (injected)
        self.exp_max = exp_max  # Populate as 0 for now
        self.exp_min = exp_min  # Populate as 0 for now
        self.order_idx = order_idx  # 1-indexed
        self.stage = stage  # Number of floors (shows up as 'battle' in the header)
        self.stamina = stamina  # Entry stamina
        self.tsd_name_jp = tsd_name_jp
        self.tsd_name_kr = tsd_name_kr or tsd_name_us
        self.tsd_name_us = tsd_name_us
        self.tsd_seq = tsd_seq  # Primary Key
        self.tstamp = tstamp or int(time.time()) * 1000

        self.resolved_dungeon_monsters = []
        self.resolved_sub_dungeon_score = None
        self.resolved_sub_dungeon_reward = None
        self.resolved_sub_dungeon_point = None

    def __repr__(self):
        return dump(self)

    def _table(self):
        return SubDungeon.TABLE

    def _key(self):
        return SubDungeon.KEY_COL

    def _insert_columns(self):
        return full_columns(self)

    def _update_columns(self):
        return full_columns(self)


class SubDungeonPoint(SqlItem):
    """MP estimate for clearing dungeon if all drops are sold.

    Seems to be required.
    Being populated as 0 automatically for now.
    """
    TABLE = 'sub_dungeon_point_list'
    KEY_COL = SubDungeon.KEY_COL
    LIST_COL = SubDungeon.KEY_COL

    def __init__(self,
                 tot_point: float=None,
                 tsd_seq: int=None,
                 tstamp: int=None):
        self.tot_point = tot_point  # Estimated points earned.
        self.tsd_seq = tsd_seq  # FK to SubDungeon (injected)
        self.tstamp = tstamp or int(time.time()) * 1000

    def __repr__(self):
        return dump(self)

    def uses_local_primary_key(self):
        return False

    def _table(self):
        return SubDungeonPoint.TABLE

    def _key(self):
        return SubDungeonPoint.KEY_COL

    def _insert_columns(self):
        return full_columns(self)

    def _update_columns(self):
        return full_columns(self)


class SubDungeonReward(SqlItem):
    """Optional reward for clearing floor, e.g. challenges.

    Format looks like: 0/1329|0/521|0/522
        0 - icon for reward (monsters use IDs, 999x for special (e.g. mp))
        1 - coins reward
        2 - pal points

    Not yet supported.
    """
    TABLE = 'sub_dungeon_reward_list'
    KEY_COL = SubDungeon.KEY_COL
    LIST_COL = SubDungeon.KEY_COL

    def __init__(self,
                 data: str=None,
                 tsd_seq: int=None,
                 tstamp: int=None):
        self.data = data  # Details above
        self.tsd_seq = tsd_seq  # FK to SubDungeon (injected)
        self.tstamp = tstamp or int(time.time()) * 1000

    def __repr__(self):
        return dump(self)

    def uses_local_primary_key(self):
        return False

    def _table(self):
        return SubDungeonReward.TABLE

    def _key(self):
        return SubDungeonReward.KEY_COL

    def _insert_columns(self):
        return full_columns(self)

    def _update_columns(self):
        return full_columns(self)


class SubDungeonScore(SqlItem):
    """Optional score for s-rank.

    Not yet supported.
    """
    TABLE = 'sub_dungeon_score_list'
    KEY_COL = SubDungeon.KEY_COL
    LIST_COL = SubDungeon.KEY_COL

    def __init__(self,
                 score: int=None,
                 tsd_seq: int=None,
                 tstamp: int=None):
        self.score = score  # Score value required
        self.tsd_seq = tsd_seq  # FK to SubDungeon (injected)
        self.tstamp = tstamp or (int(time.time()) * 1000)

    def __repr__(self):
        return dump(self)

    def uses_local_primary_key(self):
        return False

    def _table(self):
        return SubDungeonScore.TABLE

    def _key(self):
        return SubDungeonScore.KEY_COL

    def _insert_columns(self):
        return full_columns(self)

    def _update_columns(self):
        return full_columns(self)


class DungeonMonster(SqlItem):
    TABLE = 'dungeon_monster_list'
    KEY_COL = 'tdm_seq'
    LIST_COL = SubDungeon.KEY_COL
    COL_MAPPINGS = {'def': 'defense'}

    def __init__(self,
                 amount: int=None,
                 atk: int=None,
                 comment_kr: str=None,
                 comment_jp: str=None,
                 comment_us: str=None,
                 defense: int=None,  # Field actually called def!
                 drop_no: int = None,
                 dungeon_seq: int=None,
                 floor: int=None,
                 hp: int=None,
                 monster_no: int=None,
                 order_idx: int=None,
                 tdm_seq: int=None,
                 tsd_seq: int=None,
                 tstamp: int=None,
                 turn: int=None):
        self.amount = amount  # Number that appear, displays as 'x<amount>' if amount > 1
        self.atk = atk

        # These fields show up in the UI below the spawn name
        # Seem to be kind of important, including:
        #   Random x of y
        #   Randomly invade
        #   Use below skills in order
        #   x% Drop
        #   Rare
        #   Attribute changes to x when < 50%
        #   Internal counter exists. Change pattern according to the count
        self.comment_kr = comment_kr or comment_us
        self.comment_jp = comment_jp or comment_us
        self.comment_us = comment_us

        self.defense = defense  # Field actually called def!
        # 0 if no drop, otherwise a monster_no from the Monsters table (no link)
        self.drop_no = drop_no
        self.dungeon_seq = dungeon_seq  # FK to Dungeon table (not mapped; use SubDungeon)
        self.floor = floor  # 0-indexed floor monster appears on
        self.hp = hp
        # FK to Monsters table; should be from the monster tree (no link)
        self.monster_no = monster_no
        self.order_idx = order_idx  # <0 for invades, 0-indexed normally
        self.tdm_seq = tdm_seq  # Primary Key
        self.tsd_seq = tsd_seq  # FK to SubDungeon (injected)
        self.tstamp = tstamp or (int(time.time()) * 1000)
        self.turn = turn  # Turns between attacks (min 1)

        self.resolved_dungeon_monster_drops = []
        self.resolved_dungeon_skills = []

    def __repr__(self):
        return dump(self)

    def _table(self):
        return DungeonMonster.TABLE

    def _key(self):
        return DungeonMonster.KEY_COL

    def _insert_columns(self):
        return full_columns(self)

    def _update_columns(self):
        return full_columns(self)


class DungeonMonsterDrop(SqlItem):
    """Represents alternate drops for a monster, and is optional."""
    TABLE = 'dungeon_monster_drop_list'
    KEY_COL = 'tdmd_seq'
    LIST_COL = DungeonMonster.KEY_COL

    def __init__(self,
                 monster_no: int=None,
                 order_idx: int=None,
                 status: int=None,
                 tdmd_seq: int=None,
                 tdm_seq: int=None,
                 tstamp: int=None):
        self.monster_no = monster_no  # FK to Monster (not mapped)
        self.order_idx = order_idx  # Generally 10 * n where n is 1-indexed
        self.status = status  # Generally 0; Rarely 2, not sure why (might be 'deleted')
        self.tdmd_seq = tdmd_seq  # Primary Key
        self.tdm_seq = tdm_seq  # Foreign Key to DungeonMonster (injected)
        self.tstamp = tstamp or (int(time.time()) * 1000)

    def __repr__(self):
        return dump(self)

    def _table(self):
        return DungeonMonsterDrop.TABLE

    def _key(self):
        return DungeonMonsterDrop.KEY_COL

    def _insert_columns(self):
        return full_columns(self)

    def _update_columns(self):
        return full_columns(self, remove_cols=['tdm_seq'])


class DungeonSkill(SqlItem):
    """An association between DungeonMonster, Skill, and DungeonSkillDamage.

    (tdm_seq, tds_seq, ts_seq) is the Primary Key.
    tds_seq is optional (enter as 0); not all dungeon skills are attacks (e.g. status shield).
    """

    def __init__(self,
                 tdm_seq: int=None,
                 tds_seq: int=None,
                 ts_seq: int=None,
                 tstamp: int=None):
        self.tdm_seq = tdm_seq  # FK to DungeonMonster (injected)
        self.tds_seq = tds_seq  # FK to DungeonSkillDamage (local)
        self.ts_seq = ts_seq  # FK to Skill (local)
        self.tstamp = tstamp or (int(time.time()) * 1000)

        self.resolved_dungeon_skill_damage = None
        self.resolved_skill = None

    def __repr__(self):
        return dump(self)

    def _table(self):
        return 'dungeon_skill_list'

    def _key(self):
        raise NotImplemented('not working yet')

    def _insert_columns(self):
        raise NotImplemented('not working yet')

    def _update_columns(self):
        raise NotImplemented('not working yet')


class DungeonLoader(object):
    def __init__(self, db_wrapper: db_util.DbWrapper):
        self.db_wrapper = db_wrapper

    def load_dungeon(self, dungeon_seq: int):
        dungeon = self.db_wrapper.load_single_object(Dungeon, dungeon_seq)

        if dungeon.tdt_seq:
            dungeon.resolved_dungeon_type = self.db_wrapper.load_single_object(
                DungeonType, dungeon.tdt_seq)

        if dungeon.icon_seq:
            dungeon.resolved_icon = self.db_wrapper.load_single_object(Icon, dungeon.icon_seq)

        dungeon.resolved_sub_dungeons = self.load_sub_dungeons(dungeon_seq)
        # TODO: load icon

        return dungeon

    def load_sub_dungeons(self, dungeon_seq: int):
        sub_dungeons = self.db_wrapper.load_multiple_objects(SubDungeon, dungeon_seq)
        for sd in sub_dungeons:
            tsd_seq = sd.tsd_seq
            sd.resolved_dungeon_monsters = self.load_dungeon_monster(tsd_seq)
            sd.resolved_sub_dungeon_score = self.db_wrapper.load_single_object(
                SubDungeonScore, tsd_seq)
            sd.resolved_sub_dungeon_reward = self.db_wrapper.load_single_object(
                SubDungeonReward, tsd_seq)
            sd.resolved_sub_dungeon_point = self.db_wrapper.load_single_object(
                SubDungeonPoint, tsd_seq)
        return sub_dungeons

    def load_dungeon_monster(self, tsd_seq):
        dungeon_monsters = self.db_wrapper.load_multiple_objects(DungeonMonster, tsd_seq)
        for dm in dungeon_monsters:
            dm.resolved_dungeon_monster_drops = self.db_wrapper.load_multiple_objects(
                DungeonMonsterDrop, dm.tdm_seq)
            # dm.resolved_dungeon_skills = self.db_wrapper.load_multiple_objects(DungeonMonsterDrop, tsd_seq)
        return dungeon_monsters

    def insert_or_update(self, item: SqlItem):
        key = item.key_value()
        if not item.uses_local_primary_key():
            if not self.db_wrapper.check_existing(item.exists_sql()):
                print('item (fk) needed insert:', type(item), key)
                key = self.db_wrapper.insert_item(item.insert_sql())
            elif not self.db_wrapper.check_existing(item.needs_update_sql()):
                print('item (fk) needed update:', type(item), key)
                print(item.needs_update_sql())
                self.db_wrapper.insert_item(item.update_sql())

        else:
            if item.needs_insert():
                print('item needed insert:', type(item), key)
                key = self.db_wrapper.insert_item(item.insert_sql())
            elif not self.db_wrapper.check_existing(item.needs_update_sql()):
                print('item needed update:', type(item), key)
                print(item.needs_update_sql())
                self.db_wrapper.insert_item(item.update_sql())
        return key

    def save_dungeon(self, dungeon: Dungeon):
        # TODO: Run save in a transaction and commit on success
        # TODO: Save DungeonType?
        if dungeon.resolved_dungeon_type:
            dungeon.tdt_seq = dungeon.resolved_dungeon_type.tdt_seq
        dungeon_seq = self.insert_or_update(dungeon)
        for sd in dungeon.resolved_sub_dungeons:
            sd.dungeon_seq = dungeon_seq
            self.save_sub_dungeon(sd)

    def save_sub_dungeon(self, sub_dungeon: SubDungeon):
        tsd_seq = self.insert_or_update(sub_dungeon)
        for dm in sub_dungeon.resolved_dungeon_monsters:
            dm.dungeon_seq = sub_dungeon.dungeon_seq
            dm.tsd_seq = tsd_seq
            self.save_dungeon_monster(dm)

        if sub_dungeon.resolved_sub_dungeon_score:
            sub_dungeon.resolved_sub_dungeon_score.tsd_seq = tsd_seq
            self.insert_or_update(sub_dungeon.resolved_sub_dungeon_score)

        if sub_dungeon.resolved_sub_dungeon_reward:
            sub_dungeon.resolved_sub_dungeon_reward.tsd_seq = tsd_seq
            self.insert_or_update(sub_dungeon.resolved_sub_dungeon_reward)

        if sub_dungeon.resolved_sub_dungeon_point:
            sub_dungeon.resolved_sub_dungeon_point.tsd_seq = tsd_seq
            self.insert_or_update(sub_dungeon.resolved_sub_dungeon_point)

    def save_dungeon_monster(self, dungeon_monster: DungeonMonster):
        tdm_seq = self.insert_or_update(dungeon_monster)

        for dmd in dungeon_monster.resolved_dungeon_monster_drops:
            dmd.tdm_seq = tdm_seq
            self.insert_or_update(dmd)

        for ds in dungeon_monster.resolved_dungeon_skills:
            # Currently ignoring skills
            pass
