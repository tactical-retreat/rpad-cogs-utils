import json
import logging
import os

from . import bonus, card, dungeon, skill, exchange, enemy_skill
from ..processor import enemy_skillset as enemy_skillset_lib
from ..processor.merged_data import MergedBonus, MergedCard, MergedEnemySkillset, MergedEnemy


# TODO move these into data dir
fail_logger = logging.getLogger('processor_failures')


def _clean_bonuses(pg_server, bonus_sets, dungeons):
    dungeons_by_id = {d.dungeon_id: d for d in dungeons}

    merged_bonuses = []
    for data_group, bonus_set in bonus_sets.items():
        for bonus in bonus_set:
            dungeon = None
            guerrilla_group = None
            if bonus.dungeon_id:
                dungeon = dungeons_by_id.get(bonus.dungeon_id, None)
                if dungeon is None:
                    fail_logger.critical('Dungeon lookup failed for bonus: %s', repr(bonus))
                else:
                    guerrilla_group = data_group if dungeon.dungeon_type == 'guerrilla' else None

            if guerrilla_group or data_group == 'red':
                merged_bonuses.append(MergedBonus(pg_server, bonus, dungeon, guerrilla_group))

    return merged_bonuses


def _clean_cards(cards, skills):
    skills_by_id = {s.skill_id: s for s in skills}

    merged_cards = []
    for card in cards:
        active_skill = None
        leader_skill = None

        if card.active_skill_id:
            active_skill = skills_by_id.get(card.active_skill_id, None)
            if active_skill is None:
                fail_logger.critical('Active skill lookup failed: %s - %s',
                                     repr(card), card.active_skill_id)

        if card.leader_skill_id:
            leader_skill = skills_by_id.get(card.leader_skill_id, None)
            if leader_skill is None:
                fail_logger.critical('Leader skill lookup failed: %s - %s',
                                     repr(card), card.leader_skill_id)

        merged_cards.append(MergedCard(card, active_skill, leader_skill))
    return merged_cards


def _clean_enemy(cards, enemy_skills):
    enemy_skill_by_id = {s.enemy_skill_id: s for s in enemy_skills}
    merged_enemies = []
    for card in cards:
        if len(card.enemy_skill_refs) == 0:
            continue

        enemy_skillset = []
        for esr in card.enemy_skill_refs:
            if enemy_skill_by_id.get(esr.enemy_skill_id) is None:
                print("Enemy skill not found: " + str(esr.enemy_skill_id))
                continue
            es = enemy_skill_by_id.get(esr.enemy_skill_id)
            es_set = None
            if es.type == 83:
                es_set = [enemy_skill_by_id.get(s_id) for s_id in es.params[1:11]
                          if s_id is not None and enemy_skill_by_id.get(s_id) is not None]
            enemy_skillset.append(MergedEnemySkillset(esr, es, es_set))

        behavior = enemy_skillset_lib.extract_behavior(enemy_skillset)
        merged_enemies.append(MergedEnemy(card.card_id, behavior))

    return merged_enemies


class Database(object):
    def __init__(self, pg_server, raw_dir):
        self.pg_server = pg_server
        self.base_dir = os.path.join(raw_dir, pg_server)

        # Loaded from disk
        self.raw_cards = []
        self.dungeons = []
        self.bonus_sets = {}
        self.skills = []
        self.enemy_skills = []
        self.exchange = []
        self.egg_machines = []

        # This is temporary for the integration of calculated skills
        self.raw_skills = []

        # Computed from other entries
        self.bonuses = []
        self.cards = []

    def load_database(self):
        base_dir = self.base_dir
        self.raw_cards = card.load_card_data(data_dir=base_dir)
        self.dungeons = dungeon.load_dungeon_data(data_dir=base_dir)
        self.bonus_sets = {
            'red': bonus.load_bonus_data(data_dir=base_dir, data_group='red'),
            'blue': bonus.load_bonus_data(data_dir=base_dir, data_group='blue'),
            'green': bonus.load_bonus_data(data_dir=base_dir, data_group='green'),
        }
        self.skills = skill.load_skill_data(data_dir=base_dir)
        self.raw_skills = skill.load_raw_skill_data(data_dir=base_dir)
        self.enemy_skills = enemy_skill.load_enemy_skill_data(data_dir=base_dir)
        self.exchange = exchange.load_data(data_dir=base_dir)

        # TODO move this to egg machines parser same as others
        with open(os.path.join(base_dir, 'egg_machines.json')) as f:
            self.egg_machines = json.load(f)

        self.bonuses = _clean_bonuses(self.pg_server, self.bonus_sets, self.dungeons)
        self.cards = _clean_cards(self.raw_cards, self.skills)
        self.enemies = _clean_enemy(self.raw_cards, self.enemy_skills)

    def save_all(self, output_dir: str, pretty: bool):
        def save(file_name: str, obj: object):
            output_file = os.path.join(output_dir, '{}_{}.json'.format(self.pg_server, file_name))
            with open(output_file, 'w') as f:
                if pretty:
                    json.dump(obj, f, indent=4, sort_keys=True, default=lambda x: x.__dict__)
                else:
                    json.dump(obj, f, sort_keys=True, default=lambda x: x.__dict__)
        save('raw_cards', self.raw_cards)
        save('dungeons', self.dungeons)
        save('skills', self.skills)
        save('enemy_skills', self.enemy_skills)
        save('bonuses', self.bonuses)
        save('cards', self.cards)
        save('exchange', self.exchange)
        save('enemies', self.enemies)
