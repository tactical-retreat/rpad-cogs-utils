"""
Contains code to convert a list of enemy behavior logic into a flattened structure
called a ProcessedSkillset.
"""
import collections
import copy

import pad_etl.processor.debug_utils
from pad_etl.data.card import BookCard
from .enemy_skillset import *
from typing import List, Any, Set, Tuple


# This is a hack that accounts for the fact that some monsters seem to be zero-indexed
# rather than 1-indexed for jumps. Not obvious why this occurs yet.
ZERO_INDEXED_MONSTERS = [
    565, # Goemon
]

class StandardSkillGroup(object):
    """Base class storing a list of skills."""

    def __init__(self, skills: List[ESAction], hp_threshold):
        # List of skills which execute.
        self.skills = skills
        # The hp threshold that this group executes on, always present, even if 100.
        self.hp = hp_threshold


class TimedSkillGroup(StandardSkillGroup):
    """Set of skills which execute on a specific turn, possibly with a HP threshold."""

    def __init__(self, turn: int, hp_threshold: int, skills: List[ESAction]):
        super().__init__(skills, hp_threshold)
        # The turn that this group executes on.
        self.turn = turn
        # If set, this group executes over a range of turns
        self.end_turn = None  # int


class RepeatSkillGroup(TimedSkillGroup):
    """Set of skills which execute on a specific turn, possibly with a HP threshold."""

    def __init__(self, turn: int, interval: int, hp_threshold: int, skills: List[ESAction]):
        super().__init__(turn, hp_threshold, skills)
        # The number of turns between repeats, aka loop size
        self.interval = interval  # int


class EnemyCountSkillGroup(StandardSkillGroup):
    """Set of skills which execute when a specific number of enemies are present."""

    def __init__(self, count: int, hp_threshold: int, skills: List[ESAction]):
        super().__init__(skills, hp_threshold)
        # Number of enemies required to trigger this set of actions.
        self.count = count


class HpSkillGroup(StandardSkillGroup):
    """Set of skills which execute when a HP threshold is reached."""

    def __init__(self, hp_threshold: int, skills: List[ESAction]):
        super().__init__(skills, hp_threshold)


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
        self.timed_skill_groups = []  # List[TimedSkillGroup]
        # Actions which execute depending on the enemy on-screen count.
        self.enemycount_skill_groups = []  # List[StandardSkillGroup]
        # Multi-turn stable action loops.
        self.repeating_skill_groups = []  # List[RepeatSkillGroup]
        # Single-turn stable action loops.
        self.hp_skill_groups = []  # List[StandardSkillGroup]
        # Action which triggers when a staus is applied
        self.status_action = None # ESAttackUpStatus



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
        # A bitmask for flag values which can only be unset.
        self.skill_use = 0
        # Special flag that is modified by the 'counter' operations.
        self.counter = 0
        # Countdown on/off
        self.countdown = False
        # Current HP value.
        self.hp = 100
        # Monster level, toggles some behaviors.
        self.level = level
        # Number of enemies on the screen.
        self.enemies = 999
        # Cards on the team.
        self.cards = set()
        # Turns of enrage, initial:None -> (enrage cooldown period:int<0 ->) enrage:int>0 -> expire:int=0
        self.enraged = None
        # Turns of damage shield, initial:int=0 -> shield up:int>0 -> expire:int=0
        self.damage_shield = 0
        # Turns of status shield, initial:int=0 -> shield up:int>0 -> expire:int=0
        self.status_shield = 0
        # Turns of combo shield, initial:int=0 -> shield up:int>0 -> expire:int=0
        self.combo_shield = 0

    def reset(self):
        self.is_preemptive = False

    def clone(self):
        return copy.deepcopy(self)

    def check_skill_use(self, usage):
        raise NotImplementedError('check_skill_use')

    def update_skill_use(self, usage):
        raise NotImplementedError('update_skill_use')

    def turn_event(self):
        self.turn += 1
        if self.enraged is not None:
            if self.enraged > 0:
                # count down enraged turns
                self.enraged -= 1
            elif self.enraged < 0:
                # count up enraged cooldown turns
                self.enraged += 1
        if self.damage_shield > 0:
            # count down shield turns
            self.damage_shield -= 1
        if self.status_shield > 0:
            # count down shield turns
            self.status_shield -= 1
        if self.combo_shield > 0:
            # count down shield turns
            self.combo_shield -= 1
        if self.countdown:
            if self.counter > 0:
                self.counter -= 1
            else:
                self.countdown = False

    def apply_skill_effects(self, behavior):
        """Check context to see if a skill is allowed to be used, and update flag accordingly"""
        b_type = type(behavior)
        if issubclass(b_type, ESAttackUp):
            if b_type == ESAttackUPRemainingEnemies \
                    and behavior.enemy_count is not None \
                    and self.enemies > behavior.enemy_count:
                return False
            if self.enraged is None:
                if b_type == ESAttackUPCooldown and behavior.turn_cooldown is not None:
                    self.enraged = -behavior.turn_cooldown + 1
                    return False
                else:
                    self.enraged = behavior.turns
                    return True
            else:
                if self.enraged == 0:
                    self.enraged = behavior.turns
                    return True
                else:
                    return False
        elif b_type == ESDamageShield:
            if self.damage_shield == 0:
                self.damage_shield = behavior.turns
                return True
            else:
                return False
        elif b_type == ESStatusShield:
            if self.status_shield == 0:
                self.status_shield = behavior.turns
                return True
            else:
                return False
        elif b_type == ESAbsorbCombo:
            if self.combo_shield == 0:
                self.combo_shield = behavior.max_turns
                return True
            else:
                return False
        elif b_type == ESRecoverEnemy:
            self.hp += behavior.max_amount
        return True


