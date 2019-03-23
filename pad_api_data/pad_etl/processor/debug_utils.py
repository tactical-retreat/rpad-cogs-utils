from typing import List

from pad_etl.processor.enemy_skillset import ESAction
from pad_etl.processor.enemy_skillset_processor import ProcessedSkillset, StandardSkillGroup
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


def extract_used_skills(skillset: ProcessedSkillset) -> List[ESAction]:
    """Flattens a ProcessedSkillset to a list of actions"""
    results = []
    results.extend(skillset.preemptives)

    def sg_extract(l: List[StandardSkillGroup]) -> List[ESAction]:
        return [item for sublist in l for item in sublist.skills]

    results.extend(sg_extract(skillset.timed_skill_groups))
    results.extend(sg_extract(skillset.repeating_skill_groups))
    results.extend(sg_extract(skillset.hp_skill_groups))
    results.extend(sg_extract(skillset.enemycount_skill_groups))
    if skillset.status_action:
        results.append(skillset.status_action)

    return results