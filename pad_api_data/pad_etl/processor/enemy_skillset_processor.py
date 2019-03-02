import copy

from .enemy_skillset import *
from .merged_data import MergedEnemy


class SkillItem(object):
    def __init__(self, name: str, comment: str, damage: int=None):
        self.name = name
        self.comment = comment
        self.damage = damage


class StandardSkillGroup(object):
    def __init__(self, skills=[]):
        self.skills = skills


class TimedSkillGroup(StandardSkillGroup):
    def __init__(self, turn: int, hp: int, skills=[]):
        StandardSkillGroup.__init__(self, skills)
        self.turn = turn
        self.hp = hp
        self.loops = False


class EnemyCountSkillGroup(StandardSkillGroup):
    def __init__(self, count: int, skills=[], following_skills=[]):
        StandardSkillGroup.__init__(self, skills)
        self.count = count
        self.following_skills = following_skills


class HpSkillGroup(StandardSkillGroup):
    def __init__(self, hp_ceiling: int, skills=[]):
        StandardSkillGroup.__init__(self, skills)
        # TODO: this is the wrong way to handle this. Should combine a HP value
        # and a directional check.
        self.hp_ceiling = hp_ceiling


def dump_obj(o):
    if isinstance(o, ESSkillSet):
        msg = 'SkillSet:'
        msg += '\n\tCondition: {}'.format(json.dumps(o.condition,
                                                     sort_keys=True, default=lambda x: x.__dict__))
        for idx, behavior in enumerate(o.skill_list):
            msg += '\n\t{} {}'.format(idx, dump_obj(behavior))
        return msg
    elif isinstance(o, EnemySkillUnknown):
        return 'Unknown skill:{}'.format(o.name)
    else:
        msg = ''
        if hasattr(o, 'condition') and o.condition:
            msg += 'Condition: {}\n'.format(json.dumps(o.condition,
                                                       sort_keys=True, default=lambda x: x.__dict__))
        msg += '{} {} {}'.format(type(o).__name__, o.name, o.description)
        return msg


class ProcessedSkillset(object):
    def __init__(self):
        self.base_abilities = []  # List[SkillItem]
        self.preemptives = []  # List[SkillItem]
        self.timed_skill_groups = []  # List[StandardSkillGroup]
        self.enemycount_skill_groups = []  # List[StandardSkillGroup]
        self.hp_skill_groups = []  # List[StandardSkillGroup]

    def dump(self):
        msg = 'ProcessedSkillset'

        msg += '\nBase:'
        for x in self.base_abilities:
            msg += '\n' + dump_obj(x)

        msg += '\n\nPreemptives:'
        for x in self.preemptives:
            msg += '\n' + dump_obj(x)

        msg += '\n\nTimed Groups:'
        for x in self.timed_skill_groups:
            msg += '\n\nTurn {}'.format(x.turn)
            for y in x.skills:
                msg += '\n{}'.format(dump_obj(y))

        msg += '\n\nEnemyCount Groups:'
        for x in self.enemycount_skill_groups:
            msg += '\n\nEnemies {}'.format(x.count)
            for y in x.skills:
                msg += '\n'.format(dump_obj(y))

        msg += '\n\nHP Groups:'
        for x in self.hp_skill_groups:
            msg += '\n\nHP Ceiling {}'.format(x.hp_ceiling)
            for y in x.skills:
                msg += '\n{}'.format(dump_obj(y))

        return msg


def to_item(action: ESAction):
    return SkillItem(action.name, action.description, 0)


class Context(object):
    def __init__(self, level):
        self.turn = 1
        self.is_preemptive = False
        self.do_preemptive = False
        self.flags = 0
        self.onetime_flags = 0
        self.counter = 0
        self.hp = 100
        self.level = level
        self.enemies = 999
        self.cards = set()

    def reset(self):
        self.is_preemptive = False

    def clone(self):
        return copy.deepcopy(self)


