

# This is a map for the Floor raw[7] item, which indicates the board modifier
# Value for 768 is currently blank as there are no obvious indications as to what it is referring to
TEAM_REQUIREMENT_MAP = {
    0: None,
    1: 'No Fire',
    2: 'No Water',
    3: 'Wood/Light/Dark only',
    4: 'No Wood',
    5: 'Water/Light/Dark only',
    6: 'Fire/Light/Dark only',
    8: 'No Light',
    9: 'Water/Wood/Dark only',
    10: 'Fire/Wood/Dark only',
    12: 'Fire/Water/Dark only',
    16: 'No Dark',
    17: 'Water/Wood/Light only',
    18: 'Fire/Wood/Light only',
    20: 'Fire/Water/Light only',
    24: 'Tricolor',
    32: 'No RCV',
    64: 'Skills Invalid',
    128: 'Leader Skill Invalid',
    256: 'No Continues',
    259: 'Wood/Light/Dark only',
    261: 'Water/Light/Dark only',
    274: 'Fire/Wood/Light only',
    276: 'No Wood/Dark',
    280: 'Tricolor',
    288: 'No RCV',
    768: None,
    800: 'No RCV',
    1024: 'Awoken Skills Invalid',
    1056: 'No RCV, Awoken Skills Invalid',
    1280: 'Awoken Skills Invalid',
    1312: 'No RCV, Awoken Skills Invalid',
    1792: 'Awoken Skills Invalid',
    2048: 'Assists Invalid'
}


# This map takes in an int, indicated by the btype parameter in the dungeon modifiers, and returns
# the type of monster that gets a stat boost i.e. 1.5x stats for dragon type would be btype:16
ENHANCED_TYPE_MAP = {
    2: 'Balanced',
    4: 'Physical',
    8: 'Healer',
    12: 'Physical & Healer',
    16: 'Dragon',
    20: 'Physical & Dragon Enhanced',
    32: 'God',
    34: 'Balanced & God',
    40: 'Healer & God',
    64: 'Attacker',
    68: 'Physical & Attacker',
    128: 'Devil',
    132: 'Physical & Devil',
    192: 'Attacker & Devil Enhanced',
    256: 'Machine Enhanced',
    320: 'Attacker & Machine'
}

# This map takes in an int, indiciated by the battr parameter, and returns the attribute
# that receives a stat bonus, i.e. 1.5x stats for Light type would be battr:8
ENHANCED_ATTRIBUTE_MAP = {
    1: 'Fire',
    2: 'Water',
    4: 'Wood',
    8: 'Light',
    16: 'Dark',

}
