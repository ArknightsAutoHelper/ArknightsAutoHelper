import cv2 as cv
import numpy as np
from PIL import Image

from util.richlog import get_logger
from . import imgops
from . import resources
from . import util

logger = get_logger(__name__)

def check_get_item_popup(img):
    vw, vh = util.get_vwvh(img.size)
    icon1 = img.crop((50 * vw - 6.389 * vh, 5.556 * vh, 50 * vw + 8.426 * vh, 18.981 * vh)).convert('RGB')
    icon2 = resources.load_image_cached('common/getitem.png', 'RGB')

    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    mse = imgops.compare_mse(np.asarray(icon1), np.asarray(icon2))
    # print(mse, icon1.size)
    logger.logimage(icon1)
    logger.logtext('mse=%f' % mse)
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
    logger.logimage(icon1)
    logger.logtext('check_nav_button mse=%f' % mse)
    return mse < 300


def get_nav_button_back_rect(viewport):
    vw, vh = util.get_vwvh(viewport)
    return (3.194 * vh, 2.222 * vh, 20.972 * vh, 7.917 * vh)


def check_setting_scene(img):
    vw, vh = util.get_vwvh(img.size)
    icon1 = img.crop((4.722 * vh, 3.750 * vh, 19.444 * vh, 8.333 * vh)).convert('RGB')
    icon2 = resources.load_image_cached('common/settingback.png', 'RGB')

    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    mse = imgops.compare_mse(np.asarray(icon1), np.asarray(icon2))
    logger.logimage(icon1)
    logger.logtext('mse=%f' % mse)
    return mse < 200

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

def check_dialog(img):
    # vw, vh = util.get_vwvh(img.size)
    # buttons = img.crop((0, 64.861*vh, 100.000*vw, 75.417*vh)).convert('RGB')
    oldheight = img.height
    img = img.resize((1280, 720), Image.BILINEAR).convert('RGB').crop((0, 360, 1280, 640))
    yesno = resources.load_image_cached('common/dialog_2btn.png', 'RGB')
    ok = resources.load_image_cached('common/dialog_1btn.png', 'RGB')
    pt1, coef1 = imgops.match_template(img, yesno)
    pt2, coef2 = imgops.match_template(img, ok)
    # print(pt1, coef1, pt2, coef2)
    if max(coef1, coef2) > 0.5:
        return ('yesno', (pt1[1] + 360)/720 * oldheight) if coef1 > coef2 else ('ok', (pt2[1] + 360)/720 * oldheight)
    return None, None

def recognize_dialog(img):
    dlgtype, _ = check_dialog(img)
    if dlgtype is None:
        return None, None
    from . import ocr
    vw, vh = util.get_vwvh(img.size)
    content = img.crop((0, 22.222*vh, 100.000*vw, 64.167*vh)).convert('L')
    return dlgtype, ocr.acquire_engine_global_cached('zh-cn').recognize(content, int(vh * 20))

def get_dialog_left_button_rect(img):
    vw, vh = util.get_vwvh(img)
    dlgtype, y = check_dialog(img)
    assert dlgtype == 'yesno'
    return (0, y-4*vh, 50*vw, y+4*vh)

def get_dialog_right_button_rect(img):
    vw, vh = util.get_vwvh(img)
    dlgtype, y = check_dialog(img)
    assert dlgtype == 'yesno'
    return (50*vw, y-4*vh, 100*vw, y+4*vh)

def get_dialog_ok_button_rect(img):
    vw, vh = util.get_vwvh(img)
    dlgtype, y = check_dialog(img)
    assert dlgtype == 'ok'
    return (25*vw, y-4*vh, 75*vw, y+4*vh)


def convert_to_pil(cv_img, color_code=cv.COLOR_BGR2RGB):
    return Image.fromarray(cv.cvtColor(cv_img, color_code))


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


if __name__ == "__main__":
    import sys

    print(globals()[sys.argv[-2]](Image.open(sys.argv[-1])))
