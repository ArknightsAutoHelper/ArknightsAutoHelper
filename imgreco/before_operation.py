import sys
from functools import lru_cache

import numpy as np
from util import cvimage as Image

from util.richlog import get_logger
from . import imgops
from . import minireco
from . import resources
from . import common

logger = get_logger(__name__)

@lru_cache(1)
def load_data():
    reco = minireco.MiniRecognizer(resources.load_pickle('minireco/NotoSansCJKsc-Medium.dat'))
    reco2 = minireco.MiniRecognizer(resources.load_pickle('minireco/Novecentosanswide_Normal.dat'))
    return (reco, reco2)

@lru_cache(1)
def recognize(img):
    vw, vh = common.get_vwvh(img.size)
    context = common.ImageRoiMatchingContext(img)

    styles = ['ep10', 'sof', 'legacy']
    variants = ['checked', 'unchecked']
    matches = [context.match_roi(f'before_operation/delegation_{variant}_{style}') for style in styles for variant in variants]
    delegate_match = min(matches, key=lambda x: x.score)
    logger.logtext('best_match=%s' % delegate_match)
    if delegate_match.score > 3251:
        # ASSUMPTION: 存在代理指挥按钮
        return None
    *_, template, style = delegate_match.roi_name.split('_')
    delegated = template == 'checked'
    logger.logtext(f'{delegated=}, {style=}')
    reco_Noto, reco_Novecento = load_data()
    check_consume_ap = False
    if style == 'legacy':
        # old layout
        opidrect = (100 * vw - 55.694 * vh, 11.667 * vh, 100 * vw - 44.028 * vh, 15.139 * vh)
        consumerect = (100 * vw - 12.870 * vh, 94.028 * vh, 100 * vw - 7.222 * vh, 97.361 * vh)
        start_button = (100 * vw - 30.972 * vh, 88.241 * vh, 100 * vw - 3.611 * vh, 95.556 * vh)
        ap_rect = (100 * vw - 21.019 * vh, 2.917 * vh, 100 * vw, 8.194 * vh)
        stage_reco = reco_Novecento
    elif style == 'ep10':
        # 2022-04-14: episode 10 new layout
        opidrect = (100*vw-49.537*vh, 11.111*vh, 100*vw-37.870*vh, 15.370*vh)
        consumerect = (100*vw-13.704*vh, 95.833*vh, 100*vw-7.315*vh, 99.074*vh)
        start_button = (100*vw-31.759*vh, 90.093*vh, 100*vw-6.389*vh, 96.296*vh)
        ap_rect = (100 * vw - 21.019 * vh, 2.917 * vh, 100 * vw, 8.194 * vh)
        stage_reco = reco_Novecento
        check_consume_ap = True
    elif style == 'sof':
        # i.e. Stultifera Navis
        opidrect = (23.241*vh, 74.907*vh, 35.278*vh, 78.426*vh)
        consumerect = (100*vw-14.944*vh, 90.926*vh, 100*vw-8.463*vh, 94.259*vh)
        start_button = (100*vw-31.667*vh, 86.574*vh, 100*vw-9.167*vh, 90.833*vh)
        ap_rect = (100*vw-24.630*vh, 4.259*vh, 100*vw-9.259*vh, 8.611*vh)
        stage_reco = reco_Noto


    # if imgops.compare_region_mse(img, (43.333*vh, 86.111*vh, 50.185*vh, 95.093*vh), 'before_operation/interlocking/interlocking_tag.png', threshold=650, logger=logger):
    #     return recognize_interlocking(img)

    
    if check_consume_ap:
        apicon1 = img.crop((100*vw-29.722*vh, 2.130*vh, 100*vw-22.593*vh, 8.519*vh)).convert('RGB')

        apicon2 = resources.load_image_cached('before_operation/ap_icon.png', 'RGB')
        apicon1, apicon2 = imgops.uniform_size(apicon1, apicon2)
        mse = imgops.compare_mse(apicon1, apicon2)
        logger.logimage(apicon1)
        logger.logtext('mse=%f' % mse)
        consume_ap = mse < 3251
    else:
        consume_ap = True

    apimg = img.crop(ap_rect).convert('L')
    apimg = imgops.enhance_contrast(apimg, 80, 255)
    logger.logimage(apimg)
    aptext, _ = reco_Noto.recognize2(apimg, subset='0123456789/')
    logger.logtext(aptext)
    # print("AP:", aptext)

    opidimg = img.crop(opidrect).convert('L')
    opidimg = imgops.enhance_contrast(opidimg, 80, 255)
    logger.logimage(opidimg)
    opidtext = str(stage_reco.recognize(opidimg))
    if opidtext.endswith('-'):
        opidtext = opidtext[:-1]
    opidtext = opidtext.upper()
    logger.logtext(opidtext)
    fixup, opidtext = minireco.fix_stage_name(opidtext)
    if fixup:
        logger.logtext('fixed to ' + opidtext)

    nofriendshiplist = ['OF-F']
    no_friendship = any(opidtext.startswith(header) for header in nofriendshiplist)


    # print('delegated:', delegated)

    consumeimg = img.crop(consumerect).convert('L')
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
        'no_friendship': no_friendship,
        'operation': opidtext,
        'delegated': delegated,
        'consume': int(consumetext) if consumetext.isdigit() else None,
        'style': style,
        'delegate_button': delegate_match.bbox.ltrb,
        'start_button': start_button
    }
    # print('consumption:', consumetext)


