import requests
import json
from dungeon_parse import getModifiers
import csv
from io import StringIO


# link = "https://storage.googleapis.com/mirubot/paddata/processed/jp_dungeons.json"

link = "https://storage.googleapis.com/mirubot/paddata/raw/na/download_dungeon_data.json"


req = requests.get(link).text
dungeons = json.loads(req)

dungeon_json = dungeons

if dungeon_json['v'] > 6:
    print('Warning! Version of dungeon file is not tested: {}'.format(dungeon_json['v']))

dungeon_info = dungeon_json['dungeons']

dungeons = []
cur_dungeon = None

for line in dungeon_info.split('\n'):
    info = line[0:2]
    data = line[2:]
    data_values = next(csv.reader(StringIO(data), quotechar="'"))
    if info == 'd;':
        pass
    elif info == 'f;':
        possibleDrops = {}

        # This next loop runs through the elements from raw[8] until it hits a 0. The 0 indicates the end of the list
        # of drops for the floor, the following segments are the dungeon modifiers
        pos = 8

        while (int(data_values[pos]) is not 0):
            rawVal = int(data_values[pos])
            if rawVal > 10000:
                val = rawVal - 10000
                possibleDrops[val] = "rare"
                pos += 1
            else:
                possibleDrops[rawVal] = "normal"
                pos += 1
        pos += 1
        modifiers = getModifiers(data_values, pos)

        val = int(data_values[pos])

    # print("Original:", data_values)
    # print("Modifiers:", modifiers.remainingModifiers)
    # print("Message:", modifiers.messages)
    # print("Fixed team:", modifiers.fixedTeam)
    # print("Enhanced Type:", modifiers.enhancedType)
    # print("Enhanced Attribute:", modifiers.enhancedAttribute)

    elif info == 'c;':
        pass
    else:
        raise ValueError('unexpected line: ' + line)

