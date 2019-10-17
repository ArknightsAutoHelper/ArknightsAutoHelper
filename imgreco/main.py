from fractions import Fraction

import numpy as np
from PIL import Image

from . import imgops
from . import resources
from . import util


def check_main(img):
    vw, vh = util.get_vwvh(img.size)
    gear1 = img.crop((3.148 * vh, 2.037 * vh, 9.907 * vh, 8.796 * vh)).convert('L')
    gear2 = resources.load_image_cached('main/gear.png', 'L')
    gear1, gear2 = imgops.uniform_size(gear1, gear2)
    result = imgops.compare_ccoeff(gear1, gear2)
    # result = np.corrcoef(np.asarray(gear1).flat, np.asarray(gear2).flat)[0, 1]
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
    else:
        # FIXME: implement with feature matching?
        raise NotImplementedError('unsupported aspect ratio')


if __name__ == "__main__":
    import sys

    print(check_main(Image.open(sys.argv[-1])))
