import json

import dungeon_encoding

from ..common import pad_util


def parse_wave_response(encrypted_wave_data: str):
    wave_decrypted = dungeon_encoding.decodePadDungeon(encrypted_wave_data)
    wave_data = wave_decrypted.split('=')[1]
    wave_data = wave_data.split('&')[0]
    wave_data = wave_data.replace('"w":', '')
    return WaveResponse(json.loads(wave_data))


class WaveResponse(pad_util.JsonDictEncodable):
    def __init__(self, wave_data):
        self.floors = [WaveFloor(floor) for floor in wave_data]


class WaveFloor(pad_util.JsonDictEncodable):
    def __init__(self, floor_data):
        self.monsters = [WaveMonster(monster) for monster in floor_data]


class WaveMonster(pad_util.JsonDictEncodable):
    def __init__(self, monster_data):
        self.unknown_0 = monster_data[0]  # Dungeon trigger maybe? Mostly 0, last is 1
        self.monster_id = monster_data[1]
        self.monster_level = monster_data[2]
        self.drop_monster_id = monster_data[3]
        self.drop_monster_level = monster_data[4]
        self.plus_amount = monster_data[5]
