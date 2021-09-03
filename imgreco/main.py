from fractions import Fraction

import numpy as np
from PIL import Image

from util.richlog import get_logger
from . import imgops
from . import resources
from . import util

logger = get_logger(__name__)


def check_main(img):
    vw, vh = util.get_vwvh(img.size)
    gear1 = img.crop((3.148 * vh, 2.037 * vh, 9.907 * vh, 8.796 * vh)).convert('L')
    gear2 = resources.load_image_cached('main/gear.png', 'L')
    gear1, gear2 = imgops.uniform_size(gear1, gear2)
    result = imgops.compare_ccoeff(gear1, gear2)
    # result = np.corrcoef(np.asarray(gear1).flat, np.asarray(gear2).flat)[0, 1]
    logger.logimage(gear1)
    logger.logtext('ccoeff=%f' % result)
    return result > 0.9


def get_ballte_corners(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (
            (61.120 * vw, 16.944 * vh), (82.213 * vw, 15.139 * vh), (82.213 * vw, 37.083 * vh),
            (61.120 * vw, 38.333 * vh))
    elif aspect == Fraction(18, 9):
        return (
            (64.693 * vw, 16.852 * vh), (82.378 * vw, 14.352 * vh), (82.378 * vw, 37.500 * vh),
            (64.693 * vw, 37.963 * vh))
    else:
        return [x[0] for x in imgops.find_homography(resources.load_image_cached('main/terminal.png', 'L'), img)]


def get_task_corners(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((55.602 * vw, 75.880 * vh)), np.array((70.367 * vw, 78.241 * vh)),
                np.array((70.367 * vw, 91.991 * vh)), np.array((55.602 * vw, 88.518 * vh)))
    elif aspect == Fraction(18, 9):
        return (np.array((58.489 * vw, 76.296 * vh)), np.array((72.008 * vw, 78.611 * vh)),
                np.array((72.008 * vw, 92.685 * vh)), np.array((58.489 * vw, 89.167 * vh)))
    else:
        return [x[0] for x in imgops.find_homography(resources.load_image_cached('main/quest.png', 'L'), img)]


# 以下几条用于访问好友基建
def get_friend_corners(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((22.734 * vw, 76.667 * vh)), np.array((33.203 * vw, 76.667 * vh)),
                np.array((33.203 * vw, 82.083 * vh)), np.array((22.734 * vw, 82.083 * vh)))
    else:
        return [x[0] for x in imgops.find_homography(resources.load_image_cached('main/friends.png', 'L'), img)]


def get_friend_list(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (
        np.array((1.484 * vw, 25.694 * vh)), np.array((16.797 * vw, 25.694 * vh)), np.array((16.797 * vw, 36.111 * vh)),
        np.array((1.484 * vw, 36.111 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


# 获得采购中心
def get_shopping_center(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((747 / 12.8 * vw, 421 / 7.2 * vh)), np.array((924 / 12.8 * vw, 421 / 7.2 * vh)),
                np.array((926 / 12.8 * vw, 538 / 7.2 * vh)), np.array((747 / 12.8 * vw, 532 / 7.2 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')

def get_building_button(img):#进入基建
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((921 / 12.8 * vw, 562 / 7.2 * vh)), np.array((1145 / 12.8 * vw, 579 / 7.2 * vh)),
                np.array((1137 / 12.8 * vw, 699 / 7.2 * vh)), np.array((921 / 12.8 * vw, 672 / 7.2 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


# 进入信用交易所
def get_credit_center(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((1095 / 12.8 * vw, 88 / 7.2 * vh)), np.array((1268 / 12.8 * vw, 87 / 7.2 * vh)),
                np.array((1266 / 12.8 * vw, 129 / 7.2 * vh)), np.array((1095 / 12.8 * vw, 126 / 7.2 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


# 领取信用
def get_credit_daily(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((965 / 12.8 * vw, 25 / 7.2 * vh)), np.array((1071 / 12.8 * vw, 24 / 7.2 * vh)),
                np.array((1073 / 12.8 * vw, 51 / 7.2 * vh)), np.array((965 / 12.8 * vw, 54 / 7.2 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


# 领取信用
def get_credit_item(img, index):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        credit_items = {1: (np.array((271 / 12.8 * vw, 148 / 7.2 * vh)), np.array((505 / 12.8 * vw, 154 / 7.2 * vh)),
                            np.array((499 / 12.8 * vw, 378 / 7.2 * vh)), np.array((266 / 12.8 * vw, 379 / 7.2 * vh))),
                        2: (np.array((526 / 12.8 * vw, 148 / 7.2 * vh)), np.array((756 / 12.8 * vw, 157 / 7.2 * vh)),
                            np.array((752 / 12.8 * vw, 379 / 7.2 * vh)), np.array((520 / 12.8 * vw, 375 / 7.2 * vh))),
                        3: (np.array((774 / 12.8 * vw, 148 / 7.2 * vh)), np.array((1004 / 12.8 * vw, 157 / 7.2 * vh)),
                            np.array((1001 / 12.8 * vw, 375 / 7.2 * vh)), np.array((780 / 12.8 * vw, 378 / 7.2 * vh))),
                        4: (np.array((1028 / 12.8 * vw, 154 / 7.2 * vh)), np.array((1259 / 12.8 * vw, 153 / 7.2 * vh)),
                            np.array((1256 / 12.8 * vw, 375 / 7.2 * vh)), np.array((1035 / 12.8 * vw, 376 / 7.2 * vh))),
                        5: (np.array((19 / 12.8 * vw, 408 / 7.2 * vh)), np.array((248 / 12.8 * vw, 409 / 7.2 * vh)),
                            np.array((250 / 12.8 * vw, 628 / 7.2 * vh)), np.array((20 / 12.8 * vw, 630 / 7.2 * vh))),

                        }
        return credit_items[index]
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')

def get_building_blocks(img, index):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        credit_items = {1: (np.array((125 / 12.8 * vw, 283 / 7.2 * vh)), np.array((271 / 12.8 * vw, 282 / 7.2 * vh)),
                            np.array((271 / 12.8 * vw, 351 / 7.2 * vh)), np.array((125 / 12.8 * vw, 354 / 7.2 * vh))),
                        2: (np.array((175 / 12.8 * vw, 261 / 7.2 * vh)), np.array((365 / 12.8 * vw, 265 / 7.2 * vh)),
                            np.array((361 / 12.8 * vw, 355 / 7.2 * vh)), np.array((173 / 12.8 * vw, 351 / 7.2 * vh))),

                        3: (np.array((404 / 12.8 * vw, 273 / 7.2 * vh)), np.array((557 / 12.8 * vw, 270 / 7.2 * vh)),
                            np.array((563 / 12.8 * vw, 339 / 7.2 * vh)), np.array((401 / 12.8 * vw, 340 / 7.2 * vh))),

                        4: (np.array((4 / 12.8 * vw, 382 / 7.2 * vh)), np.array((35 / 12.8 * vw, 379 / 7.2 * vh)),
                            np.array((31 / 12.8 * vw, 439 / 7.2 * vh)), np.array((6 / 12.8 * vw, 435 / 7.2 * vh))),

                        5: (np.array((92 / 12.8 * vw, 381 / 7.2 * vh)), np.array((245 / 12.8 * vw, 381 / 7.2 * vh)),
                            np.array((239 / 12.8 * vw, 447 / 7.2 * vh)), np.array((98 / 12.8 * vw, 445 / 7.2 * vh))),

                        6: (np.array((301 / 12.8 * vw, 388 / 7.2 * vh)), np.array((460 / 12.8 * vw, 399 / 7.2 * vh)),
                            np.array((449 / 12.8 * vw, 445 / 7.2 * vh)), np.array((308 / 12.8 * vw, 433 / 7.2 * vh))),

                        7: (np.array((41 / 12.8 * vw, 522 / 7.2 * vh)), np.array((41 / 12.8 * vw, 522 / 7.2 * vh)),
                            np.array((41 / 12.8 * vw, 522 / 7.2 * vh)), np.array((41 / 12.8 * vw, 522 / 7.2 * vh))),

                        8: (np.array((266 / 12.8 * vw, 523 / 7.2 * vh)), np.array((266 / 12.8 * vw, 523 / 7.2 * vh)),
                            np.array((266 / 12.8 * vw, 523 / 7.2 * vh)), np.array((266 / 12.8 * vw, 523 / 7.2 * vh))),
                        9: (np.array((478 / 12.8 * vw, 513 / 7.2 * vh)), np.array((478 / 12.8 * vw, 513 / 7.2 * vh)),
                            np.array((478 / 12.8 * vw, 513 / 7.2 * vh)), np.array((478 / 12.8 * vw, 513 / 7.2 * vh))),
                        # 中枢
                        10: (np.array((861 / 12.8 * vw, 153 / 7.2 * vh)), np.array((861 / 12.8 * vw, 153 / 7.2 * vh)),
                            np.array((861 / 12.8 * vw, 153 / 7.2 * vh)), np.array((861 / 12.8 * vw, 153 / 7.2 * vh))),
                        # 宿舍1
                        11: (np.array((812 / 12.8 * vw, 310 / 7.2 * vh)), np.array((812 / 12.8 * vw, 310 / 7.2 * vh)),
                            np.array((812 / 12.8 * vw, 310 / 7.2 * vh)), np.array((812 / 12.8 * vw, 310 / 7.2 * vh))),
                        # 宿舍2
                        12: (np.array((893 / 12.8 * vw, 418 / 7.2 * vh)), np.array((893 / 12.8 * vw, 418 / 7.2 * vh)),
                            np.array((893 / 12.8 * vw, 418 / 7.2 * vh)), np.array((893 / 12.8 * vw, 418 / 7.2 * vh))),
                        # 宿舍3
                        13: (np.array((785 / 12.8 * vw, 517 / 7.2 * vh)), np.array((785 / 12.8 * vw, 517 / 7.2 * vh)),
                            np.array((785 / 12.8 * vw, 517 / 7.2 * vh)), np.array((785 / 12.8 * vw, 517 / 7.2 * vh))),

                        }
        return credit_items[index]
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')



def get_credit_shopping_check(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):

        return (np.array((801 / 12.8 * vw, 556 / 7.2 * vh)), np.array((1028 / 12.8 * vw, 552 / 7.2 * vh)),
                            np.array((1023 / 12.8 * vw, 603 / 7.2 * vh)), np.array((815 / 12.8 * vw, 604 / 7.2 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')

def get_back(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):

        return (np.array((22 / 12.8 * vw, 21 / 7.2 * vh)), np.array((152 / 12.8 * vw, 21 / 7.2 * vh)),
                            np.array((151 / 63 * vw, 603 / 7.2 * vh)), np.array((19 / 12.8 * vw, 61 / 7.2 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')

def get_back2(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):

        return (np.array((23 / 12.8 * vw, 18 / 7.2 * vh)), np.array((163/ 12.8 * vw, 15 / 7.2 * vh)),
                            np.array((160 / 63 * vw, 60 / 7.2 * vh)), np.array((20 / 12.8 * vw, 60 / 7.2 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


def get_back2_yes(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):

        return (np.array((849 / 12.8 * vw, 498 / 7.2 * vh)), np.array((849/ 12.8 * vw, 498 / 7.2 * vh)),
                            np.array((849 / 63 * vw, 498 / 7.2 * vh)), np.array((849 / 12.8 * vw, 498 / 7.2 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


def get_back2_clear(img):#清空选择
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):

        return (np.array((512 / 12.8 * vw, 672 / 7.2 * vh)), np.array((512/ 12.8 * vw, 672 / 7.2 * vh)),
                            np.array((512 / 12.8 * vw, 672 / 7.2 * vh)), np.array((512 / 12.8 * vw, 672 / 7.2 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')
#打开进驻
def get_setting_block(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):

        return (np.array((7 / 12.8 * vw, 246 / 7.2 * vh)), np.array((113/ 12.8 * vw, 246 / 7.2 * vh)),
                            np.array((118 / 63 * vw, 352 / 7.2 * vh)), np.array((7 / 12.8 * vw, 349 / 7.2 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')

def get_clear_working(img,):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((878 / 12.8 * vw, 109 / 7.2 * vh)), np.array((963 / 12.8 * vw, 123 / 7.2 * vh)),
                np.array((974 / 12.8 * vw, 213 / 7.2 * vh)), np.array((860 / 12.8 * vw, 210 / 7.2 * vh)))

    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')

def get_character(img,index):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        if index==1:
            return (np.array((427 / 12.8 * vw, 129 / 7.2 * vh)), np.array((527 / 12.8 * vw, 135 / 7.2 * vh)),
                np.array((541 / 12.8 * vw, 324 / 7.2 * vh)), np.array((431 / 12.8 * vw, 315 / 7.2 * vh)))
        if index==2:
            return (np.array((430 / 12.8 * vw, 415 / 7.2 * vh)), np.array((538 / 12.8 * vw, 418 / 7.2 * vh)),
                np.array((530 / 12.8 * vw, 586 / 7.2 * vh)), np.array((428 / 12.8 * vw, 580 / 7.2 * vh)))
        if index==3:
            return (np.array((583 / 12.8 * vw, 141 / 7.2 * vh)), np.array((668 / 12.8 * vw, 142 / 7.2 * vh)),
                np.array((681 / 12.8 * vw, 307 / 7.2 * vh)), np.array((580 / 12.8 * vw, 289 / 7.2 * vh)))
        if index==4:
            return (np.array((572 / 12.8 * vw, 405 / 7.2 * vh)), np.array((678 / 12.8 * vw, 403 / 7.2 * vh)),
                np.array((683 / 12.8 * vw, 597 / 7.2 * vh)), np.array((565 / 12.8 * vw, 591 / 7.2 * vh)))
        if index==5:
            return (np.array((723 / 12.8 * vw, 111 / 7.2 * vh)), np.array((833 / 12.8 * vw, 114 / 7.2 * vh)),
                np.array((816 / 12.8 * vw, 310 / 7.2 * vh)), np.array((723 / 12.8 * vw, 297 / 7.2 * vh)))
        if index==6:
            return (np.array((714 / 12.8 * vw, 400 / 7.2 * vh)), np.array((827 / 12.8 * vw, 400 / 7.2 * vh)),
                np.array((830 / 12.8 * vw, 610 / 7.2 * vh)), np.array((714 / 12.8 * vw, 595 / 7.2 * vh)))
        if index==7:
            return (np.array((878 / 12.8 * vw, 109 / 7.2 * vh)), np.array((963 / 12.8 * vw, 123 / 7.2 * vh)),
                np.array((968 / 12.8 * vw, 315 / 7.2 * vh)), np.array((869 / 12.8 * vw, 300 / 7.2 * vh)))
        if index==8:
            return (np.array((864 / 12.8 * vw, 402 / 7.2 * vh)), np.array((963 / 12.8 * vw, 412 / 7.2 * vh)),
                np.array((954 / 12.8 * vw, 585 / 7.2 * vh)), np.array((863 / 12.8 * vw, 573 / 7.2 * vh)))
        if index==9:
            return (np.array((1004 / 12.8 * vw, 114 / 7.2 * vh)), np.array((1100 / 12.8 * vw, 113 / 7.2 * vh)),
                np.array((1100 / 12.8 * vw, 294 / 7.2 * vh)), np.array((1005 / 12.8 * vw, 325 / 7.2 * vh)))
        if index==10:
            return (np.array((1010 / 12.8 * vw, 411 / 7.2 * vh)), np.array((1100 / 12.8 * vw, 415 / 7.2 * vh)),
                np.array((1100 / 12.8 * vw, 588 / 7.2 * vh)), np.array((1010 / 12.8 * vw, 577 / 7.2 * vh)))
        if index==-1:#确认
            return (np.array((1100 / 12.8 * vw, 654 / 7.2 * vh)), np.array((1253 / 12.8 * vw, 660 / 7.2 * vh)),
                np.array((1251 / 12.8 * vw, 694 / 7.2 * vh)), np.array((1113 / 12.8 * vw, 694 / 7.2 * vh)))
        if index==-2:#中间
            return (np.array((611 / 12.8 * vw, 370 / 7.2 * vh)), np.array((611 / 12.8 * vw, 370 / 7.2 * vh)),
                np.array((611 / 12.8 * vw, 370 / 7.2 * vh)), np.array((611 / 12.8 * vw, 370 / 7.2 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


def get_friend_build(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((74.065 * vw, 17.134 * vh)), np.array((79.967 * vw, 17.134 * vh)),
                np.array((79.967 * vw, 28.065 * vh)), np.array((74.065 * vw, 28.065 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


def get_next_friend_build(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((85.625 * vw, 79.444 * vh)), np.array((99.531 * vw, 79.444 * vh)),
                np.array((99.531 * vw, 93.750 * vh)), np.array((85.625 * vw, 93.750 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


def get_back_my_build(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((72.266 * vw, 81.528 * vh)), np.array((88.750 * vw, 81.528 * vh)),
                np.array((88.750 * vw, 92.500 * vh)), np.array((72.266 * vw, 92.500 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


# 点击基建主界面右上角的提示（以凸显一键收取）
def get_my_build_task_1(img):#上一个
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((1178 / 12.8 * vw, 73 / 7.2 * vh)), np.array((1272 / 12.8 * vw, 72 / 7.2 * vh)),
                np.array((1272 / 12.8 * vw, 112 / 7.2 * vh)), np.array((1175 / 12.8 * vw, 114 / 7.2 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')

def get_my_build_task_2(img):#下一个
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((1178 / 12.8 * vw, 123 / 7.2 * vh)), np.array((1272 / 12.8 * vw, 124 / 7.2 * vh)),
                np.array((1272 / 12.8 * vw, 162 / 7.2 * vh)), np.array((1175 / 12.8 * vw, 162 / 7.2 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')

# 一键收取制造站的物品
def get_my_build_task_clear(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((12.500 * vw, 91.667 * vh)), np.array((16.797 * vw, 91.667 * vh)),
                np.array((16.797 * vw, 98.472 * vh)), np.array((12.500 * vw, 98.472 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


# def get_my_sell_task(img):
#     """
#     :returns: [0][1]
#               [3][2]
#     """
#     aspect = Fraction(*img.size)
#     vw, vh = util.get_vwvh(img)
#     if aspect == Fraction(16, 9):
#         return (np.array((51.111*vw, 14.375*vh)), np.array((60.000*vw, 14.375*vh)), np.array((60.000*vw, *vh)), np.array((51.111*vw, *vh)))
#     else:
#         # FIXME: implement with feature matching?
#         raise NotImplementedError('unsupported aspect ratio')

# 从基建主界面点击进入第二间贸易站
def get_my_sell_task_1(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (
        np.array((5.781 * vw, 51.806 * vh)), np.array((14.688 * vw, 51.806 * vh)), np.array((14.688 * vw, 59.167 * vh)),
        np.array((5.781 * vw, 59.167 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


# 打开订单页面
def get_my_sell_tasklist(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (
        np.array((1.094 * vw, 75.833 * vh)), np.array((41.719 * vw, 75.833 * vh)), np.array((41.719 * vw, 95.139 * vh)),
        np.array((1.094 * vw, 95.139 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


# 点击 '可交付' 订单
def get_my_sell_task_main(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((29.297 * vw, 26.528 * vh)), np.array((37.109 * vw, 26.528 * vh)),
                np.array((37.109 * vw, 61.111 * vh)), np.array((29.297 * vw, 61.111 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


# 从订单列表中进入另一间贸易设施的订单列表
def get_my_sell_task_2(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (
        np.array((1.094 * vw, 25.972 * vh)), np.array((16.875 * vw, 25.972 * vh)), np.array((16.875 * vw, 33.472 * vh)),
        np.array((1.094 * vw, 33.472 * vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


if __name__ == "__main__":
    import sys

    print(check_main(Image.open(sys.argv[-1])))
