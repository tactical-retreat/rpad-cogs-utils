"""
Parses the extra egg machine data.
"""

import json
import os
from typing import Dict, List, Any

from ..common import pad_util


# The typical JSON file name for this data.
FILE_NAME = 'extra_egg_machines.json'


class ExtraEggMachine(pad_util.JsonDictEncodable):
    """Egg machines extracted from the player data json."""

    def __init__(self, raw: Dict[str, Any]):
        self.name = str(raw['name'])
        self.clean_name = pad_util.strip_colors(self.name)

        # Start time as gungho time string
        self.start_time_str = str(raw['start'])

        # End time as gungho time string
        self.end_time_str = str(raw['end'])

        # The egg machine ID used in the API call param grow
        self.egg_machine_id = int(raw['row'])

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return 'ExtraEggMachine({} - {})'.format(self.egg_machine_id, self.clean_name)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


def load_data(data_dir: str=None, egg_json_file: str=None) -> List[ExtraEggMachine]:
    """Load ExtraEggMachine objects from the json file."""
    if egg_json_file is None:
        egg_json_file = os.path.join(data_dir, FILE_NAME)

    with open(egg_json_file) as f:
        egg_json = json.load(f)

    egg_machines = []
    for outer in egg_json:
        if outer:
            for em in outer:
                egg_machines.append(ExtraEggMachine(em))
