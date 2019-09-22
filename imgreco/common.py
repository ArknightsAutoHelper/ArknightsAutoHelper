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

def check_get_item_popup(img):
    vw, vh = util.get_vwvh(img.size)
    icon1 = img.crop((50*vw-6.389*vh, 5.556*vh, 50*vw+8.426*vh, 18.981*vh)).convert('RGB')
    icon2 = resources.load_image('common/getitem.png').convert('RGB')

    icon1, icon2 = util.uniform_size(icon1, icon2)
    return imgops.compare_mse(np.asarray(icon1), np.asarray(icon2)) < icon1.width*icon1.height/3

def get_reward_popup_dismiss_rect(viewport):
    vw, vh = util.get_vwvh(viewport)
    return (100*vw-61.944*vh, 18.519*vh, 100*vw-5.833*vh, 87.222*vh)

if __name__ == "__main__":
    import sys
    print(globals()[sys.argv[-2]](Image.open(sys.argv[-1])))
