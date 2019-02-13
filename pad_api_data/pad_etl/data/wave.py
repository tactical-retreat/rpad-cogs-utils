from ..common import pad_util


class WaveResponse(pad_util.JsonDictEncodable):
    def __init__(self, wave_data):
        """Converts the raw enemy dungeon wave response into an object."""
        self.floors = [WaveFloor(floor) for floor in wave_data]


class WaveFloor(pad_util.JsonDictEncodable):
    def __init__(self, floor_data):
        """Converts the raw stage response data into an object."""
        self.monsters = [WaveMonster(monster) for monster in floor_data]


class WaveMonster(pad_util.JsonDictEncodable):
    def __init__(self, monster_data):
        """Converts the raw spawn response data into an object."""
        self.spawn_type = monster_data[0]  # Dungeon trigger maybe? Mostly 0, last is 1
        self.monster_id = monster_data[1]
        self.monster_level = monster_data[2]
        self.drop_monster_id = monster_data[3]
        self.drop_monster_level = monster_data[4]
        self.plus_amount = monster_data[5]
