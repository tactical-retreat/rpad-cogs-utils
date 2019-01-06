"""
Parses the extra egg machine data.
"""

import json
import os
import time
from typing import Dict, List, Any

from ..common import pad_util


# The typical JSON file name for this data.
FILE_NAME = 'extra_egg_machines.json'


class ExtraEggMachine(pad_util.JsonDictEncodable):
    """Egg machines extracted from the player data json."""

    def __init__(self, raw: Dict[str, Any], server: str):
        self.name = str(raw['name'])
        self.server = server
        self.clean_name = pad_util.strip_colors(self.name)

        # Start time as gungho time string
        self.start_time_str = str(raw['start'])
        self.start_timestamp = pad_util.gh_to_timestamp(self.start_time_str, server)

        # End time as gungho time string
        self.end_time_str = str(raw['end'])
        self.end_timestamp = pad_util.gh_to_timestamp(self.end_time_str, server)

        # The egg machine ID used in the API call param grow
        self.egg_machine_id = int(raw['row'])

        # TODO: extra egg machine parser needs to pull out comment
        self.comment = str(raw.get('comment', ''))
        self.clean_comment = pad_util.strip_colors(self.comment)

    def is_open(self):
        current_time = int(time.time())
        return self.start_timestamp < current_time and current_time < self.end_timestamp

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return 'ExtraEggMachine({} - {})'.format(self.egg_machine_id, self.clean_name)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


def load_data(data_dir: str=None, json_file: str=None, server: str=None) -> List[ExtraEggMachine]:
    """Load ExtraEggMachine objects from the json file."""
    if json_file is None:
        json_file = os.path.join(data_dir, FILE_NAME)

    if not server:
        if '/na/' in json_file or '\\na\\' in json_file:
            server = 'na'
        elif '/jp/' in json_file or '\\jp\\' in json_file:
            server = 'jp'
        else:
            raise Exception('Server not supplied and not automatically detected from path')

    with open(json_file) as f:
        data_json = json.load(f)

    egg_machines = []
    for outer in data_json:
        if outer:
            for em in outer:
                egg_machines.append(ExtraEggMachine(em, server))

    return egg_machines
