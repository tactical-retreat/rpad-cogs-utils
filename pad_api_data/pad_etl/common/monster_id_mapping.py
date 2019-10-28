# Pad NA/JP don't have the exact same monster IDs for the same monster.
# PadGuide mostly uses the JP IDs, but mangles a few of them.
#
# This file documents the differences

# Shinra Bansho 1
# monster_no/monster_no_jp 669-670
# monster_no_us 934-935
#
# Shinra Bansho 2
# monster_no/monster_no_jp 671-680
# monster_no_us 1049-1058
#
# Batman 1
# monster_no/monster_no_jp 924-935
# monster_no_us 669-680
#
# Batman 2
# monster_no 9900-9909
# monster_no_jp 1049-1058
# monster_no_us 924-933
#
# Voltron
# monster_no 9601-9631
# monster_no_jp/monster_no_us 2601-2631
#
# Power Rangers
# monster_no 14949-14986
# monster_no_jp/monster_no_us 4949-4986

NA_VOLTRON_IDS = list(range(2601, 2632))
NA_POWERRANGER_IDS = list(range(4949, 4987))


def between(n, bottom, top):
    return n >= bottom and n <= top


def adjust(n, local_bottom, remote_bottom):
    return n - local_bottom + remote_bottom


def jp_id_to_na_id(jp_id):
    jp_id = int(jp_id)

    # Shinra Bansho 1
    if between(jp_id, 669, 670):
        return adjust(jp_id, 669, 934)

    # Shinra Bansho 2
    if between(jp_id, 671, 680):
        return adjust(jp_id, 671, 1049)

    # Batman 1
    if between(jp_id, 924, 935):
        return adjust(jp_id, 924, 669)

    # Batman 2
    if between(jp_id, 1049, 1058):
        return adjust(jp_id, 1049, 924)

    # Voltron
    if between(jp_id, 2601, 2631):
        return None

    # Voltron
    if between(jp_id, 4949, 4987):
        return None

    # Didn't match an exception, same card ID
    return jp_id


def jp_id_to_monster_no(jp_id):
    jp_id = int(jp_id)

    # Batman 2
    if between(jp_id, 1049, 1058):
        return adjust(jp_id, 1049, 9900)

    # Didn't match an exception, same card ID
    return jp_id


# NOTE this is incomplete only supports voltron for now
def na_id_to_monster_no(na_id):
    na_id = int(na_id)

    # Voltron
    if between(na_id, 2601, 2631):
        return adjust(na_id, 2601, 9601)

    # Power Rangers
    if between(na_id, 4949, 4987):
        return adjust(na_id, 4949, 14949)

    return None

    # raise NotImplementedError('only voltron/power rangers supported')
