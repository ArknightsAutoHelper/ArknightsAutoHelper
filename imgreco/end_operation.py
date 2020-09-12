import sys
import math

import cv2
import numpy as np
from PIL import Image

from util.richlog import get_logger
from . import imgops
from . import item
from . import minireco
from . import resources
from . import util

logger = get_logger(__name__)


class RecognizeSession:
    def __init__(self):
        self.recognized_groups = []
        self.low_confidence = False
        self.vh = 0
        self.vw = 0


def tell_stars(starsimg):
    thstars = (np.asarray(starsimg.convert('L')) > 96)
    width, height = thstars.shape[::-1]
    starwidth = width // 3
    threshold = height * (width / 12)
    stars = []
    star1 = thstars[:, 0:starwidth]
    stars.append(np.count_nonzero(star1) > threshold)

    star2 = thstars[:, starwidth:starwidth * 2]
    stars.append(np.count_nonzero(star2) > threshold)

    star3 = thstars[:, starwidth * 2:]
    stars.append(np.count_nonzero(star3) > threshold)
    return tuple(stars)


recozh = minireco.MiniRecognizer(resources.load_pickle('minireco/NotoSansCJKsc-Medium.dat'))
reco_novecento_bold = minireco.MiniRecognizer(resources.load_pickle('minireco/Novecentosanswide_Bold.dat'))


def tell_group(groupimg, session, bartop, barbottom, ):
    logger.logimage(groupimg)
    grouptext = groupimg.crop((0, barbottom, groupimg.width, groupimg.height))

    thim = imgops.enhance_contrast(grouptext.convert('L'), 60)
    # thim = imgops.crop_blackedge(thim)
    logger.logimage(thim)

    groupname, diff = tell_group_name_alt(thim, session)
    if diff > 0.8:
        session.low_confidence = True

    if groupname == '幸运掉落':
        return (groupname, [('(家具)', 1)])

    vw, vh = session.vw, session.vh
    itemwidth = 20.370 * vh
    itemcount = roundint(groupimg.width / itemwidth)
    logger.logtext('group has %d items' % itemcount)
    result = []
    for i in range(itemcount):
        itemimg = groupimg.crop((itemwidth * i, 0.000 * vh, itemwidth * (i+1), 18.981 * vh))
        # x1, _, x2, _ = (0.093*vh, 0.000*vh, 19.074*vh, 18.981*vh)
        itemimg = itemimg.crop((0.093 * vh, 0, 19.074 * vh, itemimg.height))
        recognized_item = item.tell_item(itemimg, session)
        if recognized_item.low_confidence:
            session.low_confidence = True
        result.append((recognized_item.name, recognized_item.quantity))
    return (groupname, result)


def tell_group_name_alt(img, session):
    names = [('龙门币', '声望&龙门币奖励'),
             ('常规', '常规掉落'),
             ('特殊', '特殊掉落'),
             ('幸运', '幸运掉落'),
             ('额外', '额外物资'),
             ('首次', '首次掉落'),
             ('返还', '理智返还')]
    comparsions = []
    scale = session.vh * 100 / 1080

    for name, group in names:
        if group in session.recognized_groups:
            continue
        template = resources.load_image_cached(f'end_operation/group/{name}.png', 'L')
        scaled_height = template.height * scale
        scaled_height_floor = math.floor(scaled_height)
        scaled_template_floor = imgops.scale_to_height(template, scaled_height_floor)
        if scaled_template_floor.width > img.width or scaled_template_floor.height > img.height:
            raise ValueError('image smaller than template')
        _, diff_floor = imgops.match_template(img, scaled_template_floor, cv2.TM_SQDIFF_NORMED)
        if scaled_height_floor + 1 <= img.height:
            scaled_template_ceil = imgops.scale_to_height(template, scaled_height_floor + 1)
            _, diff_ceil = imgops.match_template(img, scaled_template_ceil, cv2.TM_SQDIFF_NORMED)
            diff = min(diff_floor, diff_ceil)
        else:
            diff = diff_floor
        comparsions.append((group, diff))

    if comparsions:
        comparsions.sort(key=lambda x: x[1])
        logger.logtext(repr(comparsions))
        return comparsions[0]


def find_jumping(ary, threshold):
    ary = np.array(ary, dtype=np.int16)
    diffs = np.diff(ary)
    shit = [x for x in enumerate(diffs) if abs(x[1]) >= threshold]
    if not shit:
        return []
    groups = [[shit[0]]]
    for x in shit[1:]:
        lastgroup = groups[-1]
        if np.sign(x[1]) == np.sign(lastgroup[-1][1]):
            lastgroup.append(x)
        else:
            groups.append([x])
    logger.logtext(repr(groups))
    pts = []
    for group in groups:
        pts.append(int(np.average(
            tuple(x[0] for x in group), weights=tuple(abs(x[1]) for x in group))) + 1)
    return pts


def roundint(x):
    return int(round(x))


# scale = 0


def check_level_up_popup(img):
    vw, vh = util.get_vwvh(img.size)

    lvl_up_img = img.crop((50*vw-48.796*vh, 47.685*vh, 50*vw-23.148*vh, 56.019*vh)).convert('L')  # 等级提升
    lvl_up_img = imgops.enhance_contrast(lvl_up_img, 216, 255)
    lvl_up_text = recozh.recognize(lvl_up_img)
    return minireco.check_charseq(lvl_up_text, '提升')


