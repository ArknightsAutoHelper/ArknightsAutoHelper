import sys
from functools import lru_cache

import numpy as np
from PIL import Image

from util.richlog import get_logger
from . import imgops
from . import minireco
from . import resources
from . import util

logger = get_logger(__name__)

@lru_cache(1)
def load_data():
    reco = minireco.MiniRecognizer(resources.load_pickle('minireco/NotoSansCJKsc-Medium.dat'))
    reco2 = minireco.MiniRecognizer(resources.load_pickle('minireco/Novecentosanswide_Medium.dat'))
    return (reco, reco2)

@lru_cache(1)
def recognize(img):
    vw, vh = util.get_vwvh(img.size)

    apicon1 = img.crop((100*vw-29.722*vh, 2.130*vh, 100*vw-22.593*vh, 8.519*vh)).convert('RGB')

    apicon2 = resources.load_image_cached('before_operation/ap_icon.png', 'RGB')
    apicon1, apicon2 = imgops.uniform_size(apicon1, apicon2)
    coef = imgops.compare_ccoeff(apicon1, apicon2)
    logger.logimage(apicon1)
    logger.logtext('ccoeff=%f' % coef)
    consume_ap = coef > 0.9

    apimg = img.crop((100 * vw - 21.019 * vh, 2.917 * vh, 100 * vw, 8.194 * vh)).convert('L')
    reco_Noto, reco_Novecento = load_data()
    apimg = imgops.enhance_contrast(apimg, 80, 255)
    logger.logimage(apimg)
    aptext, _ = reco_Noto.recognize2(apimg, subset='0123456789/')
    logger.logtext(aptext)
    # print("AP:", aptext)

    opidimg = img.crop((100 * vw - 55.694 * vh, 11.667 * vh, 100 * vw - 44.028 * vh, 15.139 * vh)).convert('L')
    opidimg = imgops.enhance_contrast(opidimg, 80, 255)
    logger.logimage(opidimg)
    opidtext = reco_Novecento.recognize(opidimg)
    if opidtext.endswith('-'):
        opidtext = opidtext[:-1]
    opidtext = opidtext.upper()
    logger.logtext(opidtext)
    if opidtext and opidtext[0] == '0':
        opidtext = 'O' + opidtext[1:]
        logger.logtext('fixed to ' + opidtext)
    # print('operation:', opidtext)

    delegateimg = img.crop((100 * vw - 32.778 * vh, 79.444 * vh, 100 * vw - 4.861 * vh, 85.417 * vh)).convert('L')
    template = resources.load_image_cached('before_operation/delegation_checked.png', 'L')
    logger.logimage(delegateimg)
    mse = imgops.compare_mse(*imgops.uniform_size(delegateimg, template))
    logger.logtext('mse=%f' % mse)
    delegated = mse < 400
    # print('delegated:', delegated)

    consumeimg = img.crop((100 * vw - 12.870 * vh, 94.028 * vh, 100 * vw - 7.222 * vh, 97.361 * vh)).convert('L')
    consumeimg = imgops.enhance_contrast(consumeimg, 80, 255)
    logger.logimage(consumeimg)
    consumetext, minscore = reco_Noto.recognize2(consumeimg, subset='-0123456789')
    consumetext = ''.join(c for c in consumetext if c in '0123456789')
    logger.logtext('{}, {}'.format(consumetext, minscore))

    if not aptext:
        # ASSUMPTION: 只有在战斗前界面才能识别到右上角体力
        return None
    if not consumetext.isdigit():
        # ASSUMPTION: 所有关卡都显示并能识别体力消耗
        return None

    return {
        'AP': aptext,
        'consume_ap': consume_ap,
        'operation': opidtext,
        'delegated': delegated,
        'consume': int(consumetext) if consumetext.isdigit() else None
    }
    # print('consumption:', consumetext)


def get_delegate_rect(viewport):
    vw, vh = util.get_vwvh(viewport)
    return (100 * vw - 32.083 * vh, 79.907 * vh, 100 * vw - 5.972 * vh, 84.444 * vh)


def get_start_operation_rect(viewport):
    vw, vh = util.get_vwvh(viewport)
    return (100 * vw - 30.972 * vh, 88.241 * vh, 100 * vw - 3.611 * vh, 95.556 * vh)


def check_confirm_troop_rect(img):
    vw, vh = util.get_vwvh(img.size)
    icon1 = img.crop((50 * vw + 57.083 * vh, 64.722 * vh, 50 * vw + 71.389 * vh, 79.167 * vh)).convert('RGB')
    icon2 = resources.load_image_cached('before_operation/operation_start.png', 'RGB')
    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    coef = imgops.compare_ccoeff(np.asarray(icon1), np.asarray(icon2))
    logger.logimage(icon1)
    logger.logtext('ccoeff=%f' % coef)
    return coef > 0.9


def get_confirm_troop_rect(viewport):
    vw, vh = util.get_vwvh(viewport)
    return (50 * vw + 55.833 * vh, 52.963 * vh, 50 * vw + 72.778 * vh, 87.361 * vh)


def check_ap_refill_type(img):
    vw, vh = util.get_vwvh(img.size)
    icon1 = img.crop((50*vw-3.241*vh, 11.481*vh, 50*vw+42.685*vh, 17.130*vh)).convert('RGB')
    icon2 = resources.load_image_cached('before_operation/refill_with_item.png', 'RGB')
    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    mse1 = imgops.compare_mse(icon1, icon2)
    logger.logimage(icon1)

    icon1 = img.crop((50*vw+41.574*vh, 11.481*vh, 50*vw+87.315*vh, 17.130*vh)).convert('RGB')
    icon2 = resources.load_image_cached('before_operation/refill_with_originium.png', 'RGB')
    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    mse2 = imgops.compare_mse(icon1, icon2)

    logger.logimage(icon1)
    logger.logtext('mse1=%f, mse2=%f' % (mse1, mse2))

    if min(mse1, mse2) > 1500:
        return None
    if mse1 < mse2:
        return 'item'

    icon1 = img.crop((50*vw+25.972*vh, 36.250*vh, 50*vw+54.722*vh, 61.250*vh)).convert('RGB')
    icon2 = resources.load_image_cached('before_operation/no_originium.png', 'RGB')
    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    mse3 = imgops.compare_mse(icon1, icon2)
    logger.logimage(icon1)
    logger.logtext('mse=%f' % mse3)
    if mse3 < 500:
        return None
    else:
        return 'originium'


def get_ap_refill_confirm_rect(viewport):
    vw, vh = util.get_vwvh(viewport)
    return (50*vw+49.537*vh, 77.222*vh, 50*vw+74.352*vh, 84.815*vh)


if __name__ == "__main__":
    print(recognize(Image.open(sys.argv[-1])))
