"""
Contains code to convert a list of enemy behavior logic into a flattened structure
called a ProcessedSkillset.
"""

import copy

from .enemy_skillset import *
from typing import List, Any


class StandardSkillGroup(object):
    """Base class storing a list of skills."""

    def __init__(self, skills: List[ESAction]):
        # List of skills which execute.
        self.skills = skills


class TimedSkillGroup(StandardSkillGroup):
    """Set of skills which execute on a specific turn, possibly with a HP threshold."""

    def __init__(self, turn: int, hp: int, skills: List[ESAction]):
        StandardSkillGroup.__init__(self, skills)
        # The turn that this group executes on.
        self.turn = turn
        # The hp threshold that this group executes on, always present, even if 100.
        self.hp = hp


class EnemyCountSkillGroup(StandardSkillGroup):
    """Set of skills which execute when a specific number of enemies are present."""

    def __init__(self, count: int, skills: List, following_skills: List[ESAction]):
        StandardSkillGroup.__init__(self, skills)
        # Number of enemies required to trigger this set of actions.
        self.count = count
        # I don't remember what I was thinking this would be used for =(
        self.following_skills = following_skills


class HpSkillGroup(StandardSkillGroup):
    """Set of skills which execute when a HP threshold is reached."""

    def __init__(self, hp_ceiling: int, skills: List[ESAction]):
        StandardSkillGroup.__init__(self, skills)
        # The hp threshold that this group executes on, always present, even if 100.
        self.hp_ceiling = hp_ceiling


class ProcessedSkillset(object):
    """Flattened set of enemy skills.

    Skills are broken into chunks which are intended to be output independently,
    roughly in the order in which they're declared here.
    """

    def __init__(self, level: int):
        # The monster level this skillset applies to.
        self.level = level
        # Things like color/type resists, resolve, etc.
        self.base_abilities = []  # List[ESAction]
        # Preemptive attacks, shields, combo guards.
        self.preemptives = []  # List[ESAction]
        # Actions which execute according to the current turn before behavior
        # enters a stable loop state.
        self.timed_skill_groups = []  # List[StandardSkillGroup]
        # Actions which execute depending on the enemy on-screen count.
        self.enemycount_skill_groups = []  # List[StandardSkillGroup]
        # Multi-turn stable action loops.
        self.repeating_skill_groups = []  # List[StandardSkillGroup]
        # Single-turn stable action loops.
        self.hp_skill_groups = []  # List[StandardSkillGroup]


class Context(object):
    """Represents the game state when running through the simulator."""

    def __init__(self, level):
        self.turn = 1
        # Whether the current turn triggered a preempt flag.
        self.is_preemptive = False
        # Whether we are allowed to preempt based on level flags.
        self.do_preemptive = False
        # A bitmask for flag values which can be updated.
        self.flags = 0
        # A bitmask for flag values which can only be set.
        self.onetime_flags = 0
        # Special flag that is modified by the 'counter' operations.
        self.counter = 0
        # Current HP value.
        self.hp = 100
        # Monster level, toggles some behaviors.
        self.level = level
        # Number of enemies on the screen.
        self.enemies = 999
        # Cards on the team.
        self.cards = set()
        # TODO: implement enemy status flags correctly
        # If the monster is currently enraged, for how long.
        self.enraged = None

    def reset(self):
        self.is_preemptive = False

    def clone(self):
        return copy.deepcopy(self)

    def turn_event(self):
        self.turn += 1
        if self.enraged is not None:
            if self.enraged > 0:
                # count down enraged turns
                self.enraged -= 1
            elif self.enraged < 0:
                # count up enraged cooldown turns
                self.enraged += 1


