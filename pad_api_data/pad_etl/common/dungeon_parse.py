from .dungeon_maps import ENHANCED_TYPE_MAP, ENHANCED_ATTRIBUTE_MAP, TEAM_REQUIREMENT_MAP


class Modifier:
    def __init__(self):
        self.required_dungeon = None
        self.required_floor = None
        self.remaining_modifiers = []
        self.team_stat_modifiers = {}
        self.encounter_stat_modifiers = {}
        self.messages = []
        self.fixed_team = {}
        self.enhanced_type = None
        self.enhanced_attribute = None
        self.score = None
        self.possible_drops = {}

    def __str__(self):
        return str(self.__dict__)


def split_modifiers(raw, pos, diff):
    return raw[pos + diff].split("|")


def get_last_as_string(raw):
    return str(raw[-1])


def get_stat_modifiers(mods, dungeon_modifiers):
    for m in mods:
        if m.startswith('dmsg'):
            dungeon_modifiers.messages.append(m.split(':')[-1])
        elif m.startswith('smsg'):
            dungeon_modifiers.messages.append(m.split(':')[-1])
        elif m.startswith('fc'):
            details = m.split(';')
            card_id = details[0].split(":")[-1]

            full_record = len(details) > 1

            dungeon_modifiers.fixed_team[card_id] = {
                'monster_id': details[0],
                'hp_plus': details[1] if full_record else 0,
                'atk_plus': details[2] if full_record else 0,
                'rcv_plus': details[3] if full_record else 0,
                'awakening_count': details[4] if full_record else 0,
                'skill_level': details[5] if full_record else 0,
            }
        elif m.startswith('btype'):
            split_btype = m.split(';')
            enhanced_type_raw = int(split_btype[0].split(':')[-1])
            mods = split_btype[1:]
            dungeon_modifiers.enhanced_type = ENHANCED_TYPE_MAP[enhanced_type_raw]
            dungeon_modifiers.team_stat_modifiers['hp'] = float(mods[0]) / 10000
            dungeon_modifiers.team_stat_modifiers['atk'] = float(mods[1]) / 10000
            dungeon_modifiers.team_stat_modifiers['rcv'] = float(mods[2]) / 10000

        elif m.startswith('battr'):
            split_btype = m.split(';')
            val = int(split_btype[0].split(':')[-1])
            mods = split_btype[1:]
            dungeon_modifiers.enhancedAttribute = ENHANCED_ATTRIBUTE_MAP[val]
            dungeon_modifiers.team_stat_modifiers['hp'] = float(mods[0]) / 10000
            dungeon_modifiers.team_stat_modifiers['atk'] = float(mods[1]) / 10000
            dungeon_modifiers.team_stat_modifiers['rcv'] = float(mods[2]) / 10000

        elif m.startswith('btype'):
            hp_val = m.split(':')[-1]
            dungeon_modifiers.team_stat_modifiers['fixed_hp'] = float(hp_val)
        elif m.startswith('ndf'):
            dungeon_modifiers.messages.append("No Skyfall Combos")
        elif m.startswith('hp'):
            hp_val = m.split(':')[-1]
            dungeon_modifiers.encounter_stat_modifiers['hp'] = float(hp_val) / 10000
        elif m.startswith('atk'):
            atk_val = m.split(':')[-1]
            dungeon_modifiers.encounter_stat_modifiers['atk'] = float(atk_val) / 10000
        elif m.startswith('df'):
            df_val = m.split(':')[-1]
            dungeon_modifiers.encounter_stat_modifiers['def'] = float(df_val) / 10000
        else:
            # Catch any remaining things not parsed yet, i.e. dg values
            dungeon_modifiers.remaining_modifiers.append(m)


