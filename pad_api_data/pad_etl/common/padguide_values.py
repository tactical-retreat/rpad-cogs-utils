"""
Conversions from PAD values to PadGuide strings.

Some of the PadGuide strings (e.g. awakening names) do not exactly match
the NA client names.
"""

ATTRIBUTE_MAP = {
    0: 'Fire',
    1: 'Water',
    2: 'Wood',
    3: 'Light',
    4: 'Dark',
}


TYPE_MAP = {
    -1: None,
    0: 'Evolve',
    1: 'Balanced',
    2: 'Physical',
    3: 'Healer',
    4: 'Dragon',
    5: 'God',
    6: 'Attacker',
    7: 'Devil',
    8: 'Machine',

    12: 'Awaken',

    14: 'Enhance',
    15: 'Redeemable Material',
    #? Protected?
    #? Vendor?
}

AWAKENING_MAP = {
    # 0: None,  # No need.
    1: 'Enhanced HP',
    2: 'Enhanced Attack',
    3: 'Enhanced Heal',
    4: 'Reduced Fire Damage',
    5: 'Reduced Water Damage',
    6: 'Reduced Wood Damage',
    7: 'Reduced Light Damage',
    8: 'Reduced Dark Damage',
    9: 'Auto-Recover',
    10: 'Resistance-Bind',
    11: 'Resistance-Dark',
    12: 'Resistance-Jammers',
    13: 'Resistance-Poison',
    14: 'Enhanced Fire Orbs',
    15: 'Enhanced Water Orbs',
    16: 'Enhanced Wood Orbs',
    17: 'Enhanced Light Orbs',
    18: 'Enhanced Dark Orbs',
    19: 'Extend Time',
    20: 'Recover Bind',
    21: 'Skill Boost',
    22: 'Enhanced Fire Att.',
    23: 'Enhanced Water Att.',
    24: 'Enhanced Wood Att.',
    25: 'Enhanced Light Att.',
    26: 'Enhanced Dark Att.',
    27: 'Two-Pronged Attack',
    28: 'Resistance-Skill Bind',
    29: 'Enhanced Heart Orbs',
    30: 'Multi Boost',
    31: 'Dragon Killer',
    32: 'God Killer',
    33: 'Devil Killer',
    34: 'Machine Killer',
    35: 'Balanced Killer',
    36: 'Attacker Killer',
    37: 'Physical Killer',
    38: 'Healer Killer',
    39: 'Evolve Material Killer',
    40: 'Awaken Material Killer',
    41: 'Enhance Material Killer',
    42: 'Vendor Material Killer',

    # Not sure of all these =(
    43: 'Enhanced Combo',
    44: 'Guard Break',
    45: 'Additional Attack',

    46: 'Enhanced Team HP',
    47: 'Enhanced Team Attack',
    48: 'Enhanced Team RCV',
    49: 'Super Enhanced Combo',
    50: 'Damage Void Shield Penetration',
    51: 'Awoken Assist',

    52: 'Skill Charge',
    53: 'Super Additional Attack',
    54: 'Resistance-Bind＋',
    55: 'Extend Time＋',
    56: 'Resistance-Cloud',
    57: 'Resistance-Board Restrict',
    58: 'Skill Boost＋',
    59: 'L-Shape Attack',
    60: 'L-Shape Damage Reduction',
    61: 'Enhance when HP is below 50%',
    62: 'Enhance when HP is above 80%',
}