def loop_through(ctx: Context, behaviors: List[Any]):
    """Executes a single turn through the simulator.

    This is called multiple times with varying Context values to probe the action set
    of the monster.
    """
    ctx.reset()
    # The list of behaviors identified for this loop.
    results = []
    # A list of behaviors which have been iterated over.
    traversed = []

    # The current spot in the behavior array.
    idx = 0
    # Number of iterations we've done.
    iter_count = 0
    while iter_count < 1000:
        # Safety measures against infinite loops, check if we've looped too many
        # times or if we've seen this behavior before in the current loop.
        iter_count += 1
        if idx >= len(behaviors) or idx in traversed:
            break
        traversed.append(idx)

        # Extract the current behavior and its type.
        b = behaviors[idx]
        b_type = type(b)

        # Processing for enrages.
        if b_type == ESAttackUp or b_type == ESAttackUpStatus:
            if ctx.enraged is None:
                if b.turn_cooldown is None:
                    ctx.enraged = b.turns
                    # TODO: this should append to results (assuming flags are checked)
                else:
                    ctx.enraged = -b.turn_cooldown + 1
                    idx += 1
                    continue
            else:
                if ctx.enraged == 0:
                    ctx.enraged = b.turns
                    # TODO: this should append to results (assuming flags are checked)
                else:
                    idx += 1
                    continue

        # The current action could be None because we nulled it out in preprocessing, just continue.
        if b is None or b_type == ESNone:
            idx += 1
            continue

        # Detection for preempts, null the behavior afterwards so we don't trigger it again.
        if b_type == ESPreemptive:
            behaviors[idx] = None
            ctx.is_preemptive = True
            ctx.do_preemptive = b.level <= ctx.level
            idx += 1
            continue

        # Processing for actions and unparsed stuff, this section should accumulate
        # items into results.
        if b_type == EnemySkillUnknown or issubclass(b_type, ESAction):
            # Check if we should execute this action at all.
            cond = b.condition
            if cond:
                # HP based checks.
                if cond.hp_threshold and ctx.hp >= cond.hp_threshold:
                    idx += 1
                    continue

                # Flag based checks (one-time and global flags).
                # This check might be wrong? This is checking if all flags are unset, maybe just one needs to be unset.
                if cond.one_time:
                    if not ctx.onetime_flags & cond.one_time:
                        ctx.onetime_flags = ctx.onetime_flags | cond.one_time
                        results.append(b)
                        return results
                    else:
                        idx += 1
                        continue

                if cond.ai == 100 and b_type != ESDispel:
                    # This always executes so it is a terminal action.
                    results.append(b)
                    return results
                else:
                    # Not a terminal action, so accumulate it and continue.
                    results.append(b)
                    idx += 1
                    continue
            else:
                # Stuff without a condition is always terminal.
                results.append(b)
                return results

        if b_type == ESBranchFlag:
            if b.branch_value == b.branch_value & ctx.flags:
                # If we satisfy the flag, branch to it.
                idx = b.target_round
            else:
                # Otherwise move to the next action.
                idx += 1
            continue

        if b_type == ESEndPath:
            # Forcibly ends the loop, generally used after multiple <100% actions.
            return results

        if b_type == ESFlagOperation:
            # Operations which change flag state, we always move to the next behavior after.
            if b.operation == 'SET' or b.operation == 'OR':
                # This is a bit suspicious that they have both SET and OR, possibly
                # these should be broken apart?
                ctx.flags = ctx.flags | b.flag
            elif b.operation == 'UNSET':
                ctx.flags = ctx.flags & ~b.flag
            else:
                raise ValueError('unsupported flag operation:', b.operation)
            idx += 1
            continue

        if b_type == ESBranchHP:
            # Branch based on current HP.
            if b.compare == '<':
                take_branch = ctx.hp < b.branch_value
            else:
                take_branch = ctx.hp >= b.branch_value
            idx = b.target_round if take_branch else idx + 1
            continue

        if b_type == ESBranchLevel:
            # Branch based on monster level.
            if b.compare == '<':
                take_branch = ctx.level < b.branch_value
            else:
                take_branch = ctx.level >= b.branch_value
            idx = b.target_round if take_branch else idx + 1
            continue

        if b_type == ESSetCounter:
            # Adjust the global counter value.
            if b.set == '=':
                ctx.counter = b.counter
            elif b.set == '+':
                ctx.counter += b.counter
            elif b.set == '-':
                ctx.counter -= b.counter
            idx += 1
            continue

        if b_type == ESSetCounterIf:
            # Adjust the counter if it has a specific value.
            if ctx.counter == b.counter_is:
                ctx.counter = b.counter
            idx += 1
            continue

        if b_type == ESBranchCounter:
            # Branch based on the counter value.
            if b.compare == '=':
                take_branch = ctx.counter == b.branch_value
            elif b.compare == '<':
                take_branch = ctx.counter <= b.branch_value
            elif b.compare == '>':
                take_branch = ctx.counter >= b.branch_value
            else:
                raise ValueError('unsupported counter operation:', b.compare)
            idx = b.target_round if take_branch else idx + 1
            continue

        if b_type == ESBranchCard:
            # Branch if it's checking for a card we have on the team.
            card_on_team = any([card in ctx.cards for card in b.branch_value])
            idx = b.target_round if card_on_team else idx + 1
            continue

        if b_type == ESBranchRemainingEnemies:
            # TODO: not implemented correctly
            idx += 1
            continue

        # TODO: not implemented correctly
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


