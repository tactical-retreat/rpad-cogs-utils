from dungeon_maps import btypeChart, battrChart


class Modifier:
    def __init__(self):
        self.required_dungeon = None
        self.remainingModifiers = []
        self.entryRequirement = ""
        self.modifiers = {}
        self.messages = []
        self.fixedTeam = {}
        self.enhancedType = ""
        self.enhancedAttribute = ""
        self.score = 0
        self.possibleDrops = {}


def splitMods(raw, pos, diff):
    return raw[pos + diff].split("|")


def getLast(raw):
    return str(raw[-1])


def getModifiers(raw):
    modifiers = Modifier()

    # This next loop runs through the elements from raw[8] until it hits a 0. The 0 indicates the end of the list
    # of drops for the floor, the following segments are the dungeon modifiers
    pos = 8

    while (int(raw[pos]) is not 0):
        rawVal = int(raw[pos])
        if rawVal > 10000:
            val = rawVal - 10000
            modifiers.possibleDrops[val] = "rare"
            pos += 1
        else:
            modifiers.possibleDrops[rawVal] = "normal"
            pos += 1
    pos += 1

    val = int(raw[pos])

    if val == 5:
        modifiers.requiredDungeon = int(raw[pos + 1])
        return modifiers

    elif val == 8:
        modifiers.score = raw[pos + 1]
        return modifiers

    elif val == 32:
        modifiers.messages.append(parse32[int(raw[pos + 1])](raw))
        # modifiers.messages.append(parse32[int(raw[pos + 2])](raw))
        return modifiers

    elif val == 33:
        modifiers.requiredDungeon = int(raw[pos + 1])
        modifiers.entryRequirement = parse32[int(raw[pos + 3])](raw)
        return modifiers

    elif val == 37:
        modifiers.requiredDungeon = int(raw[pos + 1])
        modifiers.entryRequirement = parse32[int(raw[-2])](raw)
        return modifiers

    elif val == 40:
        modifiers.entryRequirement = parse32[int(raw[pos + 2])](raw)
        return modifiers

    elif val == 64:
        mods = splitMods(raw, pos, 1)

        for m in mods:
            if 'dmsg' in m:
                modifiers.messages.append(m.split(':')[-1])
            elif 'smsg' in m:
                modifiers.messages.append(m.split(':')[-1])
            elif 'fc' in m:

                details = m.split(';')
                cardID = details[0].split(":")[-1]

                full_record = len(details) > 1

                modifiers.fixedTeam[cardID] = {
                    'monster_id': details[0],
                    'hp_plus': details[1] if full_record else 0,
                    'atk_plus': details[2] if full_record else 0,
                    'rcv_plus': details[3] if full_record else 0,
                    'awakening_count': details[4] if full_record else 0,
                    'skill_level': details[5] if full_record else 0,
                }
            elif 'btype' in m:
                splitBtype = m.split(';')
                val = int(splitBtype[0].split(':')[-1])
                try:
                    mods = splitBtype[1:]
                    modifiers.enhancedType = btypeChart[val]
                    modifiers.modifiers['hp'] = int(mods[0]) / 10000
                    modifiers.modifiers['atk'] = int(mods[1]) / 10000
                    modifiers.modifiers['rcv'] = int(mods[2]) / 10000
                except Exception as e:
                    print("Enhanced type for value", val, " not supported. Dungeon title:", raw[1], ". Error:", e)
            elif 'battr' in m:
                btype = m.split(';')
                val = int(btype[0].split(':')[-1])

                try:
                    mods = btype[1:]
                    modifiers.enhancedAttribute = battrChart[val]
                    modifiers.modifiers['hp'] = int(mods[0]) / 10000
                    modifiers.modifiers['atk'] = int(mods[1]) / 10000
                    modifiers.modifiers['rcv'] = int(mods[2]) / 10000
                except Exception as e:
                    print(e, "for value", val, "btype split data:", btype, "Dungeon:", raw[1])
            elif 'hpfix' in m:
                val = m.split(':')[-1]
                modifiers.modifiers['fixed_hp'] = int(val)
            elif 'ndf' in m:
                modifiers.messages.append("No Skyfall Combos")
            else:
                modifiers.remainingModifiers.append(m)
        return modifiers

    elif val == 65:
        modifiers.requiredDungeon = int(raw[pos + 1])
        modifiers.remainingModifiers = splitMods(raw, pos, 2)
        return modifiers

    elif val == 69:
        modifiers.requiredDungeon = int(raw[pos + 1])
        modifiers.remainingModifiers = splitMods(raw, pos, 4)
        return modifiers

    elif val == 72:
        modifiers.remainingModifiers = splitMods(raw, pos, 2)
        return modifiers
    elif val == 96:
        splitData = raw[pos + 1].split("|")
        for m in splitData:
            modifiers.remainingModifiers.append(m)
        modifiers.entryRequirement = parse32[int(raw[pos + 2])](raw)
        return modifiers
    else:
        return modifiers


def getCost(raw):
    return "Maximum cost: " + getLast(raw)


def getMaxStar(raw):
    return getLast(raw) + " stars or less"


def getAllowedType(raw):
    return type_flip[getLast(raw)] + " type only allowed"


def getReqAttr(raw):
    return "All Attributes Required"


def noDupes(raw):
    return "No Duplicate Cards"


def specialDesc(raw):
    return "Special Descended Dungeon"


def getReqExpDragon(raw):
    return getLast(raw) + " required to enter"


def getNumOrLess(raw):
    return "Teams of " + getLast(raw) + " or less allowed"

# Appears to be a special case, for a dungeon that no longer is in the game
TYPE_FLIP = {
    '5': 'Dragon'
}

# for n = 32, returns back a description of the dungeon entry requirements
ENTRY_REQUIREMENT_MAP = {
    2: getCost,
    4: getMaxStar,
    7: getAllowedType,
    9: getReqAttr,
    10: noDupes,
    11: specialDesc,
    13: getReqExpDragon,
    14: getNumOrLess
}
