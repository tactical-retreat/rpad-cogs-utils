"""

"""
import argparse
from datetime import datetime, timedelta
import json
import os
import time

from enum import Enum
from pad_etl.common import pad_util
from pad_etl.data import bonus, card, dungeon, skill
import pymysql


def normalize_pgserver(server: str):
    server = server.lower()
    if server == 'na':
        server = 'us'
    if server not in ('us', 'jp'):
        raise ValueError('unexpected server:', server)
    return server


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def parse_args():
    parser = argparse.ArgumentParser(description="Patches the PadGuide database.", add_help=False)
    parser.register('type', 'bool', str2bool)

    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--doupdates", default=False,
                            action="store_true", help="Enables actions")
    inputGroup.add_argument("--logsql", default=False,
                            action="store_true", help="Logs sql commands")
    inputGroup.add_argument("--db_config", required=True, help="JSON database info")
    inputGroup.add_argument("--input_dir", required=True,
                            help="Path to a folder where the input data is")

    outputGroup = parser.add_argument_group("Output")
    outputGroup.add_argument("--output_dir", required=True,
                             help="Path to a folder where output should be saved")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")
    return parser.parse_args()


def make_db_connection(db_config):
    return pymysql.connect(host=db_config['host'],
                           user=db_config['user'],
                           password=db_config['password'],
                           db=db_config['db'],
                           charset=db_config['charset'],
                           cursorclass=pymysql.cursors.DictCursor)


def load_to_key_value(connection, key_name, value_name, table_name):
    with connection.cursor() as cursor:
        sql = 'SELECT {} AS k, {} AS v FROM {}'.format(key_name, value_name, table_name)
        cursor.execute(sql)
        data = list(cursor.fetchall())
        return {row['k']: row['v'] for row in data}


def get_single_value(connection, sql, op=str):
    with connection.cursor() as cursor:
        cursor.execute(sql)
        data = list(cursor.fetchall())
        num_rows = len(data)
        if num_rows == 0:
            raise ValueError('got zero results:', sql)
        if num_rows > 1:
            raise ValueError('got too many results:', num_rows, sql)
        row = data[0]
        if len(row.values()) > 1:
            raise ValueError('too many columns in result:', sql)
        return op(list(row.values())[0])


def check_existing(connection, sql):
    if LOG_ALL_SQL:
        print(sql)
    with connection.cursor() as cursor:
        cursor.execute(sql)
        data = list(cursor.fetchall())
        num_rows = len(data)
        if num_rows > 1:
            raise ValueError('got too many results:', num_rows, sql)
        return bool(num_rows)


def insert_item(connection, sql):
    if LOG_ALL_SQL:
        print(sql)
    with connection.cursor() as cursor:
        if DRY_RUN:
            print('not inserting item due to dry run')
            return
        cursor.execute(sql)
        connection.commit()
        data = list(cursor.fetchall())
        num_rows = len(data)
        if num_rows > 0:
            raise ValueError('got too many results for insert:', num_rows, sql)


def load_event_lookups(connection):

    en_name_to_id = load_to_key_value(connection, 'event_name_us', 'event_seq', 'event_list')
    jp_name_to_id = load_to_key_value(connection, 'event_name_jp', 'event_seq', 'event_list')

    return en_name_to_id, jp_name_to_id


def load_dungeon_lookups(connection):
    en_name_to_id = load_to_key_value(connection, 'name_us', 'dungeon_seq', 'dungeon_list')
    jp_name_to_id = load_to_key_value(connection, 'name_jp', 'dungeon_seq', 'dungeon_list')

    return en_name_to_id, jp_name_to_id


class EventType(Enum):
    Week = 0
    Special = 1
    SpecialWeek = 2
    Guerrilla = 3
    GuerrillaNew = 4
    Etc = -100


