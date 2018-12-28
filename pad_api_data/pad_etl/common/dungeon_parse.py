class Modifier:
    def __init__(self):
        self.requiredDungeon = 0
        self.modifiers = []
        self.entryRequirement = "None"


def splitMods(raw, pos, diff):
    return raw[pos + diff].split("|")


def getLast(raw):
    return str(raw[-1])


def getModifiers(raw, pos):
    val = int(raw[pos])

    modifiers = Modifier()

    if val == 5:
        modifiers.requiredDungeon = int(raw[pos + 1])
        return modifiers

    elif val == 32:
        modifiers.entryRequirement = parse32[int(raw[pos + 1])](raw)
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
        modifiers.modifiers = splitMods(raw, pos, 1)
        return modifiers

    elif val == 65:
        modifiers.requiredDungeon = int(raw[pos + 1])
        modifiers.modifiers = splitMods(raw, pos, 2)
        return modifiers

    elif val == 69:
        modifiers.requiredDungeon = int(raw[pos + 1])
        modifiers.modifiers = splitMods(raw, pos, 4)
        return modifiers

    elif val == 72:
        modifiers.modifiers = splitMods(raw, pos, 2)
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


type_flip = {
    '5': 'Dragon'
}

# for n = 32
parse32 = {
    2: getCost,
    4: getMaxStar,
    7: getAllowedType,
    9: getReqAttr,
    10: noDupes,
    11: specialDesc,
    13: getReqExpDragon,
    14: getNumOrLess
}
