<<<<<<< HEAD
from datetime import datetime, timedelta
import time

from enum import Enum

from . import db_util
from . import processor_util
from .merged_data import MergedBonus


class EventType(Enum):
    Week = 0
    Special = 1
    SpecialWeek = 2
    Guerrilla = 3
    GuerrillaNew = 4
    Etc = -100


class ScheduleItem(object):
    def __init__(self, merged_bonus: MergedBonus, event_id: int, dungeon_id: int):

        # New parameters
        self.open_timestamp = merged_bonus.start_timestamp
        self.close_timestamp = merged_bonus.end_timestamp

        # TODO: Fill in garbage date values for padguide app
        # TODO: Filled in close_date/open_date due to non-nullable column, but
        # using the wrong timezone
        self.close_date = datetime.utcfromtimestamp(
            self.close_timestamp).replace(hour=0, minute=0, second=0)
        self.close_hour = 0
        self.close_minute = 0
        self.close_weekday = 0

        self.dungeon_seq = str(dungeon_id)
        self.event_seq = '0' if event_id is None else str(event_id
                                                          )
        # TODO: Need to support Week
        self.event_enum = EventType.Guerrilla if merged_bonus.group else EventType.Etc
        self.event_type = str(self.event_enum.value)

        self.open_date = datetime.utcfromtimestamp(
            self.open_timestamp).replace(hour=0, minute=0, second=0)
        self.open_hour = 0
        self.open_minute = 0
        self.open_weekday = 0

        # Set during insert generation
        self.schedule_seq = None

        self.server = processor_util.normalize_pgserver(merged_bonus.server)

        # ? Unused ?
        self.server_open_date = datetime.utcfromtimestamp(
            self.open_timestamp).replace(hour=0, minute=0, second=0)
        self.server_open_hour = 0

        group = merged_bonus.group
        self.team_data = None if group is None else ord(merged_bonus.group) - ord('a')

        self.tstamp = int(time.time()) * 1000

        self.url = None

    def is_valid(self):
        # Messages and some random data errors
        is_too_long = (self.close_date - self.open_date) > timedelta(days=365)
        # Only accept guerrilla for now
        return not is_too_long and self.event_enum == EventType.Guerrilla

    def exists_sql(self):
        sql = """SELECT schedule_seq FROM schedule_list
                 WHERE open_timestamp = {open_timestamp}
                 AND close_timestamp = {close_timestamp}
                 AND server = {server}
                 AND event_seq = {event_seq}
                 AND dungeon_seq = {dungeon_seq}
                 """

        return sql.format(**db_util.object_to_sql_params(self))

    def insert_sql(self, schedule_seq):
        self.schedule_seq = schedule_seq

        sql = """
            INSERT INTO schedule_list
            (
            `open_timestamp`, `close_timestamp`,
            `close_date`, `close_hour`, `close_minute`, `close_weekday`,
            `dungeon_seq`,
            `event_seq`,
            `event_type`,
            `open_date`, `open_hour`, `open_minute`, `open_weekday`,
            `schedule_seq`,
            `server`,
            `server_open_date`, `server_open_hour`,
            `team_data`,
            `tstamp`,
            `url`)
            VALUES
            ({open_timestamp}, {close_timestamp},
            {close_date}, {close_hour}, {close_minute}, {close_weekday}, {dungeon_seq},
            {event_seq},
            {event_type},
            {open_date}, {open_hour}, {open_minute}, {open_weekday},
            {schedule_seq},
            {server},
            {server_open_date}, {server_open_hour},
            {team_data},
            {tstamp},
            {url});
            """.format(**db_util.object_to_sql_params(self))

        return sql
=======
from datetime import datetime, timedelta
import time

from enum import Enum

from . import db_util
from . import processor_util
from .merged_data import MergedBonus


class EventType(Enum):
    Week = 0
    Special = 1
    SpecialWeek = 2
    Guerrilla = 3
    GuerrillaNew = 4
    Etc = -100


class ScheduleItem(object):
    def __init__(self, merged_bonus: MergedBonus, event_id: int, dungeon_id: int):

        # New parameters
        self.open_timestamp = merged_bonus.start_timestamp
        self.close_timestamp = merged_bonus.end_timestamp

        # TODO: Fill in garbage date values for padguide app
        # TODO: Filled in close_date/open_date due to non-nullable column, but
        # using the wrong timezone
        self.close_date = datetime.utcfromtimestamp(
            self.close_timestamp).replace(hour=0, minute=0, second=0)
        self.close_hour = 0
        self.close_minute = 0
        self.close_weekday = 0

        self.dungeon_seq = str(dungeon_id)
        self.event_seq = '0' if event_id is None else str(event_id
                                                          )
        # TODO: Need to support Week
        self.event_enum = EventType.Guerrilla if merged_bonus.group else EventType.Etc
        self.event_type = str(self.event_enum.value)

        self.open_date = datetime.utcfromtimestamp(
            self.open_timestamp).replace(hour=0, minute=0, second=0)
        self.open_hour = 0
        self.open_minute = 0
        self.open_weekday = 0

        # Set during insert generation
        self.schedule_seq = None

        self.server = processor_util.normalize_pgserver(merged_bonus.server)

        # ? Unused ?
        self.server_open_date = datetime.utcfromtimestamp(
            self.open_timestamp).replace(hour=0, minute=0, second=0)
        self.server_open_hour = 0

        group = merged_bonus.group
        self.team_data = None if group is None else ord(merged_bonus.group) - ord('a')

        self.tstamp = int(time.time()) * 1000

        self.url = None

    def is_valid(self):
        # Messages and some random data errors
        is_too_long = (self.close_date - self.open_date) > timedelta(days=365)
        # Only accept guerrilla for now
        return not is_too_long and self.event_enum == EventType.Guerrilla

    def exists_sql(self):
        sql = """SELECT schedule_seq FROM schedule_list
                 WHERE open_timestamp = {open_timestamp}
                 AND close_timestamp = {close_timestamp}
                 AND server = {server}
                 AND event_seq = {event_seq}
                 AND dungeon_seq = {dungeon_seq}
                 """

        return sql.format(**db_util.object_to_sql_params(self))

    def insert_sql(self, schedule_seq):
        self.schedule_seq = schedule_seq

        sql = """
            INSERT INTO schedule_list
            (
            `open_timestamp`, `close_timestamp`,
            `close_date`, `close_hour`, `close_minute`, `close_weekday`,
            `dungeon_seq`,
            `event_seq`,
            `event_type`,
            `open_date`, `open_hour`, `open_minute`, `open_weekday`,
            `schedule_seq`,
            `server`,
            `server_open_date`, `server_open_hour`,
            `team_data`,
            `tstamp`,
            `url`)
            VALUES
            ({open_timestamp}, {close_timestamp},
            {close_date}, {close_hour}, {close_minute}, {close_weekday}, {dungeon_seq},
            {event_seq},
            {event_type},
            {open_date}, {open_hour}, {open_minute}, {open_weekday},
            {schedule_seq},
            {server},
            {server_open_date}, {server_open_hour},
            {team_data},
            {tstamp},
            {url});
            """.format(**db_util.object_to_sql_params(self))

        return sql
>>>>>>> branch 'master' of https://github.com/nachoapps/rpad-cogs-utils.git
