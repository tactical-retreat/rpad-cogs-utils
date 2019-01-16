"""
Pulls data files for specified account/server.

Requires padkeygen which is not checked in.
"""
import argparse
import json
import os

from bs4 import BeautifulSoup
from pad_etl.data import bonus, extra_egg_machine

from pad_etl.api import pad_api


parser = argparse.ArgumentParser(description="Extracts PAD API data.", add_help=False)

inputGroup = parser.add_argument_group("Input")
inputGroup.add_argument("--server", required=True, help="One of [NA, JP, HT]")
inputGroup.add_argument("--user_uuid", required=True, help="Account UUID")
inputGroup.add_argument("--user_intid", required=True, help="Account code")
inputGroup.add_argument("--user_group", required=True, help="Expected user group")
inputGroup.add_argument("--only_bonus", action='store_true', help="Only populate bonus data")

outputGroup = parser.add_argument_group("Output")
outputGroup.add_argument("--output_dir", required=True,
                         help="Path to a folder where output should be saved")

helpGroup = parser.add_argument_group("Help")
helpGroup.add_argument("-h", "--help", action="help", help="Displays this help message and exits.")
args = parser.parse_args()

endpoint = None
if args.server == 'NA':
    endpoint = pad_api.ServerEndpoint.NA
elif args.server == 'JP':
    endpoint = pad_api.ServerEndpoint.JA
else:
    raise Exception('unexpected server:' + args.server)

api_client = pad_api.PadApiClient(endpoint, args.user_uuid, args.user_intid)

user_group = args.user_group.lower()
output_dir = args.output_dir
os.makedirs(output_dir, exist_ok=True)

api_client.login()


def pull_and_write_endpoint(api_client, action, file_name_suffix=''):
    action_json = api_client.action(action)

    file_name = '{}{}.json'.format(action.value.name, file_name_suffix)
    output_file = os.path.join(output_dir, file_name)
    print('writing', file_name)
    with open(output_file, 'w') as outfile:
        json.dump(action_json, outfile, sort_keys=True, indent=4)


pull_and_write_endpoint(api_client, pad_api.EndpointAction.DOWNLOAD_LIMITED_BONUS_DATA,
                        file_name_suffix='_{}'.format(user_group))

if args.only_bonus:
    print('skipping other downloads')
    exit()

pull_and_write_endpoint(api_client, pad_api.EndpointAction.DOWNLOAD_CARD_DATA)
pull_and_write_endpoint(api_client, pad_api.EndpointAction.DOWNLOAD_DUNGEON_DATA)
pull_and_write_endpoint(api_client, pad_api.EndpointAction.DOWNLOAD_SKILL_DATA)
pull_and_write_endpoint(api_client, pad_api.EndpointAction.DOWNLOAD_ENEMY_SKILL_DATA)
pull_and_write_endpoint(api_client, pad_api.EndpointAction.DOWNLOAD_MONSTER_EXCHANGE)

api_client.load_player_data()
player_data = api_client.player_data
bonus_data = bonus.load_bonus_data(data_dir=output_dir,
                                   data_group=user_group,
                                   server=args.server)

# Egg machine extraction
extra_egg_machines = extra_egg_machine.load_data(
    data_json=player_data.egg_data,
    server=args.server)

# Disabled for now; The value for gtype doesn't seem to be the 'type' value from the json.
# Maybe with more examples I can figure this out. So far I have:
# na request= gtype 62 grow 223 | data= type 52 ptp 0 pri 5 | sao
# jp request= gtype 62 grow 379 | data= type 33 ptp 0 pri 5 | ny
# jp request= gtype 52 grow 380 | data= type 54 ptp 0 pri 6 | fate
#open_egg_machines = [x for x in extra_egg_machines if x.is_open()]
open_egg_machines = []


def extract_event(machine_code, machine_name):
    m_events = [x for x in bonus_data if x.bonus_name == machine_code and x.is_open()]
    # Probably should only be one of these
    em_events = []
    for event in m_events:
        em_events.append({
            'name': machine_name,
            'comment': event.message,
            'start': event.start_time_str,
            'end': event.end_time_str,
            'row': event.egg_machine_id,
            'type': 1 if event.bonus_name == 'pem_event' else 2,
            'pri': 500 if event.bonus_name == 'pem_event' else 5,
        })

    return [extra_egg_machine.ExtraEggMachine(em, args.server) for em in em_events]


open_egg_machines.extend(extract_event('rem_event', 'Rare Egg Machine'))
open_egg_machines.extend(extract_event('pem_event', 'Pal Egg Machine'))

for em in open_egg_machines:
    grow = em.egg_machine_row
    gtype = em.egg_machine_type
    has_rate = em.name != 'Pal Egg Machine'

    page = api_client.get_egg_machine_page(gtype, grow)
    soup = BeautifulSoup(page, 'html.parser')
    rows = soup.table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 2:
            continue

        if has_rate:
            # Some rows can be size 3 (left header)
            name_chunk = cols[-2].a['href']
            rate_chunk = cols[-1].text.replace('%', '')
            rate = round(float(rate_chunk) / 100, 4)
        else:
            # Some rows can be size 2 (left header)
            name_chunk = cols[-1].a['href']
            rate = 0

        name_id = name_chunk[name_chunk.rfind('=') + 1:]
        em.contents[int(name_id)] = rate

output_file = os.path.join(output_dir, 'egg_machines.json')
with open(output_file, 'w') as outfile:
    json.dump(open_egg_machines, outfile, sort_keys=True, indent=4, default=lambda x: x.__dict__)