def info_from_behaviors(behaviors):
    """Extract some static info from the behavior list and clean it up where necessary."""
    base_abilities = []
    hp_checkpoints = set()
    hp_checkpoints.add(100)
    card_checkpoints = set()
    has_enemy_remaining_branch = False

    for idx, es in enumerate(behaviors):
        # Extract the passives and null them out to simplify processing
        if type(es) in PASSIVE_MAP.values():
            base_abilities.append(es)
            behaviors[idx] = None

        # Find candidate branch HP values
        if type(es) == ESBranchHP:
            hp_checkpoints.add(es.branch_value)
            hp_checkpoints.add(es.branch_value - 1)

        # Find candidate action HP values
        if hasattr(es, 'condition'):
            cond = es.condition
            if cond.hp_threshold:
                hp_checkpoints.add(cond.hp_threshold)
                hp_checkpoints.add(cond.hp_threshold - 1)

        # Find checks for specific cards.
        if type(es) == ESBranchCard:
            card_checkpoints.update(es.branch_value)

        # Find checks for specific amounts of enemies.
        if type(es) == ESBranchRemainingEnemies:
            has_enemy_remaining_branch = True

    return base_abilities, hp_checkpoints, card_checkpoints, has_enemy_remaining_branch


def extract_preemptives(ctx: Context, behaviors: List[Any]):
    """Simulate the initial run through the behaviors looking for preemptives.

    If we find a preemptive, continue onwards. If not, roll the context back.
    """
    original_ctx = ctx.clone()

    cur_loop = loop_through(ctx, behaviors)
    if not cur_loop:
        # Some monsters have no skillset at all
        return None, None

    if ctx.is_preemptive:
        # Save the current loop as preempt
        return ctx, cur_loop
    else:
        # Roll back the context.
        return original_ctx, None