class CTXBitmap(Context):
    def __init__(self, level, skill_use_flags):
        # TODO: skill_use_flags param might be useless
        super(CTXBitmap, self).__init__(level)
        self.skill_use = 0

    def check_skill_use(self, usage):
        return usage is None or self.skill_use & usage == 0

    def update_skill_use(self, usage):
        if usage is not None:
            self.skill_use |= usage


class CTXCounter(Context):
    def __init__(self, level, skill_use_counter):
        # TODO: skill_use_counter param might be useless
        super(CTXCounter, self).__init__(level)
        self.skill_use = 0

    def check_skill_use(self, usage):
        if usage is None:
            return True
        else:
            if self.skill_use == 0:
                return True
            elif self.skill_use > 0:
                self.skill_use -= 1
                return False

    def update_skill_use(self, usage):
        if usage is not None:
            self.skill_use += usage


def default_attack():
    """Indicates that the monster uses its standard attack."""
    return ESDefaultAttack()


def loop_through(ctx, behaviors: List[Any]):
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
            # Disabling default action for now; doesn't seem to improve things?
            # if len(results) == 0:
            #     # if the result set is empty, add something
            #     results.append(default_attack())
            return results
        traversed.append(idx)

        # Extract the current behavior and its type.
        b = behaviors[idx]
        b_type = type(b)

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

        if b_type == ESAttackPreemptive:
            behaviors[idx] = None
            ctx.is_preemptive = True
            ctx.do_preemptive = True
            results.append(b)
            ctx.update_skill_use(b.condition.one_time)
            return results

        if b_type == ESCountdown:
            ctx.countdown = True
            if ctx.counter == 1:
                idx += 1
                continue
            else:
                results.append(b)
                return results

        if b_type == ESAttackUpStatus:
            # This is a special case; it's not a terminal action unlike other enrages.
            results.append(b)
            idx += 1
            continue


        # Processing for actions and unparsed stuff, this section should accumulate
        # items into results.
        if b_type == EnemySkillUnknown or issubclass(b_type, ESAction):
            # Check if we should execute this action at all.
            if skill_has_condition(b):
                cond = b.condition
                # HP based checks.
                if cond.hp_threshold and ctx.hp >= cond.hp_threshold:
                    idx += 1
                    continue

                if cond.use_chance() == 100 and b_type != ESDispel:
                    # This always executes so it is a terminal action.
                    if not ctx.check_skill_use(cond.one_time):
                        idx += 1
                        continue
                    if not ctx.apply_skill_effects(b):
                        idx += 1
                        continue
                    ctx.update_skill_use(cond.one_time)
                    results.append(b)
                    return results
                else:
                    # Not a terminal action, so accumulate it and continue.
                    if ctx.check_skill_use(cond.one_time) and ctx.apply_skill_effects(b):
                        results.append(b)
                    idx += 1
                    continue
            else:
                # Stuff without a condition is always terminal.
                if not ctx.apply_skill_effects(b):
                    idx += 1
                    continue
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
            # Disabling default action for now; doesn't seem to improve things?
            # if len(results) == 0:
            #     # if the result set is empty, add something
            #     results.append(default_attack())
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
            if ctx.enemies == b.branch_value:
                idx = b.target_round
            else:
                idx += 1
            continue

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
        if issubclass(type(es), ESPassive):
            base_abilities.append(es)
            behaviors[idx] = None

        # Find candidate branch HP values
        if type(es) == ESBranchHP:
            hp_checkpoints.add(es.branch_value)
            hp_checkpoints.add(es.branch_value - 1)

        # Find candidate action HP values
        if skill_has_condition(es):
            cond = es.condition
            if cond and cond.hp_threshold:
                hp_checkpoints.add(cond.hp_threshold)
                hp_checkpoints.add(cond.hp_threshold - 1)

        # Find checks for specific cards.
        if type(es) == ESBranchCard:
            card_checkpoints.update(es.branch_value)

        # Find checks for specific amounts of enemies.
        if type(es) == ESBranchRemainingEnemies or type(es) == ESAttackUPRemainingEnemies:
            has_enemy_remaining_branch = True

    return base_abilities, hp_checkpoints, card_checkpoints, has_enemy_remaining_branch


