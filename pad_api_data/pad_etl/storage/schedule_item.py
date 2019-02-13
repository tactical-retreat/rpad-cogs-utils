from datetime import datetime, timedelta
import time

from enum import Enum
import pytz

from . import processor_util
from . import sql_item
from ..processor.merged_data import MergedBonus


# TZ used for PAD NA
NA_TZ_OBJ = pytz.timezone('America/Los_Angeles')

# TZ used for PAD JP
JP_TZ_OBJ = pytz.timezone('Asia/Tokyo')


class EventType(Enum):
    Week = 0
    Special = 1
    SpecialWeek = 2
    Guerrilla = 3
    GuerrillaNew = 4
    Etc = -100


class ScheduleItem(object):
    def __init__(self, merged_bonus: MergedBonus, event_id: int, dungeon_id: int):
        self.server = processor_util.normalize_pgserver(merged_bonus.server)

        # New parameters
        self.open_timestamp = merged_bonus.start_timestamp
        self.close_timestamp = merged_bonus.end_timestamp

        open_datetime_utc = datetime.fromtimestamp(self.open_timestamp, pytz.UTC)
        close_datetime_utc = datetime.fromtimestamp(self.close_timestamp, pytz.UTC)

        # Per padguide peculiarity, close time is inclusive, -1m from actual close
        close_datetime_utc -= timedelta(minutes=1)

        self.close_date = close_datetime_utc.date()
        self.close_hour = close_datetime_utc.strftime('%H')
        self.close_minute = close_datetime_utc.strftime('%M')
        self.close_weekday = close_datetime_utc.strftime('%w')

        self.dungeon_seq = str(dungeon_id)
        self.event_seq = '0' if event_id is None else str(event_id)

        self.event_enum = None
        if merged_bonus.is_starter:
            self.event_enum = EventType.SpecialWeek
        elif merged_bonus.group:
            self.event_enum = EventType.Guerrilla
        elif merged_bonus.bonus.bonus_name in ['Feed Skill-Up Chance', 'Feed Exp Bonus Chance']:
            self.event_enum = EventType.Etc
        else:
            self.event_enum = EventType.Special
        self.event_type = str(self.event_enum.value if self.event_enum else None)

        self.open_date = open_datetime_utc.date()
        self.open_hour = open_datetime_utc.strftime('%H')
        self.open_minute = open_datetime_utc.strftime('%M')
        self.open_weekday = open_datetime_utc.strftime('%w')

        # Set during insert generation
        self.schedule_seq = None

        # Used for maintenance or something
        server_tz = NA_TZ_OBJ if self.server == 'US' else JP_TZ_OBJ
        open_datetime_local = open_datetime_utc.replace(tzinfo=server_tz)

        self.server_open_date = open_datetime_local.replace(hour=0, minute=0, second=0).date()
        self.server_open_hour = open_datetime_local.strftime('%H')

        self.group = merged_bonus.group
        self.is_starter = merged_bonus.is_starter
        self.team_data = None

        if self.group:
            if self.is_starter:
                self.team_data = ['red', 'blue', 'green'].index(self.group)
            else:
                self.team_data = ord(self.group) - ord('a')

        # Push the tstamp forward one day into the future to try and account for the fact that
        # historically PadGuide didn't publish scheduled items this early. This is a hack to
        # fix guerrillas getting purged by the app.
        one_day_in_seconds = 1 * 24 * 60 * 60
        self.tstamp = int(time.time() + one_day_in_seconds) * 1000

        self.url = None

    def is_valid(self):
        # Messages and some random data errors
        is_too_long = (self.close_date - self.open_date) > timedelta(days=365)
        return not is_too_long and self.event_enum in (EventType.Special, EventType.Guerrilla, EventType.SpecialWeek, EventType.Etc)

    def exists_sql(self):
        sql = """SELECT schedule_seq FROM schedule_list
                 WHERE open_timestamp = {open_timestamp}
                 AND close_timestamp = {close_timestamp}
                 AND server = {server}
                 AND team_data = {team_data}
                 AND event_seq = {event_seq}
                 AND event_type = {event_type}
                 AND dungeon_seq = {dungeon_seq}
                 """

        formatted_sql = sql.format(**sql_item.object_to_sql_params(self))
        # TODO: Convert this object to use SqlItem
        fixed_sql = formatted_sql.replace('= NULL', 'is NULL')
        return fixed_sql

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
            """.format(**sql_item.object_to_sql_params(self))

        return sql

    def __repr__(self):
        return 'ScheduleItem({}/{} - {} {}->{})'.format(self.event_seq, self.dungeon_seq, self.group, self.open_date, self.close_date)
