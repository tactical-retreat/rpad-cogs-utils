# Parsing bonus data.

# keys: 'sebiadm'
# s: start
# e: end
# b: bonus type
# 2: coins * 10000
# 3: drop * 10000
# 5: stamina * 10000
# 6: special dungeon
# 8: PEM
# 9: REM
# 10: PEM cost? (skip)
# 11: xp bonus chance * 10000
# 12: (old:) absolute +egg rate?? * 10000
# 14: GF announcement?
# 16: (new:) relative +egg rate?? * 10000
# 17: skillup bonus
# 21: tournament over?
# 22: tournament?
# i: unknown

# TODO:
#   - Identify urgents. (They last for an hour.)
#   - Rather than start-end times, have time categories.
#       - Categories:
#           - Urgent (1 hour).
#           - Day.
#           - Week.
#           - Biweek.
#               ? Two-week?
#           - Halfmonth.
#               - E.g. coin dungeons and MP shop.
#           -
#   ^- Or have times.
#       - Hour.
#       - Day.
#   ^^- Or have columns per unit.
#       - Hour.
#       - Day.
#       - Week.
#       -
#       -
#   -! The bonus data depends on group. (E.g. urgents.)
#   -
#   -


def ghmult(x):
    mult = x / 10000
    if int(mult) == mult:
        mult = int(mult)
    return '%sx' % mult


def ghchance(x):
    assert x % 100 == 0
    return '%d%%' % (x // 100)


class Bonus:
    types = {
        1: {'b': 'exp*', 'a': ghmult},
        2: {'b': 'coin*', 'a': ghmult},
        3: {'b': 'drop*', 'a': ghmult},
        5: {'b': 'stam*', 'a': ghmult},
        11: {'b': 'great*', 'a': ghmult},
        12: {'b': '+egg%', 'a': ghchance},
        16: {'b': '+egg*', 'a': ghmult},
        17: {'b': 'skill*', 'a': ghmult},

        6: {'b': 'dung'},  # special/co-op dungeon list
        10: {'b': 'pem$', 'a': int},
        # 8: {'b':'rem?', },
        # 9: {'b':'pem?', },
        8: {'b': 'pem?', },  # Or "current"?
        9: {'b': 'rem?', },  # Or "next"?
        14: {'b': 'gf_?', },
        21: {'b': 'trn_anc', },  # "tourney is over, results pending"?
        22: {'b': 'annc', },
        23: {'b': 'meta?', },   # metadata?

    }

    keys = 'sebiadm'

    def __init__(self, raw):
        if not set(raw) <= set(Bonus.keys):
            raise ValueError('Unexpected keys: ' + str(set(Bonus.keys) - set(raw)))

        # Start time as gungho time string
        self.s = raw['s']

        # End time as gungho time string
        self.e = raw['e']

        # If populated, a dungeon id
        self.d = None
        if 'd' in raw:
            self.d = int(raw['d'])

        # If populated, a message (including formatting color)
        if 'm' in raw:
            self.m = 'm'.replace('\n', r'\n')

        b = raw['b']
        others = 'iam'
        if b in Bonus.types:
            typ = Bonus.types[b]
            self.b = typ['b']

        else:
            self.b = b
            typ = {}

        for k in others:
            if k in raw:
                if k in typ:
                    setattr(self, k, typ[k](raw[k]))
                else:
                    setattr(self, k, raw[k])
        self.raw = raw

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