def extract_preemptives(ctx: Context, behaviors: List[Any]):
    """Simulate the initial run through the behaviors looking for preemptives.

    If we find a preemptive, continue onwards. If not, roll the context back.
    """
    original_ctx = ctx.clone()

    cur_loop = loop_through(ctx, behaviors)
    if ctx.is_preemptive:
        # Save the current loop as preempt
        return ctx, cur_loop
    else:
        # Roll back the context.
        return original_ctx, None


def extract_turn_behaviors(ctx: Context, behaviors: List, hp_checkpoints: Set[int]) -> Tuple[dict, Context]:
    """
    Simulate the first 20 turns at all hp check points
    """
    res_ctx = None
    seen_behaviour = []
    hp_turn_data = {}
    for checkpoint in sorted(hp_checkpoints, reverse=True):
        hp_ctx = ctx.clone()
        hp_ctx.hp = checkpoint

        turn_data = []
        for idx in range(0, 20):
            cur_behavior = loop_through(hp_ctx, behaviors)
            if len(cur_behavior) > 0 and cur_behavior not in seen_behaviour:
                turn_data.append(cur_behavior)
            else:
                turn_data.append(None)
            hp_ctx.turn_event()

        seen_behaviour.extend(turn_data)
        if checkpoint == 100:
            res_ctx = hp_ctx

        hp_turn_data[checkpoint] = turn_data

    # Clean turn data
    for hp, turn_data in hp_turn_data.copy().items():
        if all([x is None for x in turn_data]):
            hp_turn_data.pop(hp)

    # for hp, turn_data in hp_turn_data.items():
    #     print('=====HP {}====='.format(hp))
    #     for turn, data in enumerate(turn_data):
    #         print('TURN {}:'.format(turn))
    #         if data is None:
    #             print('\tNone')
    #         else:
    #             for d in data:
    #                 print('\t' + d.name)

    return hp_turn_data, res_ctx


def extract_loop_indexes(turn_data: List) -> Tuple[int, int]:
    """
    Find loops in the data
    """
    # Loop over every turn
    for i_idx, check_data in enumerate(turn_data):
        # Loop over every following turn. If the outer turn matches an inner turn moveset,
        # we found a loop.
        possible_loops = []
        for j_idx in range(i_idx + 1, len(turn_data)):
            comp_data = turn_data[j_idx]
            if check_data == comp_data:
                possible_loops.append((i_idx, j_idx))
        if len(possible_loops) == 0:
            continue

        # Check all possible loops
        for check_start, check_end in possible_loops.copy():
            # Now that we found a loop, confirm that it continues
            loop_behavior = turn_data[check_start:check_end]
            loop_verified = False

            for j_idx in range(check_end, len(turn_data), len(loop_behavior)):
                # Check to make sure we don't run over the edge of the array
                j_loop_end_idx = j_idx + len(loop_behavior)
                if j_loop_end_idx > len(turn_data):
                    # We've overlapped the end of the array with no breaks, quit
                    break

                comp_data = turn_data[j_idx:j_loop_end_idx]
                loop_verified = loop_behavior == comp_data
                if not loop_verified:
                    break

            if not loop_verified:
                # The loop didn't continue so this is a bad selection, remove
                possible_loops.remove((check_start, check_end))

        if len(possible_loops) > 0:
            return possible_loops[0][0], possible_loops[0][1]


