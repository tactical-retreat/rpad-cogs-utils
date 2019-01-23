from datetime import datetime
import time

from enum import Enum

from . import db_util
from . import sql_item
from .sql_item import SimpleSqlItem


class EggMonster(SimpleSqlItem):
    TABLE = 'egg_monster_list'
    KEY_COL = 'tem_seq'
    LIST_COL = 'tet_seq'

    def __init__(self,
                 del_yn: int=0,
                 monster_no: int=None,
                 order_idx: int=None,
                 tem_seq: int=None,
                 tet_seq: int=None,
                 tstamp: int=None):
        self.del_yn = del_yn  # 1 if the row is marked deleted
        self.monster_no = monster_no  # FK to Monster (ignored)
        self.order_idx = order_idx  # Generally indexed from 10, incremented by 10
        self.tem_seq = tem_seq  # Primary key
        self.tet_seq = tet_seq  # FK to EggTitle (injected)
        self.tstamp = tstamp or (int(time.time()) * 1000)

    def uses_alternate_key_lookup(self):
        return True

    def exists_sql(self):
        return sql_item.key_and_cols_compare(
            self, cols=['tet_seq', 'order_idx'], include_key=False)
        # TODO: add unique key to enforce


class EggTitleType(Enum):
    """Type of title; controls how the row displays"""
    NAME = 0
    NAME_AND_DATE = 1


class EggTitleCategory(Enum):
    """Type of egg machine; controls which tab it shows up on

    Shorthand representation of table, egg_title_category column tec_seq.
    """
    GODFEST = 1
    RARE = 2
    PAL = 3


class EggTitle(SimpleSqlItem):
    TABLE = 'egg_title_list'
    KEY_COL = 'tet_seq'
    COL_MAPPINGS = {'type': 'title_type'}

    def __init__(self,
                 del_yn: int=0,
                 end_date: datetime=None,
                 order_idx: int=None,
                 server: str=None,
                 show_yn: int=None,
                 start_date: datetime=None,
                 tec_seq: int=None,
                 tet_seq: int=None,
                 tstamp: int=None,
                 title_type: int=None,
                 pad_machine_row: int=None,
                 pad_machine_type: int=None):
        self.del_yn = del_yn  # 1 if the row is marked delete
        self.order_idx = order_idx
        self.server = server  # US, KR, JP
        self.show_yn = show_yn
        self.tec_seq = tec_seq  # FK to egg_category_list (use EggTitleCategory.value)
        self.tet_seq = tet_seq  # Primary Key
        self.tstamp = tstamp or (int(time.time()) * 1000)

        # Start/End date should be populated if title_type == NAME_AND_DATE
        # Be sure to use UTC times!
        self.start_date = start_date
        self.end_date = end_date
        self.title_type = title_type  # Use EggTitleType.value

        # These are values I added to make looking up machines easier.
        # They shouldn't exist on legacy machines, and should always be available
        # on new machines.
        self.pad_machine_row = pad_machine_row
        self.pad_machine_type = pad_machine_type

        # There are three of these rows for every egg title.
        # They must have language set appropriately, should contain exactly 3.
        self.resolved_egg_title_names = []

        # This should only be populated if title_type = NAME
        self.resolved_egg_monsters = []

    def uses_alternate_key_lookup(self):
        return True

    def exists_sql(self):
        return sql_item.key_and_cols_compare(
            self, cols=['pad_machine_row', 'pad_machine_type', 'order_idx'], include_key=False)
        # TODO: add unique key to enforce


class EggTitleLanguage(Enum):
    """Valid values for the 'language' field in EggTitleName.

    For some reason the name is broken out into three separate rows instead of
    using a single row with three values like in other tables.
    """
    US = 1
    KR = 2
    JP = 3


