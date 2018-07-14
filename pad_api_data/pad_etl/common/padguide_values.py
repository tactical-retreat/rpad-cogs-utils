from enum import Enum

"""
Conversions from PAD values to PadGuide strings.

Some of the PadGuide strings (e.g. awakening names) do not exactly match
the NA client names.
"""

TYPE_MAP = {
    -1: 0,  # Not set
    0: 7,  # Evolve
    1: 2,  # Balance
    2: 3,  # Physical
    3: 4,  # Healer
    4: 1,  # Dragon
    5: 6,  # God
    6: 5,  # Attacker
    7: 10,  # Devil
    8: 14,  # Machine
    # x: 9,  # Protected (no longer exists)
    # 10/11 don't exist
    12: 13,  # Awoken
    # 13 doesn't exist
    14: 8,  # Enhance
    15: 15,  # Vendor
}

# Might only be accurate for JP values?
AWAKENING_MAP = {
    0: '',  # No need.
    1: 'Enhanced HP',
    2: 'Enhanced Attack',
    3: 'Enhanced Heal',
    4: 'Reduce Fire Damage',
    5: 'Reduce Water Damage',
    6: 'Reduce Wood Damage',
    7: 'Reduce Light Damage',
    8: 'Reduce Dark Damage',
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
    29: 'Enhanced Heal Orbs',
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
    43: 'Enhanced Combo',
    44: 'Guard Break',
    45: 'Additional Attack',
    46: 'Enhanced Team HP',
    47: 'Enhanced Team RCV',
    48: 'Damage Void Shield Penetration',
    49: 'Awoken Assist',
    50: 'Super Additional Attack',
    51: 'Skill Charge',
    52: 'Resistance-Bind＋',
    54: 'Resistance-Cloud',
    53: 'Extend Time＋',
    55: 'Resistance-Board Restrict',
    56: 'Skill Boost＋',
    57: 'Enhance when HP is above 80%',
    58: 'Enhance when HP is below 50%',
    59: 'L-Shape Damage Reduction',
    60: 'L-Shape Attack',
    61: 'Super Enhanced Combo',
}


class EvoType(Enum):
    """Evo types supported by PadGuide. Numbers correspond to their id values."""
    Evo = 0
    UvoAwoken = 1
    UuvoReincarnated = 2
