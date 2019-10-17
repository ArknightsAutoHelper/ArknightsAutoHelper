import cv2 as cv
import numpy as np
from PIL import Image

from . import imgops
from . import resources
from . import util

LOGFILE = 'log/common.html'


def check_get_item_popup(img):
    vw, vh = util.get_vwvh(img.size)
    icon1 = img.crop((50 * vw - 6.389 * vh, 5.556 * vh, 50 * vw + 8.426 * vh, 18.981 * vh)).convert('RGB')
    icon2 = resources.load_image_cached('common/getitem.png', 'RGB')

    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    mse = imgops.compare_mse(np.asarray(icon1), np.asarray(icon2))
    # print(mse, icon1.size)
    return mse < 2000


def get_reward_popup_dismiss_rect(viewport):
    vw, vh = util.get_vwvh(viewport)
    return (100 * vw - 61.944 * vh, 18.519 * vh, 100 * vw - 5.833 * vh, 87.222 * vh)


def check_nav_button(img):
    vw, vh = util.get_vwvh(img.size)
    icon1 = img.crop((3.194 * vh, 2.222 * vh, 49.722 * vh, 7.917 * vh)).convert('RGB')
    icon2 = resources.load_image_cached('common/navbutton.png', 'RGB')

    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    mse = imgops.compare_mse(np.asarray(icon1), np.asarray(icon2))
    print(mse)
    return mse < 200


def get_nav_button_back_rect(viewport):
    vw, vh = util.get_vwvh(viewport)
    return (3.194 * vh, 2.222 * vh, 20.972 * vh, 7.917 * vh)


def check_setting_scene(img):
    vw, vh = util.get_vwvh(img.size)
    icon1 = img.crop((4.722 * vh, 3.750 * vh, 19.444 * vh, 8.333 * vh)).convert('RGB')
    icon2 = resources.load_image_cached('common/settingback.png', 'RGB')

    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    return imgops.compare_mse(np.asarray(icon1), np.asarray(icon2)) < 200


def get_setting_back_rect(viewport):
    vw, vh = util.get_vwvh(viewport)
    return (4.722 * vh, 3.750 * vh, 19.444 * vh, 8.333 * vh)


def find_close_button(img):
    # raise NotImplementedError
    scale = 1
    if img.height != 720:
        scale = img.height / 720
        img = imgops.scale_to_height(img, 720)
    righttopimg = img.crop((img.width // 2, 0, img.width, img.height // 2)).convert('L')
    template = resources.load_image_cached('common/closebutton.png', 'L')
    mtresult = cv.matchTemplate(np.asarray(righttopimg), np.asarray(template), cv.TM_CCOEFF_NORMED)
    maxidx = np.unravel_index(np.argmax(mtresult), mtresult.shape)
    y, x = maxidx
    x += img.width // 2
    rect = np.array((x, y, x + template.width, y + template.height)) * scale
    return tuple(rect.astype(np.int32)), mtresult[maxidx]


if __name__ == "__main__":
    import sys

    print(globals()[sys.argv[-2]](Image.open(sys.argv[-1])))