def remove_duplicate_behaviour(data: list, start: int, end: int) -> list:
    """
    Helper: remove any behaviour that occurs more than once in the set
    """
    for idx in range(start, end):
        if data[idx] is None:
            continue
        del_idx = False
        for jdx in range(idx + 1, end):
            if data[jdx] is None:
                continue
            if data[idx] == data[jdx]:
                del_idx = True
                data[jdx] = None
        if del_idx:
            data[idx] = None
    return data


def remove_common_behaviour(data: list, start: int, end: int) -> list:
    """
    Helper: remove any behaviour that occurs more than once in the set
    """
    if any([x is None for x in data[start:end]]):
        return data
    common_behaviour = data[start].copy()
    for idx in range(start + 1, end):
        for skill in common_behaviour:
            if skill not in data[idx]:
                common_behaviour.remove(skill)
    for idx in range(start, end):
        if data[idx] is None:
            continue
        for skill in data[idx].copy():
            if skill in common_behaviour:
                data[idx].remove(skill)
    return data


def remove_seen_behaviour(data: list, start: int, end: int, seen_data: list) -> list:
    """
    Helper: remove any behaviour in the seen_data list
    """
    for idx in range(start, end):
        if data[idx] is None:
            continue
        if data[idx] in seen_data:
            data[idx] = None
    return data


def extract_loop_skills(hp: int, turn_data: list, loop_start: int, loop_end: int) -> Tuple[List[RepeatSkillGroup], List[TimedSkillGroup], List]:
    """
    Remove duplicate behaviour in loop and populate repeat & timed skill groups
    """
    repeating_skill_groups = []
    timed_skill_groups = []
    seen_in_loop = []  # keep track of behaviour added to loops
    loop_data = turn_data.copy()
    # multi-turn loops
    loop_size = loop_end - loop_start
    if loop_size > 1:
        # remove any behaviour that occurs in all turns of the loop
        loop_data = remove_common_behaviour(loop_data, loop_start, loop_end)
        # add items to skill group
        for idx in range(loop_start, loop_end):
            if loop_data[idx] is not None:
                repeating_skill_groups.append(RepeatSkillGroup(idx + 1, loop_size, hp, loop_data[idx]))
                seen_in_loop.append(loop_data[idx])
    # pre-loop
    if loop_start > 0:
        remove_seen_behaviour(loop_data, 0, loop_start, seen_in_loop)
        for idx in range(loop_start):
            if loop_data[idx] is not None:
                timed_skill_groups.append(TimedSkillGroup(idx + 1, hp, loop_data[idx]))
                seen_in_loop.append(loop_data[idx])

    return repeating_skill_groups, timed_skill_groups, seen_in_loop


def extract_hp_groups(hp_ctx: Context, hp_checkpoints: Set[int], behaviors: List, globally_seen_behavior: List) -> Tuple[List[HpSkillGroup], List[Any]]:
    hp_skill_groups = []
    # Simulate HP decreasing
    for checkpoint in sorted(hp_checkpoints, reverse=True):
        locally_seen_behavior = []
        hp_ctx.hp = checkpoint
        cur_loop = loop_through(hp_ctx, behaviors)
        while cur_loop not in locally_seen_behavior:
            if cur_loop not in globally_seen_behavior:
                hp_skill_groups.append(HpSkillGroup(checkpoint, cur_loop))
            globally_seen_behavior.append(cur_loop)
            locally_seen_behavior.append(cur_loop)
            cur_loop = loop_through(hp_ctx, behaviors)

    return hp_skill_groups, globally_seen_behavior


