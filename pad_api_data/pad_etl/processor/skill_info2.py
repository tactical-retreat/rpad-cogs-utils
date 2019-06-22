ALL_ATTR = [0, 1, 2, 3, 4]

ATTRIBUTES = {0: 'Fire',
              1: 'Water',
              2: 'Wood',
              3: 'Light',
              4: 'Dark',
              5: 'Heal',
              6: 'Jammer',
              7: 'Poison',
              8: 'Mortal Poison',
              9: 'Bomb'}

TYPES = {0: 'Evo Material',
         1: 'Balanced',
         2: 'Physical',
         3: 'Healer',
         4: 'Dragon',
         5: 'God',
         6: 'Attacker',
         7: 'Devil',
         8: 'Machine',
         12: 'Awaken Material',
         14: 'Enhance Material',
         15: 'Redeemable Material'}


class ActiveSkill(object):
    def __init__(self, monster_skill):
        self.name = monster_skill.name
        self.raw_description = monster_skill.description
        self.skill_type = monster_skill.skill_type
        self.levels = monster_skill.levels
        self.turn_max = monster_skill.turn_max
        self.turn_min = monster_skill.turn_min


class LeaderSkill(object):
    def __init__(self, monster_skill):
        self.name = monster_skill.name
        self.raw_description = monster_skill.description
        self.skill_type = monster_skill.skill_type


class ASFixedAttrNuke(ActiveSkill):
    def __init__(self, monster_skill):
        super().__init__(monster_skill)

        self.attribute = monster_skill.other_fields[0]
        self.damage = monster_skill.other_fields[1]
        self.mass_attack = True


class ASSelfAttrNuke(ActiveSkill):
    def __init__(self, monster_skill):
        super().__init__(monster_skill)

        self.multiplier = monster_skill.other_fields[0] / 100
        self.mass_attack = False


# Leader skills
class LSPassiveStats(LeaderSkill):
    def __init__(self, monster_skill):
        super().__init__(monster_skill)

        self.reduction_attributions = ALL_ATTR
        self.damage_reduction = monster_skill.other_fields[0] / 100


class LSAfterAttack(LeaderSkill):
    def __init__(self, monster_skill):
        super().__init__(monster_skill)

        self.multiplier = monster_skill.other_fields[0] / 100