def recognize_interlocking(img):
    vw, vh = common.get_vwvh(img)

    consume_ap = imgops.compare_region_mse(img, (100*vw-31.944*vh, 2.407*vh, 100*vw-25.648*vh, 8.426*vh), 'before_operation/interlocking/ap_icon.png', logger=logger)

    apimg = img.crop((100*vw-25.278*vh, 2.407*vh, 100*vw-10.093*vh, 8.426*vh)).convert('L')
    reco_Noto, reco_Novecento = load_data()
    apimg = imgops.enhance_contrast(apimg, 80, 255)
    logger.logimage(apimg)
    aptext, _ = reco_Noto.recognize2(apimg, subset='0123456789/')
    logger.logtext(aptext)

    delegated = imgops.compare_region_mse(img, (100*vw-32.963*vh, 78.333*vh, 100*vw-5.185*vh, 84.167*vh), 'before_operation/interlocking/delegation_checked.png', logger=logger)

    consumeimg = img.crop((100*vw-11.944*vh, 94.259*vh, 100*vw-5.185*vh, 97.500*vh)).convert('L')
    consumeimg = imgops.enhance_contrast(consumeimg, 80, 255)
    logger.logimage(consumeimg)
    consumetext, minscore = reco_Noto.recognize2(consumeimg, subset='-0123456789')
    consumetext = ''.join(c for c in consumetext if c in '0123456789')
    logger.logtext('{}, {}'.format(consumetext, minscore))


    return {
        'AP': aptext,
        'consume_ap': consume_ap,
        'no_friendship': False,
        'operation': 'interlocking',
        'delegated': delegated,
        'consume': int(consumetext) if consumetext.isdigit() else None,
        'style': 'interlocking',
        'delegate_button': (100*vw-32.963*vh, 78.333*vh, 100*vw-5.185*vh, 84.167*vh),
        'start_button': (100*vw-33.426*vh, 86.296*vh, 100*vw-5.185*vh, 95.000*vh)
    }


def check_confirm_troop_rect(img):
    vw, vh = common.get_vwvh(img.size)
    icon1 = img.crop((50 * vw + 57.083 * vh, 64.722 * vh, 50 * vw + 71.389 * vh, 79.167 * vh)).convert('RGB')
    icon2 = resources.load_image_cached('before_operation/operation_start.png', 'RGB')
    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    coef = imgops.compare_ccoeff(np.asarray(icon1), np.asarray(icon2))
    logger.logimage(icon1)
    logger.logtext('ccoeff=%f' % coef)
    return coef > 0.9


def get_confirm_troop_rect(viewport):
    vw, vh = common.get_vwvh(viewport)
    return (50 * vw + 55.833 * vh, 52.963 * vh, 50 * vw + 72.778 * vh, 87.361 * vh)


def check_ap_refill_type(img):
    context = common.ImageRoiMatchingContext(img)
    vw, vh = common.get_vwvh(img.size)

    item_icon = context.match_roi('before_operation/refill_with_item_icon', method='ccoeff')
    originium_icon = context.match_roi('before_operation/refill_with_originium_icon', method='ccoeff')

    if not item_icon and not originium_icon:
        return None
    if item_icon:
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
    vw, vh = common.get_vwvh(viewport)
    return (50*vw+49.537*vh, 77.222*vh, 50*vw+74.352*vh, 84.815*vh)


def get_ap_refill_cancel_rect(viewport):
    vw, vh = common.get_vwvh(viewport)
    return (50*vw+14.259*vh, 77.130*vh, 50*vw+24.352*vh, 83.611*vh)


if __name__ == "__main__":
    print(recognize(Image.open(sys.argv[-1])))