def extract_enemy_remaining(ec_ctx: Context, hp_checkpoints: Set[int], behaviors: List[Any], globally_seen_behavior: List) -> List[EnemyCountSkillGroup]:
    results = []
    ec_data = {}
    for ecount in [999] + list(range(6, 0, -1)):
        ec_ctx.enemies = ecount
        current_ec_data = {}
        for checkpoint in sorted(hp_checkpoints, reverse=True):
            ec_ctx.hp = checkpoint
            cur_loop = loop_through(ec_ctx, behaviors)

            if cur_loop in globally_seen_behavior:
                continue

            current_ec_data[checkpoint] = cur_loop

            # # Check for the first action being one-time. Kind of a hacky special case for loops.
            # follow_loop = loop_through(ec_ctx, behaviors)
            # if follow_loop != cur_loop:
            #     ec_data[ecount].extend(follow_loop)

        if all([x != current_ec_data for ec, x in ec_data.items()]):
            ec_data[ecount] = current_ec_data

    # prune actions
    for ecount, loop in ec_data.items():
        if loop is None:
            continue
        # remove skillsets already seen from decreasing HP
        for hp, b_set in loop.copy().items():
            if b_set in globally_seen_behavior:
                loop.pop(hp)
        # remove skillsets found on more than 1 turn
        for comp_ecount, comp_loop in ec_data.items():
            if comp_loop is None:
                continue
            if ecount != comp_ecount and loop == comp_loop:
                ec_data[ecount] = None
                ec_data[comp_ecount] = None

    for ecount, loop in ec_data.items():
        if loop is None:
            continue
        for hp, b_set in loop.items():
            results.append(EnemyCountSkillGroup(ecount, hp, b_set))

    return results


def convert(card: BookCard, enemy_behavior: List, level: int, enemy_skill_effect: int, enemy_skill_effect_type: int):
    skillset = ProcessedSkillset(level)

    # Behavior is 1-indexed, so stick a fake row in to start
    behaviors = [None] + list(enemy_behavior)

    # Fix some monsters that seem to be 0-indexed
    if card.card_id in ZERO_INDEXED_MONSTERS:
        behaviors.pop(0)

    base_abilities, hp_checkpoints, card_checkpoints, has_enemy_remaining_branch = info_from_behaviors(
        behaviors)
    skillset.base_abilities = base_abilities

    # Pick the correct enemy_skill_effect model to use
    if enemy_skill_effect_type == 0:
        ctx = CTXBitmap(level, enemy_skill_effect)
    elif enemy_skill_effect_type == 1:
        ctx = CTXCounter(level, enemy_skill_effect)
    else:
        # ctx = Context(level)
        # For now fall back to the old context implementation to prevent errors in log.
        print('Incorrect context used')
        ctx = CTXBitmap(level, enemy_skill_effect)

    ctx, preemptives = extract_preemptives(ctx, behaviors)
    if ctx is None:
        # Some monsters have no skillset at all
        return skillset

    if preemptives is not None:
        skillset.preemptives = preemptives
        if any([p.ends_battle() for p in preemptives]):
            # This monster terminates the battle immediately.
            return skillset

    hp_turn_data, ctx = extract_turn_behaviors(ctx, behaviors, hp_checkpoints)
    globally_seen_behavior = []

    for hp in sorted(hp_turn_data.keys(), reverse=True):
        turn_data = hp_turn_data[hp]
        try:
            loop_start, loop_end = extract_loop_indexes(turn_data)
        except TypeError:
            continue
        repeating_skill_groups, timed_skill_groups, seen_in_loop = extract_loop_skills(hp, turn_data, loop_start, loop_end)
        skillset.repeating_skill_groups.extend(repeating_skill_groups)
        skillset.timed_skill_groups.extend(timed_skill_groups)
        globally_seen_behavior.extend(seen_in_loop)

    # Simulate HP decreasing
    hp_skill_groups, globally_seen_behavior = extract_hp_groups(ctx.clone(), hp_checkpoints, behaviors, globally_seen_behavior)
    skillset.hp_skill_groups.extend(hp_skill_groups)

    # Simulate enemies being defeated
    if has_enemy_remaining_branch:
        enemy_skill_groups = extract_enemy_remaining(ctx.clone(), hp_checkpoints, behaviors, globally_seen_behavior)
        skillset.enemycount_skill_groups.extend(enemy_skill_groups)

    return clean_skillset(skillset)


def extract_hp_threshold(es):
    """If the action has a HP threshold, extracts it."""
    if skill_has_condition(es):
        c = es.condition
        if hasattr(c, 'hp_threshold'):
            return c.hp_threshold
    return None


