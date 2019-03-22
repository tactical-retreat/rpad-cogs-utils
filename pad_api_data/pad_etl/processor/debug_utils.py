from .enemy_skillset import *


def simple_dump_obj(o):
    def fmt_cond(c):
        msg = 'Condition: {} (ai:{} rnd:{})'.format(c.description, c._ai, c._rnd)
        if c.one_time:
            msg += ' (one-time: {})'.format(c.one_time)
        return msg

    def fmt_action_name(a):
        return '{}({}:{}) -> {}'.format(type(a).__name__, a.type, a.enemy_skill_id, a.name)

    if isinstance(o, ESSkillSet):
        msg = 'SkillSet:'
        if o.condition.description:
            msg += '\n\t{}'.format(fmt_cond(o.condition))
        for idx, behavior in enumerate(o.skill_list):
            msg += '\n\t[{}] {}'.format(idx, fmt_action_name(behavior))
            msg += '\n\t{}'.format(behavior.description)
        return msg
    else:
        msg = fmt_action_name(o)
        if hasattr(o, 'condition') and o.condition.description:
            msg += '\n\t{}'.format(fmt_cond(o.condition))
        msg += '\n{}'.format(o.description)
        return msg
