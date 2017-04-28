import cv2

from extractor import IMAGE_FOLDER
from padvision import padvision


ORB_SET_LOCK_BOTH = [
    'rbgldh',
    'jpmbhb',
    'blbrhg',
    'hrhlrh',
    'llbdhh',
]

ORB_SET_PLAIN_PLUS = [
    'rbgldh',
    'jpmhrg',
    'glgrdh',
    'dlrggr',
    'mmllgd',
]

IN_ATTACK = [
    'ddhbhg',
    'hbdrdb',
    'bdhdbg',
    'drglrl',
    'bdgrbr',
]

MOSTLY_DARK = [
    'dgdddd',
    'dddddd',
    'dddddd',
    'gddddd',
    'dgdddd',
]

BLUE_AS_LIGHT = [
    'ddrbdr',
    'bhrlbl',  # 1,4 should be blue but it comes out light
    'gdbhdg',
    'llhghg',
    'rhhgbd',
]

LIGHT_AS_RED = [
    'blgldr',
    'ghhrgg',
    'rdhdrb',
    'ldbrbl',
    'llhbdh',
]  # 4,0 should be light but it comes out red

BOMBS = [
    'odgggo',
    'dorloj',
    'bjlhbr',
    'hohgol',
    'ojdrbo',
]

DARK_ORB_SET = [
    'lbhlhl',
    'brhblh',
    'hlrjbb',
    'pmjhbj',
    'rbgldh',
]

VALIDATION_IMAGES = {
    'cb_both.png' : ORB_SET_LOCK_BOTH,
    'cb_lock.png' : ORB_SET_LOCK_BOTH,
    'cb_plain.png' : ORB_SET_PLAIN_PLUS,
    'cb_plus.png' : ORB_SET_PLAIN_PLUS,

    'std_both.png' : ORB_SET_LOCK_BOTH,
    'std_lock.png' : ORB_SET_LOCK_BOTH,
    'std_plain.png' : ORB_SET_PLAIN_PLUS,
    'std_plus.png' : ORB_SET_PLAIN_PLUS,
#     'in_attack.png' : IN_ATTACK, # disabled because it's not going to work
    'mostly_dark.png' : MOSTLY_DARK,
    'blue_as_light.png' : BLUE_AS_LIGHT,

    'bombs.png' : BOMBS,

    'dark_cb_plain.png' : DARK_ORB_SET,
    'dark_cb_plus.png' : DARK_ORB_SET,

    'dark_std_plain.png' : DARK_ORB_SET,
    'dark_std_plus.png' : DARK_ORB_SET,
}


# orb_folder = 'alt_orb_images'
orb_folder = 'orb_images'
orb_type_to_images = padvision.load_orb_images_dir_to_map(orb_folder)

failure_count = 0

for f, dat in VALIDATION_IMAGES.items():
    print('starting on', f)

    img = cv2.imread('./{}/{}'.format(IMAGE_FOLDER, f))

    extractor = padvision.SimilarityBoardExtractor(orb_type_to_images, img)
    board = extractor.get_board()
    similarity = extractor.get_similarity()

    for y, x in padvision.board_iterator():
        expected_orb = dat[y][x]
        matched_orb = board[y][x]
        matched_similarity = similarity[y][x]
#         print(matched_similarity)
        if expected_orb != matched_orb:
            failure_count += 1
            print('failure in {} expected {} got {} at {},{} similarity {}'.format(f, expected_orb, matched_orb, y, x, matched_similarity))

print("failure count:", failure_count)