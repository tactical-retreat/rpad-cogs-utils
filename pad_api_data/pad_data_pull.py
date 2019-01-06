"""
Pulls data files for specified account/server.

Requires padkeygen which is not checked in.
"""
import argparse
import json
import os

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


def write_egg_machines(player_data):
    extra_egg_machines = player_data['egatya3']
    output_file = os.path.join(output_dir, 'extra_egg_machines.json')
    with open(output_file, 'w') as outfile:
        json.dump(extra_egg_machines, outfile, sort_keys=True, indent=4)


player_data = api_client.action(pad_api.EndpointAction.GET_PLAYER_DATA)
write_egg_machines(player_data)
