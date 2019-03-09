from enum import Enum, auto
from typing import List
import os
import yaml


from .enemy_skillset_processor import SkillItem, ProcessedSkillset
from . import enemy_skillset_processor
from . import enemy_skillset


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

    def __init__(self,
                 record_type=RecordType.TEXT,
                 name_en='', name_jp='',
                 desc_en='', desc_jp=''):
        self.record_type_name = record_type.name
        self.name_en = name_en
        self.name_jp = name_jp
        self.desc_en = desc_en
        self.desc_jp = desc_jp


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


def skillitem_to_skillrecord(record_type: RecordType, es_item: any) -> SkillRecord:
    skill_item = enemy_skillset_processor.to_item(es_item)
    return SkillRecord(record_type=record_type,
                       name_en=skill_item.name,
                       name_jp=skill_item.name,
                       desc_en=skill_item.comment,
                       desc_jp=skill_item.comment)


def create_divider(divider_text: str) -> SkillRecord:
    return SkillRecord(record_type=RecordType.DIVIDER,
                       name_en=divider_text,
                       name_jp='',
                       desc_en=divider_text,
                       desc_jp='')


def flatten_skillset(level: int, skillset: ProcessedSkillset) -> SkillRecordListing:
    records = []  # List[SkillRecord]

    for item in skillset.base_abilities:
        records.append(skillitem_to_skillrecord(RecordType.PASSIVE, item))

    for item in skillset.preemptives:
        records.append(skillitem_to_skillrecord(RecordType.PREEMPT, item))

    for idx, item in enumerate(skillset.timed_skill_groups):
        records.append(create_divider('Turn {}'.format(item.turn)))
        for sub_item in item.skills:
            records.append(skillitem_to_skillrecord(RecordType.ACTION, sub_item))

    for item in skillset.enemycount_skill_groups:
        records.append(create_divider('When {} enemy remains'.format(item.count)))
        for sub_item in item.skills:
            records.append(skillitem_to_skillrecord(RecordType.ACTION, sub_item))

    for item in skillset.hp_skill_groups:
        records.append(create_divider('HP <= {}'.format(item.hp_ceiling)))
        for sub_item in item.skills:
            records.append(skillitem_to_skillrecord(RecordType.ACTION, sub_item))

    return SkillRecordListing(level=level, records=records)


def load_summary(enemy_summary: EnemySummary) -> EnemySummary:
    file_path = _file_by_id(enemy_summary.info.monster_id)
    if not os.path.exists(file_path):
        return enemy_summary

    with open(file_path) as f:
        line = f.readline()
        while line.startswith('#'):
            line = f.readline()

        entry_info_data = []
        while not line.startswith('#'):
            entry_info_data.append(line)
            line = f.readline()

        all_listings = []
        while True:
            if line is None:
                break

            while line.startswith('#'):
                line = f.readline()

            cur_listing_data = []
            while line is not None and not line.startswith('#'):
                cur_listing_data.append(line)
                line = f.readline()
            all_listings.append(cur_listing_data)

    enemy_summary.info = yaml.load('\n'.join(entry_info_data))
    enemy_summary.info.warnings = []

    listings = [yaml.load('\n'.join(x) for x in all_listings)]
    listings_by_level = {x.level: x for x in listings}
    listings_have_overrides = any(map(lambda x: len(x.overrides), listings))

    for computed_listing in enemy_summary.data:
        stored_listing = listings_by_level.get(computed_listing.level, None)
        if stored_listing is None and listings_have_overrides:
            enemy_summary.info.warnings.append(
                'Override missing for {}'.format(computed_listing.level))
        else:
            computed_listing.overrides = stored_listing.overrides

    return enemy_summary


def dump_summary_to_file(enemy_summary: EnemySummary, enemy_behavior=None):
    file_path = _file_by_id(enemy_summary.info.monster_id)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('{}\n'.format(_header('Info')))
        f.write('{}\n'.format(yaml.dump(enemy_summary.info, default_flow_style=False)))
        for listing in enemy_summary.data:
            f.write('{}\n'.format(_header('Data @ {}'.format(listing.level))))
            f.write('{}\n'.format(yaml.dump(listing, default_flow_style=False)))

        if enemy_behavior:
            f.write('{}\n'.format(_header('Raw Behavior')))
            for idx, behavior in enumerate(enemy_behavior):
                behavior_str = enemy_skillset.simple_dump_obj(behavior)
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