def check_end_operation(img):
    vw, vh = util.get_vwvh(img.size)
    template = resources.load_image_cached('end_operation/friendship.png', 'RGB')
    operation_end_img = img.crop((117.083*vh, 64.306*vh, 121.528*vh, 69.583*vh)).convert('RGB')
    mse = imgops.compare_mse(*imgops.uniform_size(template, operation_end_img))
    return mse < 3251


def check_end_operation_alt(img):
    vw, vh = util.get_vwvh(img.size)
    template = resources.load_image_cached('end_operation/end.png', 'L')
    operation_end_img = img.crop((4.722 * vh, 80.278 * vh, 56.389 * vh, 93.889 * vh)).convert('L')
    operation_end_img = imgops.enhance_contrast(operation_end_img, 225, 255)
    mse = imgops.compare_mse(*imgops.uniform_size(template, operation_end_img))
    return mse < 6502


def get_dismiss_level_up_popup_rect(viewport):
    vw, vh = util.get_vwvh(viewport)
    return (100 * vw - 67.315 * vh, 16.019 * vh, 100 * vw - 5.185 * vh, 71.343 * vh)


get_dismiss_end_operation_rect = get_dismiss_level_up_popup_rect


def recognize(im):
    import time
    t0 = time.monotonic()
    vw, vh = util.get_vwvh(im.size)

    lower = im.crop((0, 61.111 * vh, 100 * vw, 100 * vh))
    logger.logimage(lower)

    operation_id = lower.crop((0, 4.444 * vh, 23.611 * vh, 11.388 * vh)).convert('L')
    # logger.logimage(operation_id)
    operation_id = imgops.enhance_contrast(imgops.crop_blackedge(operation_id), 80, 220)
    logger.logimage(operation_id)
    operation_id_str = reco_novecento_bold.recognize(operation_id).upper()
    fixup, operation_id_str = minireco.fix_stage_name(operation_id_str)
    if fixup:
        logger.logtext('fixed to ' + operation_id_str)
    # operation_name = lower.crop((0, 14.074*vh, 23.611*vh, 20*vh)).convert('L')
    # operation_name = imgops.enhance_contrast(imgops.crop_blackedge(operation_name))
    # logger.logimage(operation_name)

    stars = lower.crop((23.611 * vh, 6.759 * vh, 53.241 * vh, 16.944 * vh))
    logger.logimage(stars)
    stars_status = tell_stars(stars)

    # level = lower.crop((63.148 * vh, 4.444 * vh, 73.333 * vh, 8.611 * vh))
    # logger.logimage(level)
    # exp = lower.crop((76.852 * vh, 5.556 * vh, 94.074 * vh, 7.963 * vh))
    # logger.logimage(exp)

    recoresult = {
        'operation': operation_id_str,
        'stars': stars_status,
        'items': [],
        'low_confidence': False
    }

    items = lower.crop((68.241 * vh, 10.926 * vh, lower.width, 35.000 * vh))
    logger.logimage(items)

    x, y = 6.667 * vh, 18.519 * vh
    linedet = items.crop((x, y, x + 1, items.height)).convert('L')
    d = np.asarray(linedet)
    linedet = find_jumping(d.reshape(linedet.height), 64)
    if len(linedet) >= 2:
        linetop, linebottom, *_ = linedet
    else:
        logger.logtext('horizontal line detection failed')
        recoresult['low_confidence'] = True
        return recoresult
    linetop += y
    linebottom += y

    grouping = items.crop((0, linetop, items.width, linebottom))
    grouping = grouping.resize((grouping.width, 1), Image.BILINEAR)
    grouping = grouping.convert('L')

    logger.logimage(grouping.resize((grouping.width, 16)))

    d = np.array(grouping, dtype=np.int16)[0]
    points = [0, *find_jumping(d, 64)]
    if len(points) % 2 != 0:
        raise RuntimeError('possibly incomplete item list')
    finalgroups = list(zip(*[iter(points)] * 2))  # each_slice(2)
    logger.logtext(repr(finalgroups))

    imggroups = [items.crop((x1, 0, x2, items.height))
                 for x1, x2 in finalgroups]
    items = []

    session = RecognizeSession()
    session.vw = vw
    session.vh = vh

    for group in imggroups:
        groupresult = tell_group(group, session, linetop, linebottom)
        session.recognized_groups.append(groupresult[0])
        items.append(groupresult)

    t1 = time.monotonic()
    if session.low_confidence:
        logger.logtext('LOW CONFIDENCE')
    logger.logtext('time elapsed: %f' % (t1 - t0))
    recoresult['items'] = items
    recoresult['low_confidence'] = recoresult['low_confidence'] or session.low_confidence
    return recoresult



def get_still_check_rect(viewport):
    vw, vh = util.get_vwvh(viewport)
    return (68.241 * vh, 61.111 * vh, 100 * vw, 100 * vh)


if __name__ == '__main__':
    print(globals()[sys.argv[-2]](Image.open(sys.argv[-1])))
