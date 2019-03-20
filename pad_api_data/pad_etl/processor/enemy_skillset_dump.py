from enum import Enum, auto
from typing import List, Optional, TextIO, Union
import os
import yaml

from pad_etl.processor import debug_utils
from pad_etl.processor.enemy_skillset_processor import ProcessedSkillset
from ..data.card import BookCard
from .enemy_skillset import *


class RecordType(Enum):
    """Describes the type of record being stored.

    Has no practical use for DadGuide but it might be useful for other apps.
    """
    # Resist, resolve
    PASSIVE = auto()
    # Actions that happen on the first turn
    PREEMPT = auto()
    # Description-only visual separation aids
    DIVIDER = auto()
    # Any kind of action, could be multiple enemy skills compounded into one
    ACTION = auto()
    # An action that increases enemy damage
    ENRAGE = auto()
    # Generic operator-supplied text placeholder, probably description-only
    TEXT = auto()


class SkillRecord(yaml.YAMLObject):
    """A skill line item, placeholder, or other text."""
    yaml_tag = u'!SkillRecord'

    def __init__(self, record_type=RecordType.TEXT, name_en='', name_jp='', desc_en='', desc_jp='', min_atk_pct=None,
                 max_atk_pct=None, usage_pct=100, one_time=False):
        self.record_type_name = record_type.name
        # For actions, the name that is displayed in-game.
        # For dividers, contains the divider text.
        self.name_en = name_en
        self.name_jp = name_jp
        # A description of what occurs when this skill is triggered.
        self.desc_en = desc_en
        self.desc_jp = desc_jp
        # None if no attack, or the damage % expressed as an integer.
        # e.g. 100 for one hit with normal damage, 200 for two hits with normal damage,
        # 300 for one hit with 3x damage.
        self.max_atk_pct = min_atk_pct
        self.max_atk_pct = max_atk_pct
        # Likelihood of this action occurring, 0 < usage_pct <= 100.
        self.usage_pct = usage_pct
        # If the action only executes once.
        self.one_time = one_time


class SkillRecordListing(yaml.YAMLObject):
    """Group of skills that explain how an enemy behaves.

    Level is used to distinguish between different sets of skills based on the specific dungeon.
    """
    yaml_tag = u'!SkillRecordListing'

    def __init__(self, level: int, records: List[SkillRecord], overrides: List[SkillRecord] = None):
        self.level = level
        self.records = records
        self.overrides = overrides or []


class EntryInfo(yaml.YAMLObject):
    """Extra info about the entry."""
    yaml_tag = u'!EntryInfo'

    def __init__(self,
                 monster_id: int, monster_name_en: str, monster_name_jp: str,
                 reviewed_by='unreviewed', comments: str = None):
        self.monster_id = monster_id
        self.monster_name_en = monster_name_en
        self.monster_name_jp = monster_name_jp
        self.reviewed_by = reviewed_by
        self.comments = comments
        self.warnings = []  # List[str]


class EnemySummary(object):
    """Describes all the variations of an enemy."""

    def __init__(self, info: EntryInfo = None, data: List[SkillRecordListing] = None):
        self.info = info
        self.data = data or []

    def data_for_level(self, level: int) -> Optional[SkillRecordListing]:
        if not self.data:
            return None

        viable_levels = [d.level for d in self.data if level >= d.level]
        if not viable_levels:
            return None

        selected_level = min(viable_levels)
        return next(filter(lambda d: d.level == selected_level, self.data))


def behavior_to_skillrecord(record_type: RecordType, action: Union[ESAction, ESLogic]) -> SkillRecord:
    name = action.name
    description = action.full_description()
    min_damage = None
    max_damage = None
    usage_pct = 100
    one_time = False
    if type(action) == ESSkillSet:
        name = ' + '.join(map(lambda s: s.name, action.skill_list))
        description = ' + '.join(map(lambda s: s.description, action.skill_list))

    if issubclass(type(action), ESPassive):
        name = 'Ability'

    if type(action) in [ESPreemptive, ESAttackPreemptive]:
        name = 'Preemptive'
    elif record_type == RecordType.PREEMPT:
        description += ' (Preemptive)'

    attack = getattr(action, 'attack', None)
    if attack is not None:
        min_damage = attack.min_damage_pct()
        max_damage = attack.max_damage_pct()

    cond = getattr(action, 'condition', None)
    if cond is not None:
        usage_pct = max(cond.ai, cond.rnd)
        if cond.one_time:
            one_time = True

    return SkillRecord(record_type=record_type,
                       name_en=name,
                       name_jp=name,
                       desc_en=description,
                       desc_jp=description,
                       max_atk_pct=max_damage,
                       min_atk_pct=min_damage,
                       usage_pct=usage_pct,
                       one_time=one_time)


