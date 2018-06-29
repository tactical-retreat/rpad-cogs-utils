"""
Parses card data.
"""

import json
import os

from typing import List, Any
from ..common.shared_types import AttrId, CardId, SkillId, TypeId

# The typical JSON file name for this data.
FILE_NAME = 'download_card_data.json'


class BookCard(json.JSONEncoder):
    """Data about a player-ownable monster."""

    def __init__(self, raw: List[Any]):
        unflatten(raw, 57, 3, replace=True)
        unflatten(raw, 58, 1, replace=True)
#         unflatten(raw, 59, 1, replace=True)

        self.card_id = CardId(raw[0])
        self.name = str(raw[1])
        self.attr_id = AttrId(raw[2])
        self.sub_attr_id = AttrId(raw[3])
        self.is_ult = bool(raw[4])
        self.type_1_id = TypeId(raw[5])
        self.type_2_id = TypeId(raw[6])
        self.rarity = int(raw[7])
        self.cost = int(raw[8])
        self.unknown_009 = raw[9]
        self.max_level = int(raw[10])
        self.feed_xp_at_lvl_4 = int(raw[11])
        self.unknown_012 = raw[12]
        self.released_status = raw[13]
        self.sell_price_at_lvl_10 = raw[14]

        self.min_hp = int(raw[15])
        self.max_hp = int(raw[16])
        self.hp_exponent = float(raw[17])

        self.min_atk = int(raw[18])
        self.max_atk = int(raw[19])
        self.atk_exponent = float(raw[20])

        self.min_rcv = int(raw[21])
        self.max_rcv = int(raw[22])
        self.rcv_exponent = float(raw[23])

        self.xp_max = int(raw[24])
        self.xp_gr = float(raw[25])

        self.active_skill_id = SkillId(raw[26])
        self.leader_skill_id = SkillId(raw[27])

        self.enemy_turns = int(raw[28])

        self.enemy_hp_1 = int(raw[29])
        self.enemy_hp_10 = int(raw[30])
        self.enemy_hp_gr = float(raw[31])

        self.enemy_atk1 = int(raw[32])
        self.enemy_at_k10 = int(raw[33])
        self.enemy_atk_gr = float(raw[34])

        self.enemy_def_1 = int(raw[35])
        self.enemy_def_10 = int(raw[36])
        self.enemy_def_gr = float(raw[37])

        self.enemy_coins_at_lvl_2 = int(raw[38])
        self.enemy_xp_at_lvl_2 = int(raw[39])

        self.ancestor_id = CardId(raw[40])

        self.evo_mat_id_1 = CardId(raw[41])
        self.evo_mat_id_2 = CardId(raw[42])
        self.evo_mat_id_3 = CardId(raw[43])
        self.evo_mat_id_4 = CardId(raw[44])
        self.evo_mat_id_5 = CardId(raw[45])

        self.un_evo_mat_1 = CardId(raw[46])
        self.un_evo_mat_2 = CardId(raw[47])
        self.un_evo_mat_3 = CardId(raw[48])
        self.un_evo_mat_4 = CardId(raw[49])
        self.un_evo_mat_5 = CardId(raw[50])

        self.unknown_051 = raw[51]
        self.unknown_052 = raw[52]
        self.unknown_053 = raw[53]
        self.unknown_054 = raw[54]
        self.unknown_055 = raw[55]
        self.unknown_056 = raw[56]

        self.eskills = raw[57]  # List[int]

        self.awakenings = raw[58]  # List[int]
        self.super_awakenings = raw[59]  # Needs unpacking?

        self.base_id = CardId(raw[60])  # ??
        self.group_id = raw[61]  # ??
        self.type_3_id = TypeId(raw[62])

        self.sell_mp = int(raw[63])
        self.latent_on_feed = int(raw[64])
        self.unknown_066 = raw[65]  # Might be which collab

        self.random_flags = raw[66]
        self.inheritable = bool(self.random_flags & 1)
        self.is_released = bool(self.random_flags & 2)
        self.is_collab = bool(self.random_flags & 4)

        self.furigana = str(raw[67])  # JP data only?
        self.limit = int(raw[68])

        self.other_fields = raw[69:]

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return 'Card({} - {})'.format(self.card_id, self.card_name)


def unflatten(raw: List[Any], idx: int, width: int, replace: bool=False):
    """Unflatten a card array.

    Index is the slot containing the item count.
    Width is the number of slots per item.
    If replace is true, values are moved into an array at idx.
    If replace is false, values are deleted.
    """
    item_count = raw[idx]
    if item_count == 0:
        return

    data_start = idx + 1
    flattened_item_count = width * item_count
    flattened_data_slice = slice(data_start, data_start + flattened_item_count)

    data = list(raw[flattened_data_slice])
    del raw[flattened_data_slice]

    if replace:
        raw[idx] = data


def load_card_data(data_dir: str=None, card_json_file: str=None) -> List[BookCard]:
    """Load BookCard objects from PAD JSON file."""
    if card_json_file is None:
        card_json_file = os.path.join(data_dir, FILE_NAME)

    with open(card_json_file) as f:
        card_json = json.load(f)

    if card_json['v'] != 1250:
        raise NotImplementedError('version: {}'.format(card_json['v']))

    return [BookCard(r) for r in card_json['card']]
