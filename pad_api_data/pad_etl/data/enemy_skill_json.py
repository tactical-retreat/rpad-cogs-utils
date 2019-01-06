import json
import codecs
from typing import List, Any

FILE_NAME = 'download_enemy_skill_data_na.json'

class EnemySkill:

    def __init__(self, raw: List[Any]):
        self.enemy_skill_id = int(raw[0])
        self.name = raw[1]
        self.type = int(raw[2])
        self.flags = int(raw[3], 16)
        self.params = []
        offset = 0
        p_idx = 4
        while offset < self.flags.bit_length():
            if (self.flags >> offset) & 1 != 0:
                self.params.append(raw[p_idx])
                p_idx += 1
            else:
                self.params.append(None)
            offset += 1


def load_enemy_skill_data(enemy_skill_json_file):
    with open(enemy_skill_json_file) as f:
        enemy_skill_json = json.load(f)
    es = enemy_skill_json['enemy_skills']
    raw_arr = [['']]
    is_str = False
    for i in range(len(es)):
        if es[i] == '\'':
            is_str = not (es[i+1] == ',') if is_str else (es[i-1] == ',')
        elif not is_str and es[i] == '\n':
            raw_arr.append([''])
        elif not is_str and es[i] == ',':
            raw_arr[-1][-1] = raw_arr[-1][-1].strip('\'')
            raw_arr[-1].append('')
        if is_str or es[i].isalnum():
            raw_arr[-1][-1] += es[i]
    res = [EnemySkill(x) for x in raw_arr if len(x) > 4]
    for r in res:
        print('id:\t' + str(r.enemy_skill_id))
        print('\tname:\t' + r.name)
        print('\ttype:\t' + str(r.type))
        print('\tflags:\t' + str(r.flags))
        print('\tparams:\t' + str(r.params))

if __name__ == '__main__':
    load_enemy_skill_data(FILE_NAME)