def convert(enemy_behavior: List, level: int):
    skillset = ProcessedSkillset(level)

    # Behavior is 1-indexed, so stick a fake row in to start
    behaviors = [None] + list(enemy_behavior)

    base_abilities, hp_checkpoints, card_checkpoints, has_enemy_remaining_branch = info_from_behaviors(
        behaviors)
    skillset.base_abilities = base_abilities

    ctx = Context(level)
    ctx, preemptives = extract_preemptives(ctx, behaviors)
    if ctx is None:
        # Some monsters have no skillset at all
        return skillset

    if preemptives is not None:
        skillset.preemptives = preemptives

    # For the first 20 turns, compute actions at every HP checkpoint
    turn_data = []
    for idx in range(0, 20):
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
                next_ctx = hp_ctx.clone()

        turn_data.append(hp_data)
        ctx = next_ctx
        ctx.turn_event()

    # Loop over every turn
    behavior_loops = []
    for i_idx, check_data in enumerate(turn_data):
        # Loop over every following turn. If the outer turn matches an inner turn moveset,
        # we found a loop.
        possible_loops = []
        for j_idx in range(i_idx + 1, len(turn_data) // 2):
            comp_data = turn_data[j_idx]
            if check_data == comp_data:
                # # do not include overlapping loops
                # loop_overlap = False
                # for comp_i, comp_j in behavior_loops:
                #     if i_idx < comp_j:
                #         loop_overlap = True
                # if not loop_overlap:
                possible_loops.append((i_idx, j_idx))
        if len(possible_loops) == 0:
            continue

        # Check all possible loops
        for check_start, check_end in possible_loops.copy():
            # Now that we found a loop, confirm that it continues
            loop_behavior = turn_data[check_start:check_end]

            for j_idx in range(check_end, len(turn_data), len(loop_behavior)):
                # Check to make sure we don't run over the edge of the array
                j_loop_end_idx = j_idx + len(loop_behavior)
                if j_loop_end_idx > len(turn_data):
                    # We've overlapped the end of the array with no breaks, quit
                    break

                comp_data = turn_data[j_idx:j_loop_end_idx]
                if loop_behavior != comp_data:
                    # The loop didn't continue so this is a bad selection, remove
                    possible_loops.remove((check_start, check_end))
                    break

        if len(possible_loops) > 0:
            behavior_loops.append(possible_loops[0])

    # Process loops
    looped_behavior = []
    if len(behavior_loops) > 0:
        loop_start, loop_end = behavior_loops[0]
        loop_size = loop_end - loop_start
        if loop_size == 1:
            # Since this isn't a multi-turn looping moveset, try to trim the earlier turns.
            looping_behavior = turn_data[loop_start]
            for idx in range(loop_start):
                check_turn_data = turn_data[idx]
                for hp, hp_behavior in looping_behavior.items():
                    if check_turn_data.get(hp, None) == hp_behavior:
                        check_turn_data.pop(hp)

                for hp, hp_behavior in check_turn_data.items():
                    skillset.timed_skill_groups.append(TimedSkillGroup(idx + 1, hp, hp_behavior))
                    looped_behavior.append((hp, hp_behavior))
        else:
            # exclude any behavior present on all turns of the loop
            common_behaviors = [hp_b for hp_b in turn_data[loop_start].items()]
            for idx in range(loop_start + 1, loop_end):
                for hp_b in common_behaviors.copy():
                    if hp_b not in turn_data[idx].items():
                        common_behaviors.remove(hp_b)
            for idx in range(loop_start, loop_end):
                for hp, hp_behavior in turn_data[idx].items():
                    if (hp, hp_behavior) not in common_behaviors:
                        skillset.repeating_skill_groups.append(
                            TimedSkillGroup(idx + 1, hp, hp_behavior))
                        looped_behavior.append((hp, hp_behavior))

    # Simulate enemies being defeated
    if has_enemy_remaining_branch:
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
            skillset.enemycount_skill_groups.append(
                EnemyCountSkillGroup(ecount, cur_loop, follow_loop))

    # Simulate HP decreasing
    globally_seen_behavior = []
    hp_ctx = ctx.clone()
    for checkpoint in sorted(hp_checkpoints, reverse=True):
        locally_seen_behavior = []
        hp_ctx.hp = checkpoint
        cur_loop = loop_through(hp_ctx, behaviors)
        while cur_loop not in globally_seen_behavior and cur_loop not in locally_seen_behavior:
            # exclude behavior already included in a repeat loop
            if (checkpoint, cur_loop) not in looped_behavior:
                skillset.hp_skill_groups.append(HpSkillGroup(checkpoint, cur_loop))
            globally_seen_behavior.append(cur_loop)
            locally_seen_behavior.append(cur_loop)
            cur_loop = loop_through(hp_ctx, behaviors)

    clean_skillset(skillset)

    return skillset


def extract_hp_threshold(es):
    """If the action has a HP threshold, extracts it."""
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
    # TODO: is this still the case post-changes with ai/onetime flags?
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

    for repeating_skills in skillset.repeating_skill_groups:
        for es in list(repeating_skills.skills):
            if es in extracted:
                repeating_skills.skills.remove(es)

    for es in extracted:
        hp_threshold = es.condition.hp_threshold
        placed = False
        for hp_group in skillset.hp_skill_groups:
            if hp_group.hp_ceiling == hp_threshold:
                hp_group.skills.append(es)
                break
        if not placed:
            skillset.hp_skill_groups.append(HpSkillGroup(hp_threshold, [es]))

    # Iterate over every skillset group and remove now-empty ones
    skillset.timed_skill_groups = [x for x in skillset.timed_skill_groups if x.skills]
    skillset.repeating_skill_groups = [x for x in skillset.repeating_skill_groups if x.skills]
    skillset.enemycount_skill_groups = [x for x in skillset.enemycount_skill_groups if x.skills]
    skillset.hp_skill_groups = [x for x in skillset.hp_skill_groups if x.skills]
    skillset.hp_skill_groups.sort(key=lambda x: x.hp_ceiling, reverse=True)


def extract_levels(enemy_behavior: List[Any]):
    """Scan through the behavior list and compile a list of level values, always including 1."""
    levels = set()
    levels.add(1)
    for b in enemy_behavior:
        if type(b) == ESBranchLevel:
            levels.add(b.branch_value)
        elif hasattr(b, 'level'):
            levels.add(b.level)
    return levels