def create_divider(divider_text: str) -> SkillRecord:
    return SkillRecord(record_type=RecordType.DIVIDER, name_en=divider_text, name_jp=divider_text, desc_en='',
                       desc_jp='')


def flatten_skillset(level: int, skillset: ProcessedSkillset) -> SkillRecordListing:
    records = []  # List[SkillRecord]

    for item in skillset.base_abilities:
        records.append(behavior_to_skillrecord(RecordType.PASSIVE, item))

    for item in skillset.preemptives:
        records.append(behavior_to_skillrecord(RecordType.PREEMPT, item))

    for idx, item in enumerate(skillset.timed_skill_groups):
        records.append(create_divider('Turn {}'.format(item.turn)))
        for sub_item in item.skills:
            records.append(behavior_to_skillrecord(RecordType.ACTION, sub_item))

    for item in skillset.enemycount_skill_groups:
        header = 'When {} enemy remains'.format(item.count)
        if item.hp != 100:
            header += ' and HP <= {}'.format(item.hp)
        records.append(create_divider(header))
        for sub_item in item.skills:
            records.append(behavior_to_skillrecord(RecordType.ACTION, sub_item))

    for item in skillset.hp_skill_groups:
        records.append(create_divider('HP <= {}'.format(item.hp_ceiling)))
        for sub_item in item.skills:
            records.append(behavior_to_skillrecord(RecordType.ACTION, sub_item))

    if skillset.repeating_skill_groups:
        records.append(create_divider('Execute below actions in order repeatedly'))

    current_turn = 0
    for item in skillset.repeating_skill_groups:
        header = ''
        if item.turn != current_turn:
            header += 'Turn {}'.format(item.turn)
            current_turn = item.turn
        if item.hp != 100:
            header += ' HP <= {}'.format(item.hp)
        if len(header) > 0:
            records.append(create_divider(header))
        for sub_item in item.skills:
            records.append(behavior_to_skillrecord(RecordType.ACTION, sub_item))

    return SkillRecordListing(level=level, records=records)


def load_summary(monster_id: int) -> Optional[EnemySummary]:
    """Load an EnemySummary from disk, returning None if no data is available (probably an error)."""
    file_path = _file_by_id(monster_id)
    if not os.path.exists(file_path):
        return None

    with open(file_path) as f:
        line = _consume_comments(f)

        entry_info_data = []
        while not line.startswith('#'):
            entry_info_data.append(line)
            line = f.readline()

        all_listings = []
        while line:
            line = _consume_comments(f, initial_line=line)

            cur_listing_data = []
            while line and not line.startswith('#'):
                cur_listing_data.append(line)
                line = f.readline()

            if cur_listing_data:
                all_listings.append(cur_listing_data)

    enemy_info = yaml.load(''.join(entry_info_data), Loader=yaml.Loader)
    enemy_info.warnings = []
    enemy_summary = EnemySummary(enemy_info)
    enemy_summary.data = [yaml.load(''.join(x), Loader=yaml.Loader) for x in all_listings]

    return enemy_summary


def _consume_comments(f: TextIO, initial_line=None) -> str:
    line = initial_line or f.readline()
    while line and line.startswith('#'):
        line = f.readline()
    return line


