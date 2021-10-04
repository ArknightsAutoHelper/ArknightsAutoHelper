from functools import lru_cache

import numpy as np
from util import cvimage as Image

from util.richlog import get_logger
from . import imgops
from . import minireco
from . import resources
from . import util

logger = get_logger(__name__)

@lru_cache(1)
def load_data():
    reco = minireco.MiniRecognizer(resources.load_pickle('minireco/NotoSansCJKsc-Medium.dat'))
    return reco


def check_collectable_reward(img):
    vw, vh = util.get_vwvh(img)
    if imgops.compare_region_mse(img, (50*vw-83.611*vh, 20.093*vh, 50*vw-77.407*vh, 26.944*vh), 'task/collected_reward_set.png', logger=logger):
        # 第一个奖励显示已完成，即已领取全部奖励
        return False
    return imgops.compare_region_mse(img, (50*vw+70.278*vh, 14.537*vh, 50*vw+83.241*vh, 22.778*vh), 'task/collect_all.png', logger=logger)

def get_collect_reward_button_rect(viewport):
    vw, vh = (x / 100 for x in viewport)
    return (50 * vw + 49.630 * vh, 16.019 * vh, 50 * vw + 83.704 * vh, 23.565 * vh)


def check_beginners_task(img):
    vw, vh = util.get_vwvh(img)
    icon1 = img.crop((50 * vw - 24.028 * vh, 1.806 * vh, 50 * vw - 17.639 * vh, 7.917 * vh)).convert('RGB')
    icon2 = resources.load_image_cached('task/beginners.png', 'RGB')

    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    mse = imgops.compare_mse(np.asarray(icon1), np.asarray(icon2))
    logger.logimage(icon1)
    logger.logtext('mse=%f' % mse)
    return mse < 650


def get_daily_task_rect(viewport, beginners_task_exist=False):
    vw, vh = util.get_vwvh(viewport)
    if beginners_task_exist:
        return (50 * vw + 4.028 * vh, 1.806 * vh, 50 * vw + 30.417 * vh, 7.917 * vh)
    else:
        return (50 * vw - 23.843 * vh, 1.806 * vh, 50 * vw + 11.250 * vh, 7.917 * vh)


def get_weekly_task_rect(viewport, beginners_task_exist=False):
    vw, vh = util.get_vwvh(viewport)
    if beginners_task_exist:
        return (50 * vw + 31.991 * vh, 1.806 * vh, 50 * vw + 58.287 * vh, 7.917 * vh)
    else:
        return (50 * vw + 13.380 * vh, 1.806 * vh, 50 * vw + 49.120 * vh, 7.917 * vh)
