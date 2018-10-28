

SKILL_TYPE = {
    0: 'ATTR Mass Attack',
    1: 'Multi Target Nuke',     # Hits multiple enemies
    2: 'Single Target Nuke',  # 50x, 200x, etc atk on an enemy
    3: 'Damage Reduction/Shield',    # Self explanatory but for ACTIVE SKILLS
    4: 'Poison Enemies',    # Poisons all enemeies
    5: 'Free Orb Movement',     # Think Myr
    6: 'Gravity',   # Reduce by some %
    7: 'HP Recover (RCV)',  # Recover based on RCV
    8: 'HP Recover (Static)',    # Recover a static amount
    9: '1 ATTR to 1 ATTR',  # One attr to another
    10: 'Orb Refresh',      # Replace all orbs
    11: 'ATTR ATK Boost',   # Boosts attr atk
    12: 'Bonus Attack',     # AKA poor mans FUA (Vajra's, Hino, etc)
    13: 'Autoheal',     # Self explanatory, thing Amaterasu, Odin
    14: 'Resolve',      # may survive when hit from full
    15: 'Movement Time Increase',   # Increases orb movement time
    16: 'Damage Reduction/Shield',    # Reduces damage i.e. shield but for LEADER SKILLS
    17: 'Reduce ATTR damage',    # i.e. Halves fire damage
    18: 'Delay',
    19: 'Defense Break',    # Void/ Half Defense for x turns
    20: '2 ATTR to 1,2 ATTR',   # Changes two attributes to one or two attributes
    21: 'Damage Void',
    22: 'Type ATK Boost',    # Boosts ATK based on type
    23: 'Type HP Boost',    # Boosts HP based on TYPE
    24: 'Type RCV Boost',    # Boosts ONLY RCV depending on type (God, Dragon, etc)
    26: 'Static ATK Boost',    # Boosts ONLY ATK for ALL cards
    28: 'ATK and RCV Boost',    # Boosts ATK and RCV by a multiplier
    29: 'All Stat Boost',   # can be something like 1.5x all stats, all stats increase a little, etc
    30: 'Dragon/God HP Boost',
    31: 'Dragon/God ATK Boost',
    33: 'Taiko Drum',   # Princess Soprano best waifu
    34: 'Nuke and Heal',    # Nukes and recovers a bit of health
    35: 'ATK Based Nuke',
    36: 'Two ATTR Damage Reduction',
    37: 'Single Target, Team ATTR Nuke',  # i.e. 30x DARK Damage nuke, etc
    38: 'Low HP Shield',     # Vastly reduce dmg under 50% health
    39: 'Low HP, ATK Boost',
    40: '2 ATTR ATK Boost',
    41: 'Counterattack',
    42: 'ATTR on ATTR Nuke',    # 35x fire nuke on WOOD enemies, type of thing
    43: 'Full HP Shield',
    44: 'High HP, ATK Boost',   # Like yog
    45: '2 ATTR, ATK and HP Boost',
    46: '2 ATTR, HP Boost',
    48: 'ATTR HP Boost',
    49: 'ATTR RCV Boost',
    50: 'ATTR Burst',
    51: 'Mass Attack',
    52: 'Orb Enhance',
    53: 'Egg Drop Rate Boost',
    54: 'Coin Drop Boost',
    55: 'True Damage Nuke',
    56: 'True Damage Nuke',
    58: 'ATTR Mass Attack',
    59: 'ATTR Nuke',    # THIS IS UNCERTAIN
    60: 'Counterattack',
    61: 'Rainbow',
    62: 'Type HP and ATK Boost',
    63: 'Type HP and RCV Boost',
    64: 'Type ATK and RCV Boost',
    65: 'Type All Stat Boost',  # i.e. 1.5x all stats for devil type
    66: 'Combo (Flat Multiplier)',
    67: 'ATTR HP and RCV Boost',
    69: 'ATTR and Type ATK Boost',
    71: 'Board Change',
    73: 'ATTR and Type HP and ATK Boost',
    75: 'ATTR and Type ATK and RCV Boost',
    76: 'ATTR and Type All Stat Boost',
    77: 'God/Dragon HP and ATK Boost',
    79: 'God/Dragon ATK and RCV Boost',
    84: 'HP Conditional Nuke',
    85: 'True Damage HP Conditional Nuke',
    86: 'Nuke with HP Penalty',
    87: 'Critical Attack with HP Penalty',
    88: 'Type Burst',
    89: 'Unknown',
    90: 'ATTR Burst',
    91: 'Bicolor Orb Enhance',
    92: 'Type Burst',
    93: 'Leader Swap',
    94: 'Low HP Conditional ATTR ATK Boost',
    95: 'Low HP Conditional Type ATK Boost',
    96: 'High HP Conditional ATTR ATK Boost',
    97: 'High HP Conditional Type ATK Boost',
    98: 'Combo (Scaled Multiplier)',
    100: 'Skill Activation ATK Boost',
    101: 'ATK Boost with Exact Combos',     # Although it has to do with Monster Hunter 4G Collab
    103: 'Unknown',
    104: "Combo (Flat Multiplier) ATTR ATK Boost",
    105: 'Reduced RCV, ATK Boost',
    106: 'ATK and RCV Boost with Combos (Flat)',     # Possible HP Cut, ATK Boost?
    107: 'HP Reduction',
    108: 'Reduced HP, Type ATK Boost',
    109: 'Row ATK Boost (not scaled)',
    110: 'Low HP Conditional, ATTR Damage Boost',
    111: '2 ATTR HP and ATK Boost',
    114: '2 ATTR All Stat Boost',
    115: 'Mini Nuke and HP Recovery',



    # THIS ONE IS REALLY IMPORTANT. FOR SKILLS THAT HAVE TWO PARTS I.E. BOARD UNLOCK, THEN BOARD CHANGE
    116: 'Two Part Active Skill',



    117: 'HP Recovery and Bind Clear',
    118: 'Random SKill',
    119: 'Row Match',
    121: 'Stat Boost',
    122: 'Low HP Conditional ATK Boost',
    123: 'High HP Conditional Boost',
    124: 'ATTR Combo (Scaling) ATK Boost',
    125: 'Team Unit Conditional Stat Boost', # i.e. if astaroth is on your team, type of thing
    126: 'Increased Skyfall Chance',
    127: 'Column Orb Change',
    128: 'Row Orb Change',



    # This one is hard
    129: 'Stat Boost',

    130: 'Low HP ATTR ATK Boost',
    131: 'High HP ATTR ATK Boost',

    132: 'Increased Orb Movement Time',
    133: 'Skill Activation Conditional ATK Boost',
    136: 'Multi ATTR Conditional Stat Boost',
    137: 'Multi Type Conditional Stat Boost',


    # Another very important one
    138: 'Two Part Leader Skill',



    139: 'HP MuLti Conditional ATK Boost',
    140: 'Orb Enhance',
    141: 'Random Location Orb Spawn',
    142: 'Attribute Change',
    143: 'ATTR Nuke',
    144: 'ATTR Nuke of ATTR2 ATK',
    145: 'HP Recovery',
    146: 'Haste',
    148: 'XP or Coin Drop Boost',
    149: 'Heal Match RCV Boost',
    150: 'Enhance Orb Match 5',
    151: 'Heart Cross',
    152: 'Orb Lock',
    153: 'Enemy ATTR Change',
    154: '3 ATTR to 1 ATTR',
    155: 'Multiboost',
    156: 'Awoken Skill Burst',
    157: 'ATTR Cross',
    158: 'Match X or more orbs',
    159: 'Advanced Row Match',
    160: 'Add Additional Combos',
    161: 'Gravity',
    162: '7x6',
    163: 'No Skyfall and Boost',
    164: 'ATTR Combo Conditional ATK and RCV Boost',
    165: 'Rainbow ATK and RCV',
    166: 'ATK and RCV Combo Scale',
    167: 'Row ATK and RCV Boost',
    169: 'Combo Mult plus Shield',
    170: 'Rainbow Mult plus Shield',
    171: 'Match ATTR plus Shield',
    172: 'Orb Lock Removal',
    173: 'Void Damage Absorption',
    175: 'Collab Conditional Boost',
    176: 'Unknown',
    177: 'Orb Remaining Multiplier',
    178: '4 Seconds Movement Time',
    179: 'HP Recovery',
    180: 'Increased Enhance Orb Skyfall',
    182: 'Row Match plus Damage Reduction',
    183: 'HP Conditional Boost',
    184: 'No Skyfall for X turns',
    185: 'Stat Boost',
    186: '7x6 and Stat Boost',
    188: 'Unknown',
    189: 'Shows Combo Path',
}
