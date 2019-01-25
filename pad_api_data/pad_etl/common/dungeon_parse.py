from dungeon_maps import ENHANCED_TYPE_MAP, ENHANCED_ATTRIBUTE_MAP


class Modifier:
    def __init__(self):
        self.required_dungeon = None
        self.remaining_modifiers = []
        self.entry_requirement = ""
        self.modifiers = {}
        self.messages = []
        self.fixed_team = {}
        self.enhanced_type = ""
        self.enhanced_attribute = ""
        self.score = 0
        self.possible_drops = {}


def split_modifiers(raw, pos, diff):
    return raw[pos + diff].split("|")


def get_last_as_string(raw):
    return str(raw[-1])


def get_modifiers(raw):
    modifiers = Modifier()

    # This next loop runs through the elements from raw[8] until it hits a 0. The 0 indicates the end of the list
    # of drops for the floor, the following segments are the dungeon modifiers
    pos = 8

    while (int(raw[pos]) is not 0):
        raw_val = int(raw[pos])
        if raw_val > 10000:
            val = raw_val - 10000
            modifiers.possible_drops[val] = "rare"
            pos += 1
        else:
            modifiers.possible_drops[raw_val] = "normal"
            pos += 1
    pos += 1

    val = int(raw[pos])

    if val == 5:
        modifiers.required_dungeon = int(raw[pos + 1])
        return modifiers

    elif val == 8:
        modifiers.score = raw[pos + 1]
        return modifiers

    elif val == 32:
        modifiers.messages.append(ENTRY_REQUIREMENT_MAP[int(raw[pos + 1])](raw))
        return modifiers

    elif val == 33:
        modifiers.required_dungeon = int(raw[pos + 1])
        modifiers.entry_requirement = ENTRY_REQUIREMENT_MAP[int(raw[pos + 3])](raw)
        return modifiers

    elif val == 37:
        modifiers.required_dungeon = int(raw[pos + 1])
        modifiers.entry_requirement = ENTRY_REQUIREMENT_MAP[int(raw[-2])](raw)
        return modifiers

    elif val == 40:
        modifiers.entry_requirement = ENTRY_REQUIREMENT_MAP[int(raw[pos + 2])](raw)
        return modifiers

    elif val == 64:
        mods = split_modifiers(raw, pos, 1)

        for m in mods:
            if 'dmsg' in m:
                modifiers.messages.append(m.split(':')[-1])
            elif 'smsg' in m:
                modifiers.messages.append(m.split(':')[-1])
            elif 'fc' in m:

                details = m.split(';')
                card_id = details[0].split(":")[-1]

                full_record = len(details) > 1

                modifiers.fixed_team[card_id] = {
                    'monster_id': details[0],
                    'hp_plus': details[1] if full_record else 0,
                    'atk_plus': details[2] if full_record else 0,
                    'rcv_plus': details[3] if full_record else 0,
                    'awakening_count': details[4] if full_record else 0,
                    'skill_level': details[5] if full_record else 0,
                }
            elif 'btype' in m:
                split_btype = m.split(';')
                enhanced_type_raw = int(split_btype[0].split(':')[-1])
                mods = split_btype[1:]
                modifiers.enhanced_type = ENHANCED_TYPE_MAP[enhanced_type_raw]
                modifiers.modifiers['hp'] = int(mods[0]) / 10000
                modifiers.modifiers['atk'] = int(mods[1]) / 10000
                modifiers.modifiers['rcv'] = int(mods[2]) / 10000

            elif 'battr' in m:
                split_btype = m.split(';')
                val = int(split_btype[0].split(':')[-1])
                mods = split_btype[1:]
                modifiers.enhancedAttribute = ENHANCED_ATTRIBUTE_MAP[val]
                modifiers.modifiers['hp'] = int(mods[0]) / 10000
                modifiers.modifiers['atk'] = int(mods[1]) / 10000
                modifiers.modifiers['rcv'] = int(mods[2]) / 10000

            elif 'hpfix' in m:
                val = m.split(':')[-1]
                modifiers.modifiers['fixed_hp'] = int(val)
            elif 'ndf' in m:
                modifiers.messages.append("No Skyfall Combos")
            else:
                modifiers.remaining_modifiers.append(m)
        return modifiers

    elif val == 65:
        modifiers.required_dungeon = int(raw[pos + 1])
        modifiers.remaining_modifiers = split_modifiers(raw, pos, 2)
        return modifiers

    elif val == 69:
        modifiers.required_dungeon = int(raw[pos + 1])
        modifiers.remaining_modifiers = split_modifiers(raw, pos, 4)
        return modifiers

    elif val == 72:
        modifiers.remaining_modifiers = split_modifiers(raw, pos, 2)
        return modifiers
    elif val == 96:
        split_data = raw[pos + 1].split("|")
        for m in split_data:
            modifiers.remaining_modifiers.append(m)
        modifiers.entry_requirement = ENTRY_REQUIREMENT_MAP[int(raw[pos + 2])](raw)
        return modifiers

    return modifiers


def get_cost(raw):
    return "Maximum cost: " + get_last_as_string(raw)


def get_max_star(raw):
    return get_last_as_string(raw) + " stars or less"


def get_allowed_type(raw):
    return TYPE_FLIP[get_last_as_string(raw)] + " type only allowed"


def get_all_attr_req(raw):
    return "All Attributes Required"


def get_no_dupes(raw):
    return "No Duplicate Cards"


def get_special_desc(raw):
    return "Special Descended Dungeon"


def get_req_exp_dragon(raw):
    return get_last_as_string(raw) + " required to enter"


def get_n_or_less(raw):
    return "Teams of " + get_last_as_string(raw) + " or less allowed"


# Appears to be a special case, for a dungeon that no longer is in the game
TYPE_FLIP = {
    '5': 'Dragon'
}

# for n = 32, returns back a description of the dungeon entry requirements
ENTRY_REQUIREMENT_MAP = {
    2: get_cost,
    4: get_max_star,
    7: get_allowed_type,
    9: get_all_attr_req,
    10: get_no_dupes,
    11: get_special_desc,
    13: get_req_exp_dragon,
    14: get_n_or_less
}