def collapse_repeating_groups(groups: List[TimedSkillGroup]) -> List[TimedSkillGroup]:
    """For repeating movesets, collapse consecutive repeats."""
    if len(groups) <= 1:
        # No work we can do here
        return groups

    cur_item = groups[0]
    new_groups = [cur_item]
    for idx in range(1, len(groups)):
        next_item = groups[idx]
        if cur_item.skills == next_item.skills and cur_item.turn != next_item.turn:
            cur_item.end_turn = next_item.turn
        else:
            new_groups.append(next_item)
            cur_item = next_item
    return new_groups


def clean_skillset(skillset: ProcessedSkillset):
    # Check to see if the skillset is functionally empty (only default actions). These are created
    # for some monsters with mostly empty/broken behavior.
    def clear_action(skills, action_type):
        skills[:] = [s for s in skills if type(s) != action_type]

    def clear_empty_group(group, action_type):
        for sg in group:
            clear_action(sg.skills, action_type)
        group[:] = [sg for sg in group if sg.skills]

    def clear_skillset(action_type):
        clear_empty_group(skillset.timed_skill_groups, action_type)
        clear_empty_group(skillset.repeating_skill_groups, action_type)
        clear_empty_group(skillset.enemycount_skill_groups, action_type)
        clear_empty_group(skillset.hp_skill_groups, action_type)

    clear_skillset(ESDefaultAttack)

    # Move ESAttackUpStatus to a special location, clear it out of any other buckets
    all_skills = pad_etl.processor.debug_utils.extract_used_skills(skillset)
    status_skills = [x for x in all_skills if type(x) == ESAttackUpStatus]
    if status_skills:
        skillset.status_action = status_skills[0]
        clear_skillset(ESAttackUpStatus)

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
            if extract_hp_threshold(es) and extract_hp_threshold(es) != hp_skills.hp:
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

    # Insert any extracted skills from the one-time/timed/repeating skillsets
    # back into the correct HP bucket.
    for es in extracted:
        hp_threshold = es.condition.hp_threshold
        placed = False
        for hp_group in skillset.hp_skill_groups:
            if hp_group.hp == hp_threshold:
                hp_group.skills.append(es)
                placed = True
                break
        if not placed:
            skillset.hp_skill_groups.append(HpSkillGroup(hp_threshold, [es]))

    # Now, starting from the max HP bucket and working our way down, identify the
    # current 'default' moveset (any items with no condition attached). If we find
    # that moveset in another bucket, remove it. If we find a new moveset, replace it.
    def extract_moveset(hp_group):
        return [s for s in hp_group.skills if not skill_has_nonpct_condition(s)]

    if skillset.hp_skill_groups:
        cur_moveset = extract_moveset(skillset.hp_skill_groups[0])
        for hp_group in skillset.hp_skill_groups[1:]:
            check_moveset = extract_moveset(hp_group)
            if check_moveset == cur_moveset:
                for move in cur_moveset:
                    hp_group.skills.remove(move)
            elif check_moveset:
                cur_moveset = check_moveset

    # Iterate over every skillset group and remove now-empty ones
    def filter_empty(group: List[StandardSkillGroup]):
        return [x for x in group if x.skills]

    skillset.timed_skill_groups = filter_empty(skillset.timed_skill_groups)
    skillset.repeating_skill_groups = filter_empty(skillset.repeating_skill_groups)
    skillset.enemycount_skill_groups = filter_empty(skillset.enemycount_skill_groups)
    skillset.hp_skill_groups = filter_empty(skillset.hp_skill_groups)

    # Ensure HP groups are sorted properly
    skillset.hp_skill_groups.sort(key=lambda x: x.hp, reverse=True)

    # Collapse unnecessary outputs
    skillset.timed_skill_groups = collapse_repeating_groups(skillset.timed_skill_groups)
    skillset.repeating_skill_groups = collapse_repeating_groups(skillset.repeating_skill_groups)

    return skillset


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


def skill_has_nonpct_condition(es):
    """Detects if a skill activates always or on a %, vs onetime/thresholded."""
    if not skill_has_condition(es):
        return False
    # Is checking the threshold here right? Maybe it should just be checking one_time.
    # Or maybe it's redundant.
    return es.condition.hp_threshold or es.condition.one_time


def skill_has_condition(es):
    if not hasattr(es, 'condition'):
        return False
    return es.condition is not None