class EggTitleName(SimpleSqlItem):
    TABLE = 'egg_title_name_list'
    KEY_COL = 'tetn_seq'
    LIST_COL = 'tet_seq'

    def __init__(self,
                 del_yn: int=0,
                 language: str=None,
                 name: int=None,
                 tetn_seq: int=None,
                 tet_seq: int=None,
                 tstamp: int=None):
        self.del_yn = del_yn  # 1 if the row is marked deleted
        self.language = language  # EggTitleLanguage.name
        self.name = name
        self.tetn_seq = tetn_seq  # Primary Key
        self.tet_seq = tet_seq  # FK to EggTitle (injected x3)
        self.tstamp = tstamp or (int(time.time()) * 1000)

    def exists_sql(self):
        return sql_item.key_and_cols_compare(
            self, cols=['tet_seq', 'language'], include_key=False)
        # TODO: add unique key to enforce

    def uses_alternate_key_lookup(self):
        return True


class EggLoader(object):
    def __init__(self, db_wrapper: db_util.DbWrapper):
        self.db_wrapper = db_wrapper

    def hide_outdated_machines(self):
        sql = """
            update egg_title_list 
            set show_yn = 0, tstamp = UNIX_TIMESTAMP() * 1000
            where pad_machine_row is null or pad_machine_type is null
        """
        self.db_wrapper.insert_item(sql)

        sql = """
            update egg_title_list as etl
            inner join (
                select pad_machine_row, pad_machine_type
                from egg_title_list
                where end_date < now()
                and pad_machine_row is not null
                and pad_machine_type is not null
                group by 1, 2
            ) as et_limit
            on etl.pad_machine_row = et_limit.pad_machine_row 
            and etl.pad_machine_type = et_limit.pad_machine_type
            set show_yn = 0, t
            """
        self.db_wrapper.insert_item(sql)

    def load_active_machines(self):
        sql = """
            select pad_machine_row, pad_machine_type
            from egg_title_list
            where show_yn = 1
        """
        em_pad_ids = self.db_wrapper.fetch_data(sql)
        return [self.load(em['pad_machine_row'], em['pad_machine_type']) for em in em_pad_ids]

    def load(self, pad_machine_row: int, pad_machine_type: int):
        sql = """
            select tet_seq 
            from egg_title_list 
            where pad_machine_row = {} 
            and pad_machine_type = {}
        """.format(pad_machine_row, pad_machine_type)
        em_ids = self.db_wrapper.fetch_data(sql)
        return [self.load_egg_title(data['tet_seq']) for data in em_ids]

    def load_egg_title(self, tet_seq: int):
        egg_title = self.db_wrapper.load_single_object(EggTitle, tet_seq)
        egg_title.resolved_egg_title_names = self.db_wrapper.load_multiple_objects(
            EggTitleName, tet_seq)
        egg_title.resolved_egg_monsters = self.db_wrapper.load_multiple_objects(EggMonster, tet_seq)
        return egg_title

    def save_egg_title_list(self, egg_title_list):
        # Each machine needs an absolute offset for display purposes (in case there are multiple
        # machines on a single page). Use the start day of year and machine row to compute an index
        # space for the machine.
        title = egg_title_list[0]
        day_of_year = title.start_date.timetuple().tm_yday
        row = title.pad_machine_row
        idx_offset = day_of_year * 10000 + row * 10

        for egg_title in egg_title_list:
            egg_title.order_idx += idx_offset
            tet_seq = self.db_wrapper.insert_or_update(egg_title)

            for egg_title_name in egg_title.resolved_egg_title_names:
                egg_title_name.tet_seq = tet_seq
                self.save_egg_title_name(egg_title_name)

            for egg_monster in egg_title.resolved_egg_monsters:
                egg_monster.tet_seq = tet_seq
                self.save_egg_monster(egg_monster)

    def save_egg_title_name(self, egg_title_name):
        self.db_wrapper.insert_or_update(egg_title_name)

    def save_egg_monster(self, save_egg_monster):
        self.db_wrapper.insert_or_update(save_egg_monster)
