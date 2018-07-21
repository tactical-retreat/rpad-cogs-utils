import datetime
import json
import re
from .dungeon_types import DUNGEON_TYPE


def strip_colors(message: int) -> str:
    return re.sub(r'(?i)[$^][a-f0-9]{6}[$^]', '', message)


def ghmult(x: int) -> str:
    """Normalizes multiplier to a human-readable number."""
    mult = x / 10000
    if int(mult) == mult:
        mult = int(mult)
    return '%sx' % mult


def ghchance(x: int) -> str:
    """Normalizes percentage to a human-readable number."""
    assert x % 100 == 0
    return '%d%%' % (x // 100)


def ghtime(time_str: str, server: str) -> datetime.datetime:
    """Converts a time string into a datetime."""
    #<  151228000000
    #>  2015-12-28 00:00:00
    tz_offsets = {
        'na': '-0800',
        'jp': '+0900',
    }
    timezone_str = '{} {}'.format(time_str, tz_offsets[server.lower()])
    return datetime.datetime.strptime(timezone_str, '%y%m%d%H%M%S %z')


def gh_to_timestamp(time_str: str, server: str) -> int:
    """Converts a time string to a timestamp."""
    dt = ghtime(time_str, server)
    return int(dt.timestamp())


def internal_id_to_display_id(i_id: int) -> str:
    """Permutes internal PAD ID to the displayed form."""
    i_id = str(i_id).zfill(9)
    return ''.join(i_id[x - 1] for x in [1, 5, 9, 6, 3, 8, 2, 4, 7])


def display_id_to_group(d_id: str) -> str:
    """Converts the display ID into the group name (a,b,c,d,e)."""
    return chr(ord('a') + (int(d_id[2]) % 5))


def internal_id_to_group(i_id: str) -> str:
    """Converts the internal ID into the group name (a,b,c,d,e)."""
    return chr(ord('a') + (int(i_id) % 5))


class JsonDictEncodable(json.JSONEncoder):
    """Utility parent class that makes the child JSON encodable."""

    def default(self, o):
        return o.__dict__

# Simply returns a dungeon comment for a input raw value. Doing it this way is necessary as to not have to put all the values
# directly into a dictionary when multiple val's correspond to a single comment, but are unnecessarily delineated
def get_dungeon_type(val: int) -> str:
    if val in range(5611, 5615):
        return "Retired Special Dungeons"  # These are the last normal dungeons
    elif val in range(21612, 21618):
        return "Technical"
    elif val in range(38901, 38912):
        return "Descended (original)"
    elif val in range(200101, 200111):
        return "Alt. Technial"
    elif val in range(200021, 200057):
        return "Technical"
    elif val in range(200301, 200306) or val in range(200201, 200206):
        return "Special Decended"
    elif val in DUNGEON_TYPE:
        return DUNGEON_TYPE[val]
    else:
        return "No Data"
