"""
Pulls data files for specified account/server.

Requires padkeygen which is not checked in.
"""
import argparse
import json
import os
import sys
import urllib

from padtools.servers.server import Server
import requests

import padkeygen


parser = argparse.ArgumentParser(description="Extracts PAD API data.", add_help=False)

inputGroup = parser.add_argument_group("Input")
inputGroup.add_argument("--server", required=True, help="One of [NA, JP, HT]")
inputGroup.add_argument("--user_uuid", required=True, help="Account UUID")
inputGroup.add_argument("--user_intid", required=True, help="Account code")

outputGroup = parser.add_argument_group("Output")
outputGroup.add_argument("--output_dir", required=True,
                         help="Path to a folder where output should be saved")

helpGroup = parser.add_argument_group("Help")
helpGroup.add_argument("-h", "--help", action="help", help="Displays this help message and exits.")
args = parser.parse_args()


# All my endpoint data is for the android stuff, padtools picks ios by default.
# Load the data from the json for the android endpoints.
SERVERS = {
    'JP': Server('http://patch-pad.gungho.jp/base_adr.json'),
    'NA': Server('http://patch-na-pad.gungho.jp/base-na-adr.json'),
    'HT': Server('http://dl.padsv.gungho.jp/base.ht-adr.json'),
}


def get_headers(host):
    headers = {
        'User-Agent': 'GunghoPuzzleAndDungeon',
        'Accept-Charset': 'utf-8',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept-Encoding': 'gzip',
        'Host': host,
        'Connection': 'Keep-Alive',
    }
    return headers


# u / i are required per-player info
# p is the server in lowercase (jp/ht/na)
# v/r are the version info
def get_login_payload(u, i, p, v, r):
    payload = [
        ('action', 'login'),
        ('t',      '1'),
        ('v',      v),
        ('u',      u),
        ('i',      i),
        ('p',      p),
        ('dev',    'bullhead'),
        ('osv',    '6.0'),
        ('r',      r),
        ('m',      '0'),
    ]
    return payload


server_name = args.server
server = SERVERS[server_name]
server_p = server_name.lower()
server_v = server.version
server_r = server_v.replace('.', '')

server_api_endpoint = server.base['base']
server_host = urllib.parse.urlparse(server_api_endpoint).hostname

user_u = args.user_uuid
user_i = args.user_intid

output_dir = args.output_dir
os.makedirs(output_dir, exist_ok=True)

headers = get_headers(server_host)


def build_url(url, payload):
    combined_payload = ['{}={}'.format(x[0], x[1]) for x in payload]
    payload_str = '&'.join(combined_payload)
    key = padkeygen.generate_key(payload_str)
    final_payload_str = '{}&key={}'.format(payload_str, key)

    return '{}?{}'.format(url, final_payload_str)


def get_json_results(url, headers):
    s = requests.Session()
    req = requests.Request('GET', url, headers=headers)
    p = req.prepare()
    r = s.send(p)
    return r.json()


login_payload = get_login_payload(user_u, user_i, server_p, server_v, server_r)
login_url = build_url(server_api_endpoint, login_payload)
login_json = get_json_results(login_url, headers)

user_sid = login_json['sid']


def get_action_payload(action, pid, sid, v_name, v_value, r):
    payload = [
        ('action', action),
        ('pid',    pid),
        ('sid',    sid),
        (v_name,   v_value),
        ('r',      r),
    ]
    return payload


def pull_and_write_endpoint(action, pid, sid, v_name, v_value, r):
    payload = get_action_payload(action, pid, sid, v_name, v_value, r)
    url = build_url(server_api_endpoint, payload)
    print('querying', url)
    action_json = get_json_results(url, headers)
    print('got ', action_json)

    output_file = os.path.join(output_dir, '{}.json'.format(action))
    with open(output_file, 'w') as outfile:
        json.dump(action_json, outfile, sort_keys=True, indent=4)


pull_and_write_endpoint('download_card_data', user_i, user_sid, 'v', '3', server_r)
pull_and_write_endpoint('download_dungeon_data', user_i, user_sid, 'v', '2', server_r)
pull_and_write_endpoint('download_skill_data', user_i, user_sid, 'ver', '1', server_r)
pull_and_write_endpoint('download_limited_bonus_data', user_i, user_sid, 'v', '2', server_r)
pull_and_write_endpoint('download_enemy_skill_data', user_i, user_sid, 'ver', '0', server_r)
