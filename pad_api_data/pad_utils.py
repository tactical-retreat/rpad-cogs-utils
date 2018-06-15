import datetime
import pytz


def ghtime(s, server):
    #<  151228000000
    #>  2015-12-28 00:00:00
    tz_offsets = {
        'na': '-0800',
        'jp': '0900',
    }
    return datetime.datetime.strptime('{} {}'.format(s, tz_offsets[server.lower()]), '%y%m%d%H%M%S %z')


def internal_id_to_display_id(i_id):
    """Permutes internal PAD ID to the displayed form."""
    i_id = str(i_id).zfill(9)
    return ''.join(i_id[x - 1] for x in [1, 5, 9, 6, 3, 8, 2, 4, 7])


def display_id_to_group(d_id):
    return chr(ord('a') + (int(d_id[2]) % 5))


def internal_id_to_group(i_id):
    return chr(ord('a') + (int(i_id) % 5))
