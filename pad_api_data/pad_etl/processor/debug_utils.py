from pad_etl.processor.enemy_skillset_processor import ProcessedSkillset
from .enemy_skillset import *


def dump_obj(o):
    """Dump enemy behavior to a string."""
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
        msg += '{} [{}] {}'.format(type(o).__name__, o.name, o.full_description())
        return msg

# I don't remember why we have two of these =(
def dump_obj2(o):
    if isinstance(o, ESSkillSet):
        msg = 'SkillSet:'
        msg += '\n\tCondition: {}'.format(json.dumps(o.condition,
                                                     sort_keys=True, default=lambda x: x.__dict__))
        for idx, behavior in enumerate(o.skill_list):
            msg += '\n\t{} {} {}'.format(idx, type(behavior).__name__,
                                         json.dumps(behavior, sort_keys=True, default=lambda x: x.__dict__))
        return msg
    else:
        return '{} {}'.format(type(o).__name__, json.dumps(o, sort_keys=True, default=lambda x: x.__dict__))


def simple_dump_obj(o):
    if isinstance(o, ESSkillSet):
        msg = 'SkillSet:'
        if o.condition.description:
            msg += '\n\tCondition: {}'.format(o.condition.description)
        for idx, behavior in enumerate(o.skill_list):
            msg += '\n\t[{}] {} -> {}\n\t{}'.format(
                idx, type(behavior).__name__, behavior.name, behavior.description)
        return msg
    else:
        msg = '{} -> {}'.format(type(o).__name__, o.name)
        if hasattr(o, 'condition'):
            if o.condition.description:
                msg += '\nCondition: {}'.format(o.condition.description)
        msg += '\n{}'.format(o.description)
        return msg


# This seems unused?
def dump_skillset(o: ProcessedSkillset):
    msg = 'ProcessedSkillset'

    msg += '\nBase:'
    for x in o.base_abilities:
        msg += '\n' + dump_obj(x)

    msg += '\n\nPreemptives:'
    for x in o.preemptives:
        msg += '\n' + dump_obj(x)

    msg += '\n\nTimed Groups:'
    for x in o.timed_skill_groups:
        msg += '\n\nTurn {}'.format(x.turn)
        if x.hp is not None and x.hp < 100:
            msg += ' (HP <= {})'.format(x.hp)
        for y in x.skills:
            msg += '\n{}'.format(dump_obj(y))

    msg += '\n\nRepeating Groups:'
    for x in o.repeating_skill_groups:
        msg += '\n\nTurn {}'.format(x.turn)
        if x.hp is not None and x.hp < 100:
            msg += ' (HP <= {})'.format(x.hp)
        for y in x.skills:
            msg += '\n{}'.format(dump_obj(y))

    msg += '\n\nEnemyCount Groups:'
    for x in o.enemycount_skill_groups:
        msg += '\n\nEnemies {}'.format(x.count)
        for y in x.skills:
            msg += '\n{}'.format(dump_obj(y))

    msg += '\n\nHP Groups:'
    for x in o.hp_skill_groups:
        msg += '\n\nHP Ceiling {}'.format(x.hp_ceiling)
        for y in x.skills:
            msg += '\n{}'.format(dump_obj(y))

    return msg
