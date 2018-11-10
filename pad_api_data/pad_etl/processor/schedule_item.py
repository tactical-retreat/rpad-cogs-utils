from datetime import datetime, timedelta
import time

from enum import Enum
import pytz

from . import db_util
from . import processor_util
from .merged_data import MergedBonus


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

        # TODO: Need to support Week
        self.event_enum = EventType.Etc
        if merged_bonus.group:
            self.event_enum = EventType.Guerrilla
        elif merged_bonus.starter:
            self.event_enum = EventType.SpecialWeek
        self.event_type = str(self.event_enum.value)

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
        self.starter = merged_bonus.starter
        self.team_data = None
        if self.group:
            self.team_data = ord(self.group) - ord('a')
        elif self.starter:
            self.team_data = ['RED', 'BLUE', 'GREEN'].index(self.starter)

        # Push the tstamp forward one day into the future to try and account for the fact that
        # historically PadGuide didn't publish scheduled items this early. This is a hack to
        # fix guerrillas getting purged by the app.
        one_day_in_seconds = 1 * 24 * 60 * 60
        self.tstamp = int(time.time() + one_day_in_seconds) * 1000

        self.url = None

    def is_valid(self):
        # Messages and some random data errors
        is_too_long = (self.close_date - self.open_date) > timedelta(days=365)
        # Only accept guerrilla for now
        return not is_too_long and self.event_enum in (EventType.Guerrilla, EventType.SpecialWeek)

    def exists_sql(self):
        sql = """SELECT schedule_seq FROM schedule_list
                 WHERE open_timestamp = {open_timestamp}
                 AND close_timestamp = {close_timestamp}
                 AND server = {server}
                 AND event_seq = {event_seq}
                 AND event_type = {event_type}
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

    def __repr__(self):
        return 'ScheduleItem({}/{} - {} {}->{})'.format(self.event_seq, self.dungeon_seq, self.group, self.open_date, self.close_date)
