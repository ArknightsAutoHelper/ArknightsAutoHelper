from functools import lru_cache

import numpy as np
from PIL import Image, ImageOps

from richlog import get_logger
from . import imgops
from . import util
from . import minireco
from . import resources

LOGFILE = 'log/task.html'

@lru_cache(1)
def load_data():
    reco = minireco.MiniRecognizer(resources.load_pickle('minireco/NotoSansCJKsc-Medium.dat'))
    return reco

def check_reward_popup(img):
    vw, vh = (x/100 for x in img.size)
    getrewardimg = img.crop((50*vw-7.130*vh, 19.630*vh, 50*vw+7.130*vh, 23.519*vh))
    getrewardimg = imgops.image_threshold(getrewardimg, 144)
    reco = load_data()
    return util.any_in('物资', reco.recognize(getrewardimg))

def get_reward_popup_dismiss_rect(viewport):
    vw, vh = (x/100 for x in viewport)
    return (100*vw-61.944*vh, 18.519*vh, 100*vw-5.833*vh, 87.222*vh)