def loop_through(ctx: Context, behaviors):
    ctx.reset()
    results = []
    traversed = []
    errors = []

    idx = 0
    iter_count = 0
    while iter_count < 1000:
        iter_count += 1
        if idx >= len(behaviors) or idx in traversed:
            break
        traversed.append(idx)

        b = behaviors[idx]
        b_type = type(b)

        if b is None or b_type == ESNone:
            idx += 1
            continue

        if b_type == ESPreemptive:
            behaviors[idx] = None
            idx += 1
            ctx.is_preemptive = True
            ctx.do_preemptive = b.level <= ctx.level
            continue

        if b_type == EnemySkillUnknown or issubclass(b_type, ESAction):
            cond = b.condition
            if cond:
                # This check might be wrong? This is checking if all flags are unset, maybe just one needs to be unset.
                if cond.hp_threshold and ctx.hp >= cond.hp_threshold:
                    idx += 1
                    continue

                if cond.one_time:
                    if not ctx.onetime_flags & cond.one_time:
                        ctx.onetime_flags = ctx.onetime_flags | cond.one_time
                        results.append(b)
                        return results
                    else:
                        idx += 1
                        continue

                if cond.ai == 100:
                    results.append(b)
                    return results
                else:
                    results.append(b)
                    idx += 1
                    continue
            else:
                results.append(b)
                return results

        if b_type == ESBranchFlag:
            if b.branch_value == b.branch_value & ctx.flags:
                idx = b.target_round
            else:
                idx += 1
            continue

        if b_type == ESEndPath:
            break

        if b_type == ESFlagOperation:
            if b.operation == 'SET' or b.operation == 'OR':
                ctx.flags = ctx.flags | b.flag
            elif b.operation == 'UNSET':
                ctx.flags = ctx.flags & ~b.flag
            else:
                raise ValueError('unsupported flag operation:', b.operation)
            idx += 1
            continue

        if b_type == ESBranchHP:
            take_branch = False
            if b.compare == '<':
                take_branch = ctx.hp < b.branch_value
            else:
                take_branch = ctx.hp >= b.branch_value
            if take_branch:
                idx = b.target_round
            else:
                idx += 1
            continue

        if b_type == ESBranchLevel:
            take_branch = False
            if b.compare == '<':
                take_branch = ctx.level < b.branch_value
            else:
                take_branch = ctx.level >= b.branch_value
            if take_branch:
                idx = b.target_round
            else:
                idx += 1
            continue

        if b_type == ESSetCounter:
            if b.set == '=':
                ctx.counter = b.counter
            elif b.set == '+':
                ctx.counter += b.counter
            elif b.set == '-':
                ctx.counter -= b.counter
            idx += 1
            continue

        if b_type == ESSetCounterIf:
            if ctx.counter == b.counter_is:
                ctx.counter = b.counter
            idx += 1
            continue

        if b_type == ESBranchCounter:
            take_branch = False
            if b.compare == '<':
                take_branch = ctx.counter < b.branch_value
            else:
                take_branch = ctx.counter >= b.branch_value
            if take_branch:
                idx = b.target_round
            else:
                idx += 1
            continue

        if b_type == ESBranchCard:
            if any([card in ctx.cards for card in b.branch_value]):
                idx = b.target_round
            else:
                idx += 1
            continue


        # if b_type == ESCountdown:
        #    if ctx.counter == 0:
        #        idx += 1
        #        continue
        #    else:
        #        ctx.counter -= 1
        #        break

        raise ValueError('unsupported operation:', b_type, b)

    if iter_count == 1000:
        print('error, iter count exceeded 1000')

    return results


