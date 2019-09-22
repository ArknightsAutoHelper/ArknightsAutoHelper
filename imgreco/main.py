from functools import lru_cache
from fractions import Fraction
import numpy as np
from PIL import Image, ImageOps

from richlog import get_logger
from . import imgops
from . import util
from . import minireco
from . import resources

def check_main(img):
    vw, vh = util.get_vwvh(img.size)
    gear1 = img.crop((3.148*vh, 2.037*vh, 9.907*vh, 8.796*vh)).convert('RGB')

    gear2 = resources.load_image('main/gear.png').convert('RGB')

    if gear1.height < gear2.height:
        gear2 = gear2.resize(gear1.size, Image.BILINEAR)
    elif gear1.height > gear2.height:
        gear1 = gear1.resize(gear2.size, Image.BILINEAR)
    elif gear1.width != gear2.width:
        gear1 = gear1.resize(gear2.size, Image.BILINEAR)

    mse = imgops.compare_mse(np.asarray(gear1), np.asarray(gear2))
    return mse < gear1.width*gear1.height

def get_ballte_corners(img):
    """
    :returns: [0][1]
              [3][2]
    """
    aspect = Fraction(*img.size)
    vw, vh = util.get_vwvh(img)
    if aspect == Fraction(16, 9):
        return ((61.120*vw, 16.944*vh), (82.213*vw, 15.139*vh), (82.213*vw, 37.083*vh), (61.120*vw, 38.333*vh))
    elif aspect == Fraction(18, 9):
        return ((64.693*vw, 16.852*vh), (82.378*vw, 14.352*vh), (82.378*vw, 37.500*vh), (64.693*vw, 37.963*vh))
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
        return (np.array((55.602*vw, 75.880*vh)), np.array((70.367*vw, 78.241*vh)), np.array((70.367*vw, 91.991*vh)), np.array((55.602*vw, 88.518*vh)))
    elif aspect == Fraction(18, 9):
        return (np.array((58.489*vw, 76.296*vh)), np.array((72.008*vw, 78.611*vh)), np.array((72.008*vw, 92.685*vh)), np.array((58.489*vw, 89.167*vh)))
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')

if __name__ == "__main__":
    import sys
    print(check_main(Image.open(sys.argv[-1])))
