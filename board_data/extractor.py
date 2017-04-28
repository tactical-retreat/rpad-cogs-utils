from collections import defaultdict

import cv2

from padvision import padvision


FIRST_ORB_SET = ['rbgldh',
                 'jpm...',
                 '......',
                 '......',
                 '......']

BLUE_AS_LIGHT = [
    '......',
    '....b.',  # 1,4 should be blue but it comes out light
    '......',
    '......',
    '......',
]
LIGHT_AS_RED = [
    '......',
    '......',
    '......',
    '......',
    'l.....',
]  # 4,0 should be light but it comes out red

BOMBS = [
    'o....o',
    '.o..o.',
    '......',
    '.o..o.',
    'o....o',
]

DARK_ORB_SET = [
    '......',
    '......',
    '......',
    'pmj...',
    'rbgldh',
]

IMAGES = {
    'cb_both.png' : FIRST_ORB_SET,
    'cb_lock.png' : FIRST_ORB_SET,
    'cb_plain.png' : FIRST_ORB_SET,
    'cb_plus.png' : FIRST_ORB_SET,

    'std_both.png' : FIRST_ORB_SET,
    'std_lock.png' : FIRST_ORB_SET,
    'std_plain.png' : FIRST_ORB_SET,
    'std_plus.png' : FIRST_ORB_SET,

    'blue_as_light.png' : BLUE_AS_LIGHT,
    'light_as_red.png' : LIGHT_AS_RED,

    'bombs.png' : BOMBS,

    'dark_cb_plain.png' : DARK_ORB_SET,
    'dark_cb_plus.png' : DARK_ORB_SET,

    'dark_std_plain.png' : DARK_ORB_SET,
    'dark_std_plus.png' : DARK_ORB_SET,
}

IMAGE_FOLDER = 'board_images'

def do_extraction():
    for f, dat in IMAGES.items():
        print('processing', f)
        img = cv2.imread('./board_images/' + f)
        oe = padvision.OrbExtractor(img)
        type_to_count = defaultdict(int)
        for y, x in padvision.board_iterator():
            orb_title = dat[y][x]
            type_to_count[orb_title] += 1
            if orb_title in padvision.EXTRACTABLE:
                orb_img = oe.get_orb_img(x, y)
                output_file = './orb_images/{}_{}_{}'.format(orb_title, type_to_count[orb_title], f)
                cv2.imwrite(output_file, orb_img)

if __name__ == '__main__':
    do_extraction()
