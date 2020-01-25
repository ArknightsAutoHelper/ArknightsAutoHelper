from fractions import Fraction

import numpy as np
from PIL import Image

from richlog import get_logger
from . import imgops
from . import resources
from . import util

LOGFILE = 'main.html'
logger = get_logger(LOGFILE)

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
        (61.120 * vw, 16.944 * vh), (82.213 * vw, 15.139 * vh), (82.213 * vw, 37.083 * vh), (61.120 * vw, 38.333 * vh))
    elif aspect == Fraction(18, 9):
        return (
        (64.693 * vw, 16.852 * vh), (82.378 * vw, 14.352 * vh), (82.378 * vw, 37.500 * vh), (64.693 * vw, 37.963 * vh))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


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

# 以下几条用于访问好友基建
def get_friend_corners(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((22.734*vw, 76.667*vh)), np.array((33.203*vw, 76.667*vh)), np.array((33.203*vw, 82.083*vh)), np.array((22.734*vw, 82.083*vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')
       
def get_friend_list(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((1.484*vw, 25.694*vh)), np.array((16.797*vw, 25.694*vh)), np.array((16.797*vw, 36.111*vh)), np.array((1.484*vw, 36.111*vh)))
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
    	return (np.array((74.065*vw, 17.134*vh)), np.array((79.967*vw, 17.134*vh)), np.array((79.967*vw, 28.065*vh)), np.array((74.065*vw, 28.065*vh)))
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
        return (np.array((85.625*vw, 79.444*vh)), np.array((99.531*vw, 79.444*vh)), np.array((99.531*vw, 93.750*vh)), np.array((85.625*vw, 93.750*vh)))
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
        return (np.array((72.266*vw, 81.528*vh)), np.array((88.750*vw, 81.528*vh)), np.array((88.750*vw, 92.500*vh)), np.array((72.266*vw, 92.500*vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')

# 点击基建主界面右上角的提示（以凸显一键收取）
def get_my_build_task(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return (np.array((92.031*vw, 10.417*vh)), np.array((99.688*vw, 10.417*vh)), np.array((99.688*vw, 15.417*vh)), np.array((92.031*vw, 15.417*vh)))
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
        return (np.array((12.500*vw, 91.667*vh)), np.array((16.797*vw, 91.667*vh)), np.array((16.797*vw, 98.472*vh)), np.array((12.500*vw, 98.472*vh)))
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
        return (np.array((5.781*vw, 51.806*vh)), np.array((14.688*vw, 51.806*vh)), np.array((14.688*vw, 59.167*vh)), np.array((5.781*vw, 59.167*vh)))
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
        return (np.array((1.094*vw, 75.833*vh)), np.array((41.719*vw, 75.833*vh)), np.array((41.719*vw, 95.139*vh)), np.array((1.094*vw, 95.139*vh)))
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
        return (np.array((29.297*vw, 26.528*vh)), np.array((37.109*vw, 26.528*vh)), np.array((37.109*vw, 61.111*vh)), np.array((29.297*vw, 61.111*vh)))
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
        return (np.array((1.094*vw, 25.972*vh)), np.array((16.875*vw, 25.972*vh)), np.array((16.875*vw, 33.472*vh)), np.array((1.094*vw, 33.472*vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')
        
if __name__ == "__main__":
    import sys

    print(check_main(Image.open(sys.argv[-1])))
