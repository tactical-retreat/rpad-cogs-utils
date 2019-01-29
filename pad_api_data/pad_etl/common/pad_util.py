import datetime
import json
import re

import pytz

from .dungeon_types import DUNGEON_TYPE_COMMENTS


def strip_colors(message: int) -> str:
    return re.sub(r'(?i)[$^][a-f0-9]{6}[$^]', '', message)


def ghmult(x: int) -> str:
    """Normalizes multiplier to a human-readable number."""
    mult = x / 10000
    if int(mult) == mult:
        mult = int(mult)
    return '%sx' % mult


def ghmult_plain(x: int) -> str:
    """Normalizes multiplier to a human-readable number (without decorations)."""
    mult = x / 10000
    if int(mult) == mult:
        mult = int(mult)
    return '{}'.format(mult)


def ghchance(x: int) -> str:
    """Normalizes percentage to a human-readable number."""
    assert x % 100 == 0
    return '%d%%' % (x // 100)


def ghchance_plain(x: int) -> str:
    """Normalizes percentage to a human-readable number (without decorations)."""
    assert x % 100 == 0
    return '%d%' % (x // 100)


def ghtime(time_str: str, server: str) -> datetime.datetime:
    """Converts a time string into a datetime."""
    # <  151228000000
    # >  2015-12-28 00:00:00
    server = server.lower()
    server = 'jp' if server == 'ja' else server
    tz_offsets = {
        'na': '-0800',
        'jp': '+0900',
    }
    timezone_str = '{} {}'.format(time_str, tz_offsets[server])
    return datetime.datetime.strptime(timezone_str, '%y%m%d%H%M%S %z')


def gh_to_timestamp(time_str: str, server: str) -> int:
    """Converts a time string to a timestamp."""
    dt = ghtime(time_str, server)
    return int(dt.timestamp())


def datetime_to_gh(dt):
    # Assumes timezone is set properly
    return dt.strftime('%y%m%d%H%M%S')


class NoDstWestern(datetime.tzinfo):
    def utcoffset(self, *dt):
        return datetime.timedelta(hours=-8)

    def tzname(self, dt):
        return "NoDstWestern"

    def dst(self, dt):
        return datetime.timedelta(hours=-8)


def cur_gh_time(server):
    server = server.lower()
    server = 'jp' if server == 'ja' else server
    tz_offsets = {
        'na': NoDstWestern(),
        'jp': pytz.timezone('Asia/Tokyo'),
    }
    return datetime_to_gh(datetime.datetime.now(tz_offsets[server]))


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

    def __str__(self):
        return str(self.__dict__)


# directly into a dictionary when multiple val's correspond to a single
# comment, but are unnecessarily delineated
def get_dungeon_comment(val: int) -> str:
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
    elif val in DUNGEON_TYPE_COMMENTS:
        return DUNGEON_TYPE_COMMENTS[val]
    else:
        return "No Data"


class Multiplier:
    def __init__(self):
        self.hp = 1.0
        self.atk = 1.0
        self.rcv = 1.0
        self.shield = 0.0


def parse_skill_multiplier(skill, other_fields, length) -> Multiplier:
    multipliers = Multiplier()

    if length > 0:
        if skill == 3:
            multipliers.shield = get_last(other_fields)

        # Attack boost only
        elif skill in [11, 22, 26, 31, 40, 66, 69, 88, 90, 92, 94, 95, 96, 97, 101, 104, 109, 150]:
            multipliers.atk *= get_last(other_fields)

        # HP boost only
        elif skill in [23, 30, 48, 107]:
            multipliers.hp *= get_last(other_fields)

        elif skill in [24, 49, 149]:
            multipliers.rcv *= get_last(other_fields)

        # RCV and ATK
        elif skill in [28, 64, 75, 79, 103]:
            multipliers.atk *= get_last(other_fields)
            multipliers.rcv *= get_last(other_fields)

        # All stat boost
        elif skill in [29, 65, 76, 114]:
            multipliers.hp *= get_last(other_fields)
            multipliers.atk *= get_last(other_fields)
            multipliers.rcv *= get_last(other_fields)

        elif skill in [16, 17, 36, 38, 43]:
            multipliers.shield = get_last(other_fields)

        elif skill in [39]:
            multipliers.atk *= get_last(other_fields)
            if other_fields[2] == 2:
                multipliers.rcv *= get_last(other_fields)
        elif skill == 44:
            if other_fields[1] == 1:
                multipliers.atk *= get_last(other_fields)
            elif other_fields[1] == 2:
                multipliers.rcv *= get_last(other_fields)
            elif other_fields[1] == 3:
                multipliers.atk *= get_last(other_fields)
                multipliers.rcv *= get_last(other_fields)

        elif skill in [45, 62, 73, 77, 111]:
            multipliers.hp *= get_last(other_fields)
            multipliers.atk *= get_last(other_fields)

        elif skill == 46:
            multipliers.hp *= get_last(other_fields)

        elif skill == 50:
            if other_fields[1] == 5:
                multipliers.rcv *= get_last(other_fields)
            else:
                multipliers.atk *= get_last(other_fields)

        elif skill == 86:
            if length == 4:
                multipliers.hp *= get_last(other_fields)

        # rainbow parsing
        elif skill == 61:
            if length == 3:
                multipliers.atk *= get_last(other_fields)
            elif length == 4:
                r_type = other_fields[0]
                if r_type == 31:
                    mult = get_second_last(other_fields) + \
                           get_last(other_fields) * (5 - other_fields[1])
                    multipliers.atk *= mult
                elif r_type % 14 == 0:
                    multipliers.atk *= get_second_last(other_fields) + get_last(other_fields)
                else:
                    # r_type is 63
                    mult = get_second_last(other_fields) + \
                           (get_last(other_fields)) * (6 - other_fields[1])
                    multipliers.atk *= mult
            elif length == 5:
                if other_fields[-1] <= other_fields[1]:
                    if other_fields[0] == 31:
                        multipliers.atk *= get_third_last(other_fields) + (5 - other_fields[1]) * get_second_last(
                            other_fields)
                    if other_fields[0] == 63:
                        multipliers.atk *= get_third_last(other_fields) + (6 - other_fields[1]) * get_second_last(
                            other_fields)
                else:
                    multipliers.atk *= get_third_last(other_fields) + (
                            other_fields[-1] - other_fields[1]) * get_second_last(other_fields)

        elif skill in [63, 67]:
            multipliers.hp *= get_last(other_fields)
            multipliers.rcv *= get_last(other_fields)

        elif skill == 98:
            multipliers.atk *= get_third_last(other_fields) + (other_fields[3] - other_fields[0]) * get_second_last(
                other_fields)

        elif skill == 100:
            if other_fields[0] != 0:
                multipliers.atk *= get_last(other_fields)
            if other_fields[1] != 0:
                multipliers.rcv *= get_last(other_fields)

        elif skill == 105:
            multipliers.atk *= get_last(other_fields)
            multipliers.rcv *= get_mult(other_fields[0])

        elif skill in [106, 108]:
            multipliers.atk *= get_last(other_fields)
            multipliers.hp *= get_mult(other_fields[0])

        elif skill in [119, 159]:
            if length == 3:
                multipliers.atk *= get_last(other_fields)
            elif length == 5:
                multipliers.atk *= get_third_last(other_fields) + (
                        (other_fields[4] - other_fields[1]) * (get_second_last(other_fields)))

        elif skill == 121:
            if length == 3:
                if get_last(other_fields) != 0:
                    multipliers.hp *= get_last(other_fields)
            elif length == 4:
                multipliers.atk *= get_last(other_fields)
                if get_second_last(other_fields) != 0:
                    multipliers.hp *= get_second_last(other_fields)
            elif length == 5:
                if get_third_last(other_fields) != 0:
                    multipliers.hp *= get_third_last(other_fields)
                if get_second_last(other_fields):
                    multipliers.atk *= get_second_last(other_fields)
                if get_last(other_fields) != 0:
                    multipliers.rcv *= get_last(other_fields)

        elif skill == 122:
            if length == 4:
                multipliers.atk = get_last(other_fields)
            else:
                if get_second_last(other_fields) != 0:
                    multipliers.atk *= get_second_last(other_fields)
                if get_last(other_fields) != 0:
                    multipliers.rcv *= get_last(other_fields)

        elif skill == 123:
            if length == 4:
                multipliers.atk *= get_last(other_fields)
            elif length == 5:
                multipliers.atk *= get_second_last(other_fields)
                multipliers.rcv *= get_last(other_fields)

        elif skill == 124:
            if length == 7:
                multipliers.atk *= get_last(other_fields)
            elif length == 8:
                max_combos = 0
                for i in range(0, 5):
                    if other_fields[i] != 0:
                        max_combos += 1

                scale = get_last(other_fields)
                c_count = other_fields[5]
                multipliers.atk *= get_second_last(other_fields) + scale * (max_combos - c_count)

        elif skill == 125:
            if length == 6:
                if get_last(other_fields) != 0:
                    multipliers.hp *= get_last(other_fields)
            elif length == 7:
                multipliers.atk *= get_last(other_fields)
                if get_second_last(other_fields) != 0:
                    multipliers.hp *= get_second_last(other_fields)
            elif length == 8:
                if other_fields[-2] != 0:
                    multipliers.atk *= get_second_last(other_fields)
                if other_fields[-1] != 0:
                    multipliers.rcv *= get_last(other_fields)
                if other_fields[-3] != 0:
                    multipliers.hp *= get_third_last(other_fields)

        elif skill == 129:
            if length == 3:
                if get_last(other_fields) != 0:
                    multipliers.hp *= get_last(other_fields)
            elif length == 4:
                if get_second_last(other_fields) != 0:
                    multipliers.hp *= get_second_last(other_fields)
                multipliers.atk *= get_last(other_fields)
            elif length == 5:
                if get_third_last(other_fields) != 0:
                    multipliers.hp *= get_third_last(other_fields)
                if get_second_last(other_fields) != 0:
                    multipliers.atk *= get_second_last(other_fields)
                if get_last(other_fields) != 0:
                    multipliers.rcv *= get_last(other_fields)
            elif length == 7:
                if get_mult(other_fields[2]) != 0:
                    multipliers.hp *= get_mult(other_fields[2])
                if get_mult(other_fields[3]) != 0:
                    multipliers.atk *= get_mult(other_fields[3])
                if get_mult(other_fields[4]) != 0:
                    multipliers.rcv *= get_mult(other_fields[4])
                if get_last(other_fields) != 0:
                    multipliers.shield = get_last(other_fields)

        elif skill == 130:
            if length == 4:
                multipliers.atk *= get_last(other_fields)
            elif length == 5:
                if get_second_last(other_fields) != 0:
                    multipliers.atk *= get_second_last(other_fields)
                if get_last(other_fields) != 0:
                    multipliers.rcv *= get_last(other_fields)
            elif length == 7:
                if get_mult(other_fields[2]) != 0:
                    multipliers.hp *= get_mult(other_fields[2])
                if get_mult(other_fields[3]) != 0:
                    multipliers.atk *= get_mult(other_fields[3])
                if get_mult(other_fields[4]) != 0:
                    multipliers.rcv *= get_mult(other_fields[4])
                if get_last(other_fields) != 0:
                    multipliers.shield = get_last(other_fields)

        elif skill == 131:
            if length == 4:
                multipliers.atk *= get_last(other_fields)
            elif length == 7:
                if get_mult(other_fields[2]) != 0:
                    multipliers.hp *= get_mult(other_fields[2])
                if get_mult(other_fields[3]) != 0:
                    multipliers.atk *= get_mult(other_fields[3])
                if get_mult(other_fields[4]) != 0:
                    multipliers.rcv *= get_mult(other_fields[4])
                if get_last(other_fields) != 0:
                    multipliers.shield = get_last(other_fields)

        elif skill == 133:
            if length == 3:
                multipliers.atk *= get_last(other_fields)
            elif length == 4:
                if get_second_last(other_fields) != 0:
                    multipliers.atk *= get_second_last(other_fields)
                multipliers.rcv *= get_last(other_fields)

        elif skill == 136:
            if length == 6:
                multipliers.atk *= get_mult(other_fields[2])
                if get_last(other_fields) > 1:
                    multipliers.hp *= get_last(other_fields)
            elif length == 7:
                multipliers.atk *= get_mult(other_fields[2]) * get_last(other_fields)
            elif length == 8:
                if get_mult(other_fields[2]) > 1:
                    multipliers.atk *= get_mult(other_fields[2])
                if get_mult(other_fields[1]) > 1:
                    multipliers.hp *= get_mult(other_fields[1])
                if get_mult(other_fields[3]) > 1:
                    multipliers.rcv *= get_mult(other_fields[3])
                if get_second_last(other_fields) > 1:
                    multipliers.atk *= get_second_last(other_fields)
                if get_third_last(other_fields) > 1:
                    multipliers.hp *= get_third_last(other_fields)
                if get_last(other_fields) > 1:
                    multipliers.rcv *= get_last(other_fields)

        elif skill == 137:
            if length == 6:
                multipliers.atk *= get_mult(other_fields[2])
                multipliers.hp *= get_last(other_fields)
            elif length == 7:
                if other_fields[1] != 0:
                    multipliers.hp *= get_mult(other_fields[1])
                multipliers.atk *= get_mult(other_fields[2]) * get_last(other_fields)
                if other_fields[3] != 0:
                    multipliers.rcv *= get_mult(other_fields[3])
            elif length == 8:
                if get_mult(other_fields[1]) != 0:
                    multipliers.hp *= get_mult(other_fields[1])
                if get_mult(other_fields[2]) != 0:
                    multipliers.atk *= get_mult(other_fields[2])
                if get_mult(other_fields[3]) != 0:
                    multipliers.rcv *= get_mult(other_fields[3])
                if get_third_last(other_fields) != 0:
                    multipliers.hp *= get_third_last(other_fields)
                if get_second_last(other_fields) != 0:
                    multipliers.atk *= get_second_last(other_fields)
                if get_last(other_fields) != 0:
                    multipliers.rcv *= get_last(other_fields)

        elif skill == 139:
            if length == 5:
                multipliers.atk *= get_last(other_fields)
            if length == 7 or length == 8:
                multipliers.atk *= max(get_mult(other_fields[4]), get_last(other_fields))

        elif skill == 151:
            if other_fields[0] != 0:
                multipliers.atk *= get_mult(other_fields[0])
            multipliers.shield = get_last(other_fields)

        elif skill == 155:
            if length == 4:
                if get_second_last(other_fields) != 0:
                    multipliers.hp *= get_second_last(other_fields)
                multipliers.atk *= get_last(other_fields)
            elif length == 5:
                if get_third_last(other_fields) != 0:
                    multipliers.hp *= get_third_last(other_fields)
                if get_second_last(other_fields) != 0:
                    multipliers.atk *= get_second_last(other_fields)
                if get_last(other_fields) != 0:
                    multipliers.rcv *= get_last(other_fields)

        elif skill == 156:
            check = other_fields[-2]
            if check == 2:
                multipliers.atk *= get_last(other_fields)
            if check == 3:
                multipliers.shield = get_last(other_fields)

        elif skill == 157:
            if length == 2:
                multipliers.atk *= get_last(other_fields) ** 2
            if length == 4:
                multipliers.atk *= get_last(other_fields) ** 3
            if length == 6:
                multipliers.atk *= get_last(other_fields) ** 3

        elif skill == 158:
            if length == 4:
                multipliers.atk *= get_last(other_fields)
            elif length == 5:
                if get_second_last(other_fields) != 0:
                    multipliers.hp *= get_second_last(other_fields)
                if get_last(other_fields) != 0:
                    multipliers.atk *= get_last(other_fields)
            elif length == 6:
                if get_third_last(other_fields) != 0:
                    multipliers.rcv *= get_third_last(other_fields)
                if get_second_last(other_fields) != 0:
                    multipliers.hp *= get_second_last(other_fields)
                if get_last(other_fields) != 0:
                    multipliers.atk *= get_last(other_fields)

        elif skill == 163:
            if length == 4:
                if get_second_last(other_fields) != 0:
                    multipliers.hp *= get_second_last(other_fields)
                multipliers.atk *= get_last(other_fields)
            if length == 5:
                if get_third_last(other_fields) != 0:
                    multipliers.hp *= get_third_last(other_fields)
                if get_second_last(other_fields) != 0:
                    multipliers.atk *= get_second_last(other_fields)
                if get_last(other_fields) != 0:
                    multipliers.rcv *= get_last(other_fields)
            if length == 6 or length == 7:
                multipliers.shield = get_last(other_fields)

        elif skill == 164:
            if length == 7:
                multipliers.atk *= get_second_last(other_fields)
                multipliers.rcv *= get_last(other_fields)
            if length == 8:
                multipliers.atk *= get_third_last(other_fields)
                multipliers.rcv *= get_second_last(other_fields)
                if other_fields[4] == 1:
                    multipliers.atk += get_last(other_fields)
                    multipliers.rcv += get_last(other_fields)
                elif other_fields[4] == 2:
                    multipliers.atk += get_last(other_fields)

        elif skill == 165:
            if length == 4:
                multipliers.atk *= get_second_last(other_fields)
                multipliers.rcv *= get_last(other_fields)
            if length == 7:
                multipliers.atk *= get_mult(other_fields[2]) + \
                                   get_third_last(other_fields) * other_fields[-1]
                multipliers.rcv *= get_mult(other_fields[3]) + \
                                   get_second_last(other_fields) * other_fields[-1]

        elif skill == 166:
            multipliers.atk *= get_mult(other_fields[1]) + (other_fields[-1] - other_fields[0]) * get_third_last(
                other_fields)
            multipliers.rcv *= get_mult(other_fields[2]) + (other_fields[-1] - other_fields[0]) * get_second_last(
                other_fields)

        elif skill == 167:
            if length == 4:
                multipliers.atk *= get_second_last(other_fields)
                multipliers.rcv *= get_last(other_fields)
            elif length == 7:
                diff = other_fields[-1] - other_fields[1]
                multipliers.atk *= get_mult(other_fields[2]) + diff * get_third_last(other_fields)
                multipliers.rcv *= get_mult(other_fields[3]) + diff * get_second_last(other_fields)

        elif skill in [169, 170, 171, 182]:
            if get_second_last(other_fields) > 1:
                multipliers.atk *= get_second_last(other_fields)
            multipliers.shield = get_last(other_fields)

        elif skill == 175:
            if length == 5:
                if get_second_last(other_fields) != 0:
                    multipliers.hp *= get_second_last(other_fields)
                multipliers.atk *= get_last(other_fields)
            if length == 6:
                if get_third_last(other_fields) != 0:
                    multipliers.hp *= get_third_last(other_fields)
                if get_second_last(other_fields) != 0:
                    multipliers.atk *= get_second_last(other_fields)
                if get_last(other_fields) != 0:
                    multipliers.rcv *= get_last(other_fields)

        elif skill == 177:
            if length == 7:
                multipliers.atk *= get_last(other_fields)
            elif length == 8:
                multipliers.atk *= get_second_last(other_fields) + \
                                   other_fields[-3] * get_last(other_fields)

        elif skill in [178, 185]:
            if length == 4:
                multipliers.hp *= get_last(other_fields)
            elif length == 5:
                if get_second_last(other_fields) != 0:
                    multipliers.hp *= get_second_last(other_fields)
                multipliers.atk *= get_last(other_fields)
            elif length == 6:
                if get_third_last(other_fields) != 0:
                    multipliers.hp *= get_third_last(other_fields)
                if get_second_last(other_fields) != 0:
                    multipliers.atk *= get_second_last(other_fields)
                if get_last(other_fields) != 0:
                    multipliers.rcv *= get_last(other_fields)

        elif skill == 183:
            if length == 4 or length == 7:
                multipliers.atk *= get_last(other_fields)
            elif length == 5:
                if get_second_last(other_fields) != 0:
                    multipliers.atk *= get_second_last(other_fields)
                multipliers.shield = get_last(other_fields)
            elif length == 8:
                multipliers.atk *= max(get_mult(other_fields[3]), get_second_last(other_fields))
                multipliers.rcv *= max(get_mult(other_fields[4]), get_last(other_fields))

        elif skill == 186:
            if length == 4:
                if get_second_last(other_fields) != 0:
                    multipliers.hp *= get_second_last(other_fields)
                if get_last(other_fields) != 0:
                    multipliers.atk *= get_last(other_fields)
            elif length == 5:
                if get_third_last(other_fields) != 0:
                    multipliers.hp *= get_third_last(other_fields)
                if get_second_last(other_fields) != 0:
                    multipliers.atk *= get_second_last(other_fields)
                if get_last(other_fields) != 0:
                    multipliers.rcv *= get_last(other_fields)

    return multipliers


def get_mult(val):
    return val / 100


def get_last(other_fields):
    if len(other_fields) != 0:
        return other_fields[-1] / 100
    else:
        return 1


def get_second_last(other_fields):
    if len(other_fields) != 0:
        return other_fields[-2] / 100
    else:
        return 1


def get_third_last(other_fields):
    if len(other_fields) != 0:
        return other_fields[-3] / 100
    else:
        return 1
