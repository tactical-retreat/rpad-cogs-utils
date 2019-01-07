import os
import json
from typing import List, Any

from ..common import pad_util

FILE_NAME = 'download_enemy_skill_data.json'


class EnemySkill(pad_util.JsonDictEncodable):

    def __init__(self, raw: List[Any]):
        self.enemy_skill_id = int(raw[0])
        self.name = raw[1]
        self.type = int(raw[2])
        self.flags = int(raw[3], 16)  # 16bitmap for params
        self.params = [None] * 16
        offset = 0
        p_idx = 4
        while offset < self.flags.bit_length():
            if (self.flags >> offset) & 1 != 0:
                self.params[offset] = raw[p_idx]
                p_idx += 1
            offset += 1


def load_enemy_skill_data(data_dir: str=None, card_json_file: str=None) -> List[EnemySkill]:
    def check_new_str(es, i):
        return es[i] == ',' or es[i] == '\n'

    if card_json_file is None:
        card_json_file = os.path.join(data_dir, FILE_NAME)
    with open(card_json_file) as f:
        enemy_skill_json = json.load(f)
    es = enemy_skill_json['enemy_skills']
    raw_arr = [['']]
    is_str = False
    for i in range(len(es)):
        if es[i] == '\'':
            is_str = not check_new_str(es, i+1) if is_str else check_new_str(es, i-1)
        elif not is_str and es[i] == '\n':
            raw_arr.append([''])
        elif not is_str and es[i] == ',':
            raw_arr[-1][-1] = raw_arr[-1][-1].strip('\'')
            raw_arr[-1].append('')
        if is_str or es[i].isalnum():
            raw_arr[-1][-1] += es[i]
    return [EnemySkill(x) for x in raw_arr if len(x) > 3]