def load_and_merge_summary(enemy_summary: EnemySummary) -> EnemySummary:
    """Loads any stored data from disk and merges with the supplied summary."""
    saved_summary = load_summary(enemy_summary.info.monster_id)
    if saved_summary is None:
        return enemy_summary

    # Merge any new items into the stored summary.
    for attr, new_value in enemy_summary.info.__dict__.items():
        stored_value = getattr(saved_summary.info, attr)
        if new_value is not None and stored_value is None:
            setattr(saved_summary.info, attr, new_value)

    listings_by_level = {x.level: x for x in saved_summary.data}
    overrides_exist = any(map(lambda x: len(x.overrides), saved_summary.data))

    # Update stored data with newly computed data.
    for computed_listing in enemy_summary.data:
        stored_listing = listings_by_level.get(computed_listing.level, None)
        if stored_listing is None:
            # No existing data was found.
            stored_listing = computed_listing
            saved_summary.data.append(computed_listing)
        else:
            # Found existing data so just update the computed part
            stored_listing.records = computed_listing.records

        # There were overrides in general but not on this item (probably because it is new).
        if overrides_exist and not stored_listing.overrides:
            saved_summary.info.warnings.append(
                'Override missing for {}'.format(computed_listing.level))

    return saved_summary


def dump_summary_to_file(card: BookCard, enemy_summary: EnemySummary, enemy_behavior: List):
    """Writes the enemy info, actions by level, and enemy behavior to a file."""
    file_path = _file_by_id(enemy_summary.info.monster_id)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('{}\n'.format(_header('Info')))
        f.write('{}\n'.format(yaml.dump(enemy_summary.info, default_flow_style=False)))
        for listing in enemy_summary.data:
            f.write('{}\n'.format(_header('Data @ {}'.format(listing.level))))
            f.write('{}\n'.format(yaml.dump(listing, default_flow_style=False)))

        f.write('{}\n'.format(_header('ES Modifiers')))
        f.write('# [{}] {} - {:8b}\n'.format(9, card.unknown_009, card.unknown_009))
        f.write('# [{}] {}\n'.format(52, 'true' if card.unknown_052 else 'false'))
        f.write('# [{}] {} - {:8b}\n'.format(53, card.enemy_skill_effect, card.enemy_skill_effect))
        f.write('# [{}] {}\n'.format(54, card.enemy_skill_effect_type))
        f.write('# 53 is enemy_skill_modifier\n')
        f.write('# 54 is enemy_skill_modifier_type\n')

        f.write('#\n')

        if enemy_behavior:
            f.write('{}\n'.format(_header('Raw Behavior')))
            for idx, behavior in enumerate(enemy_behavior):
                behavior_str = debug_utils.simple_dump_obj(behavior)
                behavior_str = behavior_str.replace('\n', '\n# ').rstrip('#').rstrip()
                f.write('# [{}] {}\n'.format(idx + 1, behavior_str, '\n'))


def _header(header_text: str) -> str:
    return '\n'.join([
        '#' * 60,
        '#' * 3 + ' {}'.format(header_text),
        '#' * 60,
    ])


def _file_by_id(monster_id):
    return os.path.join(os.path.dirname(__file__), 'enemy_data', '{}.yaml'.format(monster_id))


def load_summary_as_dump_text(card: BookCard, monster_level: int, dungeon_atk_modifier: float):
    """Produce a textual description of enemy behavior.

    Loads the enemy summary from disk, identifies the behavior appropriate for the level,
    and converts it into human-friendly output.
    """
    monster_id = card.card_id
    summary = load_summary(monster_id)
    if not summary:
        return 'Basic attacks (1)\n'

    skill_data = summary.data_for_level(monster_level)
    if not skill_data:
        return 'Basic attacks (2)\n'

    enemy_info = skill_data.overrides or skill_data.records
    if not enemy_info:
        return 'Basic attacks (3)\n'

    atk = card.enemy().atk.value_at(monster_level)
    atk *= dungeon_atk_modifier
    msg = ''
    for row in enemy_info:
        header = row.name_en
        if row.record_type_name == 'DIVIDER':
            header = '{} {} {}'.format('-' * 5, header, '-' * 5)

        desc = row.desc_en
        if row.max_atk_pct:
            desc = '{} Damage - {}'.format(int(row.max_atk_pct * atk / 100), desc)
        if row.usage_pct not in [100, 0]:
            desc += ' ({}% chance)'.format(row.usage_pct)
        if row.one_time:
            desc += ' (1 time use)'
        msg += header + '\n'
        if desc:
            msg += desc + '\n'

    return msg