def get_modifiers(raw):
    dungeon_modifiers = Modifier()

    # This indicates the types of things you should build your team around, i.e. No Awoken Skills, Tricolor, No RCV, etc
    team_requirement = TEAM_REQUIREMENT_MAP[int(raw[7])]
    if team_requirement is not None:
        dungeon_modifiers.messages.append(team_requirement)

    # This next loop runs through the elements from raw[8] until it hits a 0. The 0 indicates the end of the list
    # of drops for the floor, the following segments are the dungeon modifiers
    pos = 8

    while int(raw[pos]) is not 0:
        raw_val = int(raw[pos])
        if raw_val > 10000:
            val = raw_val - 10000
            dungeon_modifiers.possible_drops[val] = "rare"
            pos += 1
        else:
            dungeon_modifiers.possible_drops[raw_val] = "normal"
            pos += 1
    pos += 1

    val = int(raw[pos])

    if val == 1:
        dungeon_modifiers.required_dungeon = int(raw[pos + 1])
        dungeon_modifiers.required_floor = int(raw[pos + 2])

    elif val == 5:
        dungeon_modifiers.required_dungeon = int(raw[pos + 1])
        dungeon_modifiers.required_floor = int(raw[pos + 2])
        return dungeon_modifiers

    elif val == 8:
        dungeon_modifiers.score = int(raw[pos + 1])
        return dungeon_modifiers

    elif val == 9:
        dungeon_modifiers.score = int(raw[pos + 3])
        return dungeon_modifiers

    elif val == 32:
        dungeon_modifiers.messages.append(ENTRY_REQUIREMENT_MAP[int(raw[pos + 1])](raw))
        return dungeon_modifiers

    elif val == 33:
        dungeon_modifiers.required_dungeon = int(raw[pos + 1])
        dungeon_modifiers.required_floor = int(raw[pos + 2])
        dungeon_modifiers.messages.append(ENTRY_REQUIREMENT_MAP[int(raw[pos + 3])](raw))
        return dungeon_modifiers

    elif val == 37:
        dungeon_modifiers.required_dungeon = int(raw[pos + 1])
        dungeon_modifiers.required_floor = int(raw[pos + 2])
        dungeon_modifiers.messages.append(ENTRY_REQUIREMENT_MAP[int(raw[-2])](raw))
        return dungeon_modifiers

    elif val == 40:
        dungeon_modifiers.messages.append(ENTRY_REQUIREMENT_MAP[int(raw[pos + 2])](raw))
        return dungeon_modifiers

    elif val == 64:
        mods = split_modifiers(raw, pos, 1)
        get_stat_modifiers(mods, dungeon_modifiers)
        return dungeon_modifiers

    elif val == 65:
        dungeon_modifiers.required_dungeon = int(raw[pos + 1])
        dungeon_modifiers.required_floor = int(raw[pos + 2])

        dungeon_modifiers.remaining_modifiers = split_modifiers(raw, pos, 2)
        return dungeon_modifiers

    elif val == 69:
        dungeon_modifiers.required_dungeon = int(raw[pos + 1])
        dungeon_modifiers.required_floor = int(raw[pos + 2])
        dungeon_modifiers.remaining_modifiers = split_modifiers(raw, pos, 4)
        return dungeon_modifiers

    elif val == 72:
        dungeon_modifiers.remaining_modifiers = split_modifiers(raw, pos, 2)
        return dungeon_modifiers

    elif val == 96:
        split_data = raw[pos + 1].split("|")
        for m in split_data:
            dungeon_modifiers.remaining_modifiers.append(m)
        dungeon_modifiers.messages.append(ENTRY_REQUIREMENT_MAP[int(raw[pos + 2])](raw))
        return dungeon_modifiers

    elif val == 97:
        dungeon_modifiers.required_dungeon = int(raw[pos + 1])
        dungeon_modifiers.required_floor = int(raw[pos + 2])
        mods = split_modifiers(raw, pos, 3)
        get_stat_modifiers(mods, dungeon_modifiers)
        dungeon_modifiers.messages.append(ENTRY_REQUIREMENT_MAP[int(raw[pos + 4])](raw))
        return dungeon_modifiers

    elif val == 101:
        dungeon_modifiers.required_dungeon = int(raw[pos + 1])
        dungeon_modifiers.required_floor = int(raw[pos + 2])
        mods = split_modifiers(raw, pos, 4)
        get_stat_modifiers(mods, dungeon_modifiers)
        return dungeon_modifiers

    return dungeon_modifiers


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
