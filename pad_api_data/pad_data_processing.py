"""
Converts the downloaded files into stuff useful for import.
"""
from collections import defaultdict
import glob
import json
import os

import argparse
from limited_bonus_data import Bonus
import limited_bonus_data
import pad_utils
import pytz

from dungeon_data import Dungeon, DungeonFloor
import dungeon_data


ET_TZ_OBJ = pytz.timezone('US/Eastern')


def gh_to_time(time_str, server):
    dt = pad_utils.ghtime(time_str, server)
    return dt.astimezone(ET_TZ_OBJ).strftime('%Y-%m-%d %H:%M')


def gh_to_timestamp(time_str, server):
    dt = pad_utils.ghtime(time_str, server)
    return int(dt.timestamp())


def dt_to_time(dt):
    return dt.astimezone(ET_TZ_OBJ).strftime('%Y-%m-%d %H:%M')


parser = argparse.ArgumentParser(description="Extracts PAD API data.", add_help=False)

inputGroup = parser.add_argument_group("Input")
inputGroup.add_argument("--server", required=True, help="One of [NA, JP, HT]")
inputGroup.add_argument("--input_dir", required=True,
                        help="Path to a folder where the input data is")

outputGroup = parser.add_argument_group("Output")
outputGroup.add_argument("--output_dir", required=True,
                         help="Path to a folder where output should be saved")

helpGroup = parser.add_argument_group("Help")
helpGroup.add_argument("-h", "--help", action="help", help="Displays this help message and exits.")
args = parser.parse_args()

server = args.server
input_dir = args.input_dir
output_dir = args.output_dir

# Shitty hack but I'm lazy and don't care
if server == 'NA':
    GROUP_TO_COLOR = {
        'A': 'R',
        'B': 'G',
        'C': 'R',
        'D': 'R',
        'E': 'B',
    }
    SELECTED_STARTER_GROUPS = ['A', 'B', 'E']
elif server == 'JP':
    GROUP_TO_COLOR = {
        'A': 'R',
        'B': 'R',
        'C': 'G',
        'D': 'B',
        'E': 'B',
    }
    SELECTED_STARTER_GROUPS = ['A', 'C', 'D']


dungeon_file = os.path.join(input_dir, 'download_dungeon_data.json')
dungeons = dungeon_data.load_dungeons(dungeon_file)
dungeon_id_to_dungeon = {d.dungeon_id: d for d in dungeons}


class DungeonBonus:
    def __init__(self, dungeon, bonus, server):
        self.dungeon = dungeon
        self.bonus = bonus
        self.group = None
        self.starter = None
        self.server = server

        self.starter_unique_string = '{}{}'.format(dungeon.clean_name, bonus.s)


guerrilla_dungeon_bonuses = []

bonus_file_glob = os.path.join(input_dir, 'download_limited_bonus_data_*.json')
for file_match in glob.glob(bonus_file_glob):
    before_group = file_match.rfind('_')
    group = file_match[before_group + 1:before_group + 2].upper()
    starter = GROUP_TO_COLOR[group]
    bonuses = limited_bonus_data.load_bonus_data(file_match)

    for item in bonuses:
        if not item.d:
            continue
        dungeon = dungeon_id_to_dungeon[item.d]
        cur_dungeon_bonus = DungeonBonus(dungeon, item, server)
        if dungeon.is_guerrilla() and item.b == 'dung':
            cur_dungeon_bonus.group = group
            cur_dungeon_bonus.starter = starter
            guerrilla_dungeon_bonuses.append(cur_dungeon_bonus)

# Figure out which guerrillas are starter based.
# A bit awkward since we only have dupes for Red mostly, and an uneven number.
starter_string_to_gdb = defaultdict(list)
for gdb in guerrilla_dungeon_bonuses:
    starter_string_to_gdb[gdb.starter_unique_string].append(gdb)

# Pick out the names for those guerrillas
starter_guerrilla_dungeon_names = set()
for gdb_list in starter_string_to_gdb.values():
    if len(gdb_list) > 1:
        starter_guerrilla_dungeon_names.add(gdb_list[0].dungeon.clean_name)

# Loop over the guerrillas checking against the names; if it's in the list
# and from the selected 'normal' group, use it. If it's not in the list,
# use it.
final_guerrillas = []
for gdb in guerrilla_dungeon_bonuses:
    if gdb.dungeon.clean_name in starter_guerrilla_dungeon_names:
        if gdb.group in SELECTED_STARTER_GROUPS:
            gdb.group = gdb.starter
            final_guerrillas.append(gdb)
    else:
        final_guerrillas.append(gdb)


output_data = []
for gdb in final_guerrillas:
    output_data.append({
        'group': gdb.group,
        'dungeon_name': gdb.dungeon.clean_name,
        'start_timestamp': gh_to_timestamp(gdb.bonus.s, server),
        'end_timestamp': gh_to_timestamp(gdb.bonus.e, server),
        'server': server,
    })

output_file = os.path.join(output_dir, 'guerrilla_data.json')
with open(output_file, 'w') as f:
    json.dump({'items': output_data}, f, sort_keys=True, indent=4)

# print('Times in ET')
# for db in guerrilla_dungeon_bonuses:
#     print('Group {}:'.format(db.group.upper()), db.dungeon.clean_name, '\n\t',
#           gh_to_time(db.bonus.s, server), '-', gh_to_time(db.bonus.e, server))
