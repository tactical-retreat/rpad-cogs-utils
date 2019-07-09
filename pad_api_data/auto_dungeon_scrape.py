import argparse
import json
import subprocess

from pad_etl.processor import active_dungeons
from pad_etl.storage import db_util
from pad_etl.storage import timestamp_processor


def parse_args():
    parser = argparse.ArgumentParser(description="Automatically scrape dungeons.", add_help=False)

    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--server", required=True, help="na or jp")
    inputGroup.add_argument("--group", required=True, help="guerrilla group (red/blue/green)")
    inputGroup.add_argument("--user_uuid", required=True, help="Account UUID")
    inputGroup.add_argument("--user_intid", required=True, help="Account code")

    outputGroup = parser.add_argument_group("Output")
    outputGroup.add_argument("--doprod", default=False,
                             action="store_true", help="Run against prod")
    outputGroup.add_argument("--doupdates", default=False,
                             action="store_true", help="Apply updates")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")

    return parser.parse_args()


args = parse_args()


processed_dir = '/home/tactical0retreat/pad_data/processed'
bonuses_file = '{}/{}_bonuses.json'.format(processed_dir, args.server)

with open(bonuses_file) as f:
    bonuses = json.load(f)

current_dungeons = active_dungeons.filter_current_bonuses(
    bonuses, args.group, include_normals=False, include_multiplayer=True)

db_config_prod = '/home/tactical0retreat/rpad-cogs-utils/pad_api_data/db_config.json'
db_config_dev = '/home/tactical0retreat/rpad-cogs-utils/pad_api_data/db_config_dev.json'
selected_db_config = db_config_prod if args.doprod else db_config_dev

with open(selected_db_config) as f:
    db_config = json.load(f)

dry_run = not args.doupdates
db_wrapper = db_util.DbWrapper(dry_run)
db_wrapper.connect(db_config)


def do_dungeon_load(dungeon_id,
                    floor_id):
    if not args.doupdates:
        print('skipping due to dry run')
        return
    dungeon_script = '/home/tactical0retreat/rpad-cogs-utils/pad_api_data/pad_dungeon_pull.py'
    process_args = [
        'python3',
        dungeon_script,
        '--db_config={}'.format(selected_db_config),
        '--server={}'.format(args.server),
        '--dungeon_id={}'.format(dungeon_id),
        '--floor_id={}'.format(floor_id),
        '--user_uuid={}'.format(args.user_uuid),
        '--user_intid={}'.format(args.user_intid),
        '--loop_count=20',
    ]
    p = subprocess.run(process_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(str(p.stdout))
    print(str(p.stderr))


for dungeon in current_dungeons:
    dungeon_id = int(dungeon['dungeon_id'])
    print(dungeon['clean_name'], dungeon_id)

    floor_ids = active_dungeons.filter_floors(dungeon['floors'])
    for floor_id in floor_ids:
        sql = 'select count(distinct entry_id) from wave_data where dungeon_id={} and floor_id={}'.format(
            dungeon_id, floor_id)
        wave_count = db_wrapper.get_single_value(sql, op=int)
        print(wave_count, 'entries for', floor_id)
        if wave_count >= 20:
            print('skipping')
        else:
            print('entering', dungeon_id, floor_id)
            do_dungeon_load(dungeon_id, floor_id)


def do_dungeon_fill(dungeon_seq):
    if not args.doupdates:
        print('skipping due to dry run')
        return
    dungeon_script = '/home/tactical0retreat/rpad-cogs-utils/pad_api_data/load_dungeon.py'
    process_args = [
        'python3',
        dungeon_script,
        '--db_config={}'.format(selected_db_config),
        '--raw_input_dir={}'.format('/home/tactical0retreat/pad_data/raw/'),
        '--doupdates',
        '--dungeon_seq={}'.format(dungeon_seq),
    ]
    p = subprocess.run(process_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(str(p.stdout))
    print(str(p.stderr))


FIND_DUNGEONS_SQL = """
select dungeon_seq, name_us
from dungeon_list
where dungeon_seq in (
    select dungeon_seq 
    from etl_dungeon_map
    where pad_dungeon_id in (
        select dungeon_id from wave_data group by 1
    )
    group by 1
    having count(*) = 1
)
and dungeon_seq not in (
    select dungeon_seq from dungeon_monster_list group by 1
)
order by dungeon_seq desc
"""

ready_dungeons = db_wrapper.fetch_data(FIND_DUNGEONS_SQL)

for row in ready_dungeons:
    dungeon_seq = row['dungeon_seq']
    name_us = row['name_us']
    print('dungeon to load:', dungeon_seq, name_us)
    if int(dungeon_seq) in [1450]:
        print('skipping unloadable dungeon', dungeon_seq)
        continue
    do_dungeon_fill(dungeon_seq)


timestamp_processor.update_timestamps(db_wrapper)
