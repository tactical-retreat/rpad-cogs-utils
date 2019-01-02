import time


# import json
# import requests
#
# link = "https://storage.googleapis.com/mirubot/paddata/processed/na_bonuses.json"
#
# json_data = requests.get(link).text
#
# bonus_dungeons = json.loads(json_data)


def get_current_bonus(bonus_dungeons) -> []:
    dungeon_list = []

    current_time = time.time()

    for bonus in bonus_dungeons:

        bonus_info = bonus['bonus']

        start_time = float(bonus['start_timestamp'])
        end_time = float(bonus['end_timestamp'])

        if start_time < current_time < end_time:
            if bonus_info['dungeon_id'] is not None and bonus_info['bonus_name'] != "score_announcement":
                bonus['is_multiplayer'] = True if bonus['dungeon']['dungeon_comment_value'] in range(600000, 700000) else False
                dungeon_list.append(bonus)

    return dungeon_list