class ScheduleItem(object):
    def __init__(self, merged_event, event_id: int, dungeon_id: int):
        #     def __init(self, merged_event: MergedBonus, event_id: int, dungeon_id: int):

        # New parameters
        self.open_timestamp = merged_event.start_timestamp
        self.close_timestamp = merged_event.end_timestamp

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
        self.event_enum = EventType.Guerrilla if merged_event.group else EventType.Etc
        self.event_type = str(self.event_enum.value)

        self.open_date = datetime.utcfromtimestamp(
            self.open_timestamp).replace(hour=0, minute=0, second=0)
        self.open_hour = 0
        self.open_minute = 0
        self.open_weekday = 0

        # Set during insert generation
        self.schedule_seq = None

        self.server = normalize_pgserver(merged_event.server)

        # ? Unused ?
        self.server_open_date = datetime.utcfromtimestamp(
            self.open_timestamp).replace(hour=0, minute=0, second=0)
        self.server_open_hour = 0

        group = merged_event.group
        self.team_data = None if group is None else ord(merged_event.group) - ord('a')

        if group:
            print('in here')
        self.tstamp = int(time.time())

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

        return sql.format(**object_to_sql_params(self))

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
            """.format(**object_to_sql_params(self))

        return sql


def object_to_sql_params(obj):
    d = obj.__dict__
    new_d = {}
    for k, v in d.items():
        if v is None:
            new_d[k] = 'NULL'
        elif type(v) == str:
            new_d[k] = "'{}'".format(v)
        elif type(v) in (int, float):
            new_d[k] = '{}'.format(v)
        elif type(v) == datetime:
            new_d[k] = "'{}'".format(v.isoformat())
    return new_d


def database_diff(connection, database):
    en_name_to_event_id, jp_name_to_event_id = load_event_lookups(connection)
    en_name_to_dungeon_id, jp_name_to_dungeon_id = load_dungeon_lookups(connection)

#     general_events = []
#     dungeon_events = []
#     guerilla_events = []
    schedule_events = []
    unmatched_events = []

    for merged_event in database.bonuses:
        event_id = None
        dungeon_id = None

        bonus_name = merged_event.bonus.bonus_name
        bonus_message = merged_event.bonus.clean_message
        if bonus_name in en_name_to_event_id:
            event_id = en_name_to_event_id[bonus_name]
        elif bonus_message in en_name_to_event_id:
            event_id = en_name_to_event_id[bonus_message]
        elif bonus_message in jp_name_to_event_id:
            event_id = jp_name_to_event_id[bonus_message]
        else:
            print('failed to match bonus name/message:', bonus_name, bonus_message)

        if merged_event.dungeon:
            name_mapping = {
                '-Awoken Skills Invalid': ' [Awoken Skills Invalid]',
                '-Assists Invalid': ' [Assists Invalid]',
                '-Skills Invalid': ' [Skills Invalid]',
                '-All Att. Req.': ' [All Att. Req.]',
                '-No Continues': ' [No Continues]',
                '-No Dupes': ' [No Dupes]',
                '-No RCV': ' [No RCV]',
                '-No Fire': ' [No Fire]',
                '-No Water': ' [No Water]',
                '-No Wood': ' [No Wood]',
                '-No Light': ' [No Light]',
                '-No Dark': ' [No Dark]',
                '-Special': ' [Special]',
                '-7x6 Board': ' [7x6]',
            }
            clean_name = merged_event.dungeon.clean_name
            for k, v in name_mapping.items():
                clean_name = clean_name.replace(k, v)
            dungeon_id = en_name_to_dungeon_id.get(clean_name, None)
            if dungeon_id is None:
                dungeon_id = jp_name_to_dungeon_id.get(clean_name, None)

            if dungeon_id is None:
                if merged_event.group:
                    print('failed group lookup =(')
                print('dungeon lookup failed', repr(merged_event.dungeon))

        if not dungeon_id:
            print('unmatched record')
            unmatched_events.append(merged_event)
        else:
            schedule_item = ScheduleItem(merged_event, event_id, dungeon_id)
            if not schedule_item.is_valid():
                print('skipping item', repr(merged_event), event_id, dungeon_id)
                continue
            else:
                schedule_events.append(schedule_item)

    next_id = get_single_value(
        connection, 'SELECT COALESCE(MAX(CAST(schedule_seq AS SIGNED)), 30000) FROM schedule_list', op=int)

    print('updating db starting at', next_id)

    for se in schedule_events:
        if check_existing(connection, schedule_item.exists_sql()):
            print('event already exists, skipping')
        else:
            next_id += 1
            print('inserting item')
            insert_item(connection, se.insert_sql(next_id))

#     print('matched events:', len(matched_events))
#     print('matched guerrilla:', len(matched_guerrilla))
#     print('unmatched events:', len(unmatched_events))


def load_data(args):
    input_dir = args.input_dir
    output_dir = args.output_dir

    jp_database = load_database(os.path.join(input_dir, 'jp'), 'jp')
    na_database = load_database(os.path.join(input_dir, 'na'), 'na')

    jp_database.save_all(output_dir)
    na_database.save_all(output_dir)

    with open(args.db_config) as f:
        db_config = json.load(f)

    connection = make_db_connection(db_config)

    database_diff(connection, na_database)
    database_diff(connection, jp_database)

    print('done')


def load_database(base_dir, pg_server):
    return Database(
        pg_server,
        card.load_card_data(data_dir=base_dir),
        dungeon.load_dungeon_data(data_dir=base_dir),
        {x: bonus.load_bonus_data(data_dir=base_dir, data_group=x) for x in 'abcde'},
        skill.load_skill_data(data_dir=base_dir))


class Database(object):
    def __init__(self, pg_server, cards, dungeons, bonus_sets, skills):
        self.pg_server = pg_server
        self.raw_cards = cards
        self.dungeons = dungeons
        self.bonus_sets = bonus_sets
        self.skills = skills

        self.bonuses = clean_bonuses(pg_server, bonus_sets, dungeons)
        self.cards = clean_cards(cards, skills)

    def save_all(self, output_dir: str):
        def save(file_name: str, obj: object):
            output_file = os.path.join(output_dir, '{}_{}.json'.format(self.pg_server, file_name))
            with open(output_file, 'w') as f:
                json.dump(obj, f, indent=4, sort_keys=True, default=lambda x: x.__dict__)
        save('raw_cards', self.raw_cards)
        save('dungeons', self.dungeons)
        save('skills', self.skills)
        save('bonuses', self.bonuses)
        save('cards', self.cards)


def clean_bonuses(pg_server, bonus_sets, dungeons):
    dungeons_by_id = {d.dungeon_id: d for d in dungeons}

    merged_bonuses = []
    for data_group, bonus_set in bonus_sets.items():
        for bonus in bonus_set:
            dungeon = None
            guerrilla_group = None
            if bonus.dungeon_id:
                dungeon = dungeons_by_id.get(bonus.dungeon_id, None)
                if dungeon is None:
                    print('Dungeon lookup failed for bonus', repr(bonus))
                else:
                    guerrilla_group = data_group if dungeon.dungeon_type == 'guerrilla' else None

            if guerrilla_group or data_group == 'a':
                merged_bonuses.append(MergedBonus(pg_server, bonus, dungeon, guerrilla_group))

    return merged_bonuses


def clean_cards(cards, skills):
    skills_by_id = {s.skill_id: s for s in skills}

    merged_cards = []
    for card in cards:
        active_skill = None
        leader_skill = None

        if card.active_skill_id:
            active_skill = skills_by_id.get(card.active_skill_id, None)
            if active_skill is None:
                print('Active skill lookup failed', repr(card), card.active_skill_id)

        if card.leader_skill_id:
            leader_skill = skills_by_id.get(card.leader_skill_id, None)
            if leader_skill is None:
                print('Leader skill lookup failed', repr(card), card.leader_skill_id)
            pass

        merged_cards.append(MergedCard(card, active_skill, leader_skill))
    return merged_cards


class MergedBonus(pad_util.JsonDictEncodable):
    def __init__(self, server, bonus, dungeon, group):
        self.server = server
        self.bonus = bonus
        self.dungeon = dungeon
        self.group = group

        self.start_timestamp = pad_util.gh_to_timestamp(bonus.start_time_str, server)
        self.end_timestamp = pad_util.gh_to_timestamp(bonus.end_time_str, server)

    def __repr__(self):
        return 'MergedBonus({} {} - {} - {})'.format(
            self.server, self.group, repr(self.dungeon), repr(self.bonus))


class MergedCard(pad_util.JsonDictEncodable):
    def __init__(self, card, active_skill, leader_skill):
        self.card = card
        self.active_skill = active_skill
        self.leader_skill = leader_skill


if __name__ == '__main__':
    args = parse_args()
    global LOG_ALL_SQL
    global DRY_RUN
    LOG_ALL_SQL = args.logsql
    DRY_RUN = not args.doupdates
    print('log sql:', LOG_ALL_SQL)
    print('dry_run:', DRY_RUN)
    load_data(args)
