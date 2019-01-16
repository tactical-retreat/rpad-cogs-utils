from collections import defaultdict
from datetime import datetime

import pytz

from . import egg


def normalize_server(text):
    text = text.lower().strip()
    return 'US' if text in ['us', 'na'] else 'JP'


def extract_egg_category(name):
    category = egg.EggTitleCategory.GODFEST
    if 'rare egg machine' == name.lower():
        category = egg.EggTitleCategory.RARE
    elif 'pal egg machine' == name.lower():
        category = egg.EggTitleCategory.PAL
    return category.value


def create_egg_title_name(name: str, language: egg.EggTitleLanguage):
    return egg.EggTitleName(
        language=language.name,
        name=name)


def create_all_egg_title_names(name: str):
    return [
        create_egg_title_name(name, egg.EggTitleLanguage.JP),
        create_egg_title_name(name, egg.EggTitleLanguage.KR),
        create_egg_title_name(name, egg.EggTitleLanguage.US),
    ]


def create_egg_title(egg_json, title_type: egg.EggTitleType, title_value: str):
    et = egg.EggTitle()
    et.order_idx = 0
    et.server = normalize_server(egg_json['server'])
    et.show_yn = 1
    et.tec_seq = extract_egg_category(egg_json['clean_name'])

    if title_type == egg.EggTitleType.NAME_AND_DATE:
        et.end_date = datetime.fromtimestamp(egg_json['end_timestamp'], tz=pytz.utc)
        et.start_date = datetime.fromtimestamp(egg_json['start_timestamp'], tz=pytz.utc)
    et.title_type = title_type.value

    et.pad_machine_row = egg_json['egg_machine_row']
    et.pad_machine_type = egg_json['egg_machine_type']

    et.resolved_egg_title_names = create_all_egg_title_names(title_value)

    return et


def fmt_pct(num):
    return '{:.1%}'.format(num).rstrip('0%.') + '%'


class EggProcessor(object):
    def __init__(self):
        pass

    def convert_from_json(self, egg_json):
        results = []
        results.append(create_egg_title(
            egg_json, egg.EggTitleType.NAME_AND_DATE, egg_json['clean_comment']))

        rate_to_monsters = defaultdict(set)
        for monster_id, rate in egg_json['contents'].items():
            rate_to_monsters[fmt_pct(rate)].add(monster_id)

        for row_idx, rate in enumerate(sorted(rate_to_monsters.keys()), 1):
            rate_row = create_egg_title(egg_json, egg.EggTitleType.NAME, rate)
            rate_row.order_idx = row_idx
            for monster_idx, monster_id in enumerate(sorted(rate_to_monsters[rate])):
                rate_row.resolved_egg_monsters.append(
                    egg.EggMonster(monster_no=int(monster_id), order_idx=monster_idx))

            results.append(rate_row)

        return results
