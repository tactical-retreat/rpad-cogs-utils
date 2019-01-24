import csv
from io import StringIO
import json

# Simple dungeons
# d;1,Start Tower Pt. 1,1,0,0,0
# f;1,Basic Controls,3,103,0,0,0,0,0,0,0
# d;2,Start Tower Pt. 2,1,0,0,0
# f;1,Enemies & Eggs,3,104,0,0,0,0,1,1,1,0,0

# Multipliers
# d;501,Gaia Descended!-God Enhanced,240,1,0,0
# f;1,Creator Goddess-Master,6,128,30,1,1,0,64,btype:32;<junk>|smsg1:1.5x to stats for God Type,0,0
# f;2,Creator Goddess-Legend,6,128,50,1,1,0,64,btype:32;<junk>|smsg1:1.5x to stats for God Type,0,0

# Special floor
# d;534,$47ae64$Light Insect Dragon,1328,1,0,210001
# f;1,Honey Insect Dragon-Int,5,128,15,1,1,0,0,0,0
# f;2,Honey Insect Dragon-Expert,7,128,25,1,1,0,0,0,0
# f;3,Honey Insect Dragon-Master,7,128,40,1,1,0,0,0,0
# f;4,Honey Insect Dragon-Legend,7,128,45,1,1,0,0,0,0
# f;5,Honey Insect Dragon-Mythical,7,640,50,1,1,0,8,60000,0,0
# f;6,$cdddd7$Honey Insect Dragon-Teams of 4 or less,7,128,50,1,1,0,32,14,4


class DungeonFloor:
    def __init__(self, raw):
        self.raw = raw

        self.floor_number = int(raw[0])
        self.raw_name = raw[1]
        self.f3 = raw[2]
        self.f4 = raw[3]
        self.stamina = raw[4]
        self.f6 = raw[5]
        self.f7 = raw[6]
        self.f8 = raw[7]
        self.f9 = raw[8]
        self.f10 = raw[9]
        self.f11 = raw[10]


prefix_to_dungeontype = {
    # $47ae64$Forbidden Tower-No L. Skills
    '$47ae64$': 'green',

    # $5677a9$Alt. Castle of Satan in Abyss-No Dupes
    '$5677a9$': 'blue',

    # $00e0c6$Score Attack Dungeon dung
    '$00e0c6$': 'teal',

    # $be7fbc$Scarlet Descended!-Special +egg*
    '$be7fbc$': 'rogue',

    # $f59292$June Quest Dungeon 37
    '$f59292$': 'quest',

    # $d3423e$Ultimate Arena-No Continues exp*
    '$d3423e$': 'hard_tech',

    # #G#Ruins of the Star Vault 25
    '#G#': 'guerrilla',

    # #1#Star Treasure of the Night Sky 25
    '#1#': 'unknown-1',

    # #C#Rurouni Kenshin dung
    '#C#': 'collab',

    # $ffeb66$Satan Tournament-No Dupes annc
    '$ffeb66$': 'tournament',

    # $7dc3cd$Ultimate Hera Rush!
    '$7dc3cd$': '2p-rush',

    # $cdddd7$Aegir Descended Challenge!-7x6 Board
    # $cdddd7$Mion Descended! (Snow Globe Challenge)
    '$cdddd7$': 'descend_challenge',

    # $b86028$Poring Tower
    '$b86028$': 'defunct',
}


class Dungeon:
    def __init__(self, raw):
        self.raw = raw
        self.floors = []

        self.dungeon_id = int(raw[0])
        self.raw_name = raw[1]
        self.f3 = raw[2]
        self.f4 = raw[3]
        self.f5 = raw[4]
        self.f6 = raw[5]

        self.clean_name = self.raw_name
        self.dungeon_type = 'unknown'
        self.prefix = None
        for prefix, dungeon_type in prefix_to_dungeontype.items():
            if self.raw_name.startswith(prefix):
                self.prefix = prefix
                self.dungeon_type = dungeon_type
                self.clean_name = self.raw_name[len(prefix):]
                break

    def is_bad(self):
        return self.raw_name == '*****'

    def is_guerrilla(self):
        return self.dungeon_type == 'guerrilla'


def load_dungeons(dungeon_file):
    """Converts dungeon JSON into an array of Dungeons."""
    with open(dungeon_file) as f:
        dungeon_json = json.load(f)
    dungeon_info = dungeon_json['dungeons']

    dungeons = []
    cur_dungeon = None

    for line in dungeon_info.split('\n'):
        info = line[0:2]
        data = line[2:]
        data_values = next(csv.reader(StringIO(data), quotechar="'"))
        if info == 'd;':
            cur_dungeon = Dungeon(data_values)
            if not cur_dungeon.is_bad():
                dungeons.append(cur_dungeon)
        elif info == 'f;':
            floor = DungeonFloor(data_values)
            cur_dungeon.floors.append(floor)
        elif info == 'c;':
            pass
        else:
            print('unexpected line: ' + line)

    return dungeons