def convert(enemy: MergedEnemy, level: int):
    skillset = ProcessedSkillset()

    # Behavior is 1-indexed, so stick a fake row in to start
    behaviors = [None] + list(enemy.behavior)

    hp_checkpoints = set()
    hp_checkpoints.add(100)
    card_checkpoints = set()
    for idx, es in enumerate(behaviors):
        # Extract the passives and null them out to simplify processing
        if type(es) in PASSIVE_MAP.values():
            skillset.base_abilities.append(es)
            behaviors[idx] = None

        # Find candidate branch HP values
        if type(es) == ESBranchHP:
            hp_checkpoints.add(es.branch_value)
            if es.branch_value != 100:
                hp_checkpoints.add(es.branch_value + 1)
            if es.branch_value != 0:
                hp_checkpoints.add(es.branch_value - 1)

        # Find candidate action HP values
        if hasattr(es, 'condition'):
            cond = es.condition
            if cond.hp_threshold:
                hp_checkpoints.add(cond.hp_threshold)
                if cond.hp_threshold != 100:
                    hp_checkpoints.add(cond.hp_threshold + 1)
                if cond.hp_threshold != 0:
                    hp_checkpoints.add(cond.hp_threshold - 1)

        if type(es) == ESBranchCard:
            card_checkpoints.update(es.branch_value)

    ctx = Context(level)
    last_ctx = ctx.clone()

    cur_loop = loop_through(ctx, behaviors)
    if not cur_loop:
        # Some monsters have no skillset at all
        return skillset

    if ctx.is_preemptive:
        # Save the current loop as preempt
        skillset.preemptives = cur_loop
        cur_loop = []
        last_ctx = ctx.clone()
    else:
        # Roll back the context.
        ctx = last_ctx.clone()

    # For the first 10 turns, compute actions at every HP checkpoint
    turn_data = []
    for idx in range(0, 10):
        next_ctx = None
        hp_data = {}
        seen_behavior = []
        for checkpoint in sorted(hp_checkpoints, reverse=True):
            hp_ctx = ctx.clone()
            hp_ctx.hp = checkpoint
            cur_behavior = loop_through(hp_ctx, behaviors)
            if cur_behavior not in seen_behavior:
                hp_data[checkpoint] = cur_behavior
                seen_behavior.append(cur_behavior)

            if next_ctx is None:
                # We need to flip flags, so arbitrarily pick the first ctx to roll over.
                next_ctx = hp_ctx

        turn_data.append(hp_data)
        ctx = next_ctx

    # Loop over every turn
    loop_start = None
    loop_end = None
    for i_idx, check_data in enumerate(turn_data):
        # Loop over every following turn. If the outer turn matches an inner turn moveset,
        # we found a loop.
        loop_found_idx = None
        for j_idx in range(i_idx + 1, len(turn_data)):
            comp_data = turn_data[j_idx]
            if check_data == comp_data:
                loop_found_idx = j_idx
                break

        if loop_found_idx:
            # We found a loop, trim the rest of the moveset.
            turn_data = turn_data[:loop_found_idx]
            loop_start = i_idx
            loop_end = loop_found_idx
            break

    # Need a processing loop in here to break HP conditions out from other actions

    loop_size = loop_end - loop_start
    if loop_size == 1 and loop_start > 0:
        # Since this isn't a multi-turn looping moveset, try to trim the earlier turns.
        looping_behavior = turn_data[loop_start]
        for idx in range(loop_start):
            check_turn_data = turn_data[idx]
            for hp, hp_behavior in looping_behavior.items():
                if check_turn_data.get(hp, None) == hp_behavior:
                    check_turn_data.pop(hp)

            for hp, hp_behavior in check_turn_data.items():
                skillset.timed_skill_groups.append(TimedSkillGroup(idx + 1, hp, hp_behavior))

    if loop_size > 1:
        # TODO: for loop_size > 1, extract stable behaviors
        pass

    # Simulate enemies being defeated
    default_enemy_action = loop_through(ctx, behaviors)
    seen_skillsets = [default_enemy_action]
    for ecount in range(6, 0, -1):
        ctx.enemies = ecount
        cur_loop = loop_through(ctx, behaviors)

        if cur_loop in seen_skillsets:
            continue

        seen_skillsets.append(cur_loop)

        # Check for the first action being one-time. Kind of a hacky special case for loops.
        follow_loop = loop_through(ctx, behaviors)
        if follow_loop == cur_loop:
            follow_loop = None
        else:
            seen_skillsets.append(follow_loop)
        skillset.enemycount_skill_groups.append(EnemyCountSkillGroup(ecount, cur_loop, follow_loop))

    # Simulate HP decreasing
    globally_seen_behavior = []
    for checkpoint in sorted(hp_checkpoints, reverse=True):
        locally_seen_behavior = []
        hp_ctx = ctx.clone()
        hp_ctx.hp = checkpoint
        cur_loop = loop_through(hp_ctx, behaviors)
        while cur_loop not in globally_seen_behavior and cur_loop not in locally_seen_behavior:
            globally_seen_behavior.append(cur_loop)
            locally_seen_behavior.append(cur_loop)
            skillset.hp_skill_groups.append(HpSkillGroup(checkpoint, cur_loop))
            cur_loop = loop_through(hp_ctx, behaviors)

    clean_skillset(skillset)

    return skillset


def extract_hp_threshold(es):
    if hasattr(es, 'condition'):
        c = es.condition
        if hasattr(c, 'hp_threshold'):
            return c.hp_threshold
    return None


def clean_skillset(skillset: ProcessedSkillset):
    # First cleanup: items with a condition attached can show up in timed
    # groups and also in random HP buckets (generally the 100% one due to
    # earlier cleanups).
    #
    # Extract the ones in the HP buckets to a unique set, then only remove
    # timed entries that match (to prevent removing things like, <50% in turn 1).
    #
    # Then re-insert the skills into their own HP group.
    extracted = []
    for hp_skills in skillset.hp_skill_groups:
        for es in list(hp_skills.skills):
            if extract_hp_threshold(es) and extract_hp_threshold(es) != hp_skills.hp_ceiling:
                if es not in extracted:
                    extracted.append(es)
                hp_skills.skills.remove(es)

    for timed_skills in skillset.timed_skill_groups:
        for es in list(timed_skills.skills):
            if es in extracted:
                timed_skills.skills.remove(es)

    for es in extracted:
        hp_threshold = es.condition.hp_threshold
        placed = False
        for hp_group in skillset.hp_skill_groups:
            if hp_group.hp_ceiling == hp_threshold:
                hp_group.skills.append(es)
                break
        if not placed:
            skillset.hp_skill_groups.append(HpSkillGroup(hp_threshold, [es]))
