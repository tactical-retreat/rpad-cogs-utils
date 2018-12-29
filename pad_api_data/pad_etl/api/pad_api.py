"""
Pulls data files for specified account/server.

Requires padkeygen which is not checked in.
"""
from typing import Callable
import urllib

from enum import Enum
import keygen
from padtools.servers.server import Server
import requests


class ServerEndpointInfo(object):
    def __init__(self, server: Server, keygen_fn: Callable[[str, int], str]):
        self.server = server
        self.keygen_fn = keygen_fn


class ServerEndpoint(Enum):
    NA = ServerEndpointInfo(
        Server('http://patch-na-pad.gungho.jp/base-na-adr.json'), keygen.generate_key_na)
    JA = ServerEndpointInfo(
        Server('http://dl.padsv.gungho.jp/base_adr.json'), keygen.generate_key_jp)


class EndpointActionInfo(object):
    def __init__(self, name: str, v_name: str, v_value: int):
        # Name of the action
        self.name = name

        # Name of the version parameter
        self.v_name = v_name

        # Value for the version parameter
        self.v_value = v_value


class EndpointAction(Enum):
    DOWNLOAD_CARD_DATA = EndpointActionInfo('download_card_data', 'v', 3)
    DOWNLOAD_DUNGEON_DATA = EndpointActionInfo('download_dungeon_data', 'v', 2)
    DOWNLOAD_SKILL_DATA = EndpointActionInfo('download_skill_data', 'ver', 1)
    DOWNLOAD_ENEMY_SKILL_DATA = EndpointActionInfo('download_enemy_skill_data', 'ver', 0)
    DOWNLOAD_LIMITED_BONUS_DATA = EndpointActionInfo('download_limited_bonus_data', 'v', 2)
    GET_PLAYER_DATA = EndpointActionInfo('get_player_data', 'v', 2)


def get_headers(host):
    return {
        'User-Agent': 'GunghoPuzzleAndDungeon',
        'Accept-Charset': 'utf-8',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept-Encoding': 'gzip',
        'Host': host,
        'Connection': 'Keep-Alive',
    }


class PadApiClient(object):
    def __init__(self, endpoint: ServerEndpoint, user_uuid: str, user_intid: str):
        # Server-specific key generation function
        self.keygen_fn = endpoint.value.keygen_fn

        # Server short name, na or ja
        self.server_p = endpoint.name.lower()

        # PadTools server object
        self.server = endpoint.value.server

        # Current version string
        self.server_v = self.server.version

        # Stripped version string
        self.server_r = self.server_v.replace('.', '')

        # Base URL to use for API calls
        self.server_api_endpoint = self.server.base['base']

        # Hostname for the base URL to use in the headers
        self.server_host = urllib.parse.urlparse(self.server_api_endpoint).hostname

        # Headers to use in every API call
        self.default_headers = get_headers(self.server_host)

        # The UUID of the user (with dashes) unique to each device transfer
        # 1ab232ac-1235-4789-6dfg-123456789abc
        self.user_uuid = user_uuid

        # The INT ID of the user (just numbers) static for each user
        # 123456789
        self.user_intid = user_intid

        # The result of the login attempt (must attempt to log in first)
        self.login_json = None

        # The current session ID (must be logged in first)
        self.session_id = None

# Failure
# {'res': 3}

    def login(self):
        login_payload = self.get_login_payload()
        login_url = self.build_url(login_payload)
        self.login_json = self.get_json_results(login_url)
        self.session_id = self.login_json['sid']

    def action(self, action: EndpointAction):
        payload = self.get_action_payload(action)
        url = self.build_url(payload)
        action_json = self.get_json_results(url)
        return action_json

    def get_login_payload(self):
        return [
            ('action', 'login'),
            ('t',      '1'),
            ('v',      self.server_v),
            ('u',      self.user_uuid),
            ('i',      self.user_intid),
            ('p',      self.server_p),
            ('dev',    'bullhead'),
            ('osv',    '6.0'),
            ('r',      self.server_r),
            ('m',      '0'),
        ]

    def get_action_payload(self, action: EndpointAction):
        return [
            ('action', action.value.name),
            ('pid',    self.user_intid),
            ('sid',    self.session_id),
            (action.value.v_name,   action.value.v_value),
            ('r',      self.server_r),
        ]

    def build_url(self, payload):
        combined_payload = ['{}={}'.format(x[0], x[1]) for x in payload]
        payload_str = '&'.join(combined_payload)
        key = self.keygen_fn(payload_str, n=0)
        final_payload_str = '{}&key={}'.format(payload_str, key)
        return '{}?{}'.format(self.server_api_endpoint, final_payload_str)

    def get_json_results(self, url):
        print(url)
        s = requests.Session()
        req = requests.Request('GET', url, headers=self.default_headers)
        p = req.prepare()
        r = s.send(p)
        result_json = r.json()
        response_code = result_json.get('res', 0)
        if response_code != 0:
            raise Exception('Bad server response: ' + response_code)
        return result_json
