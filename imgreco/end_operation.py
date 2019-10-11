import sys
import pickle

import numpy as np
from PIL import Image, ImageOps

from richlog import get_logger
from . import util
from . import imgops
from . import item
from . import minireco
from . import resources
from .util import any_in

LOGFILE = 'log/drop-recognition.html'

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
    threshold = height * (width/12)
    stars = []
    star1 = thstars[:, 0:starwidth]
    stars.append(np.count_nonzero(star1) > threshold)

    star2 = thstars[:, starwidth:starwidth*2]
    stars.append(np.count_nonzero(star2) > threshold)

    star3 = thstars[:, starwidth*2:]
    stars.append(np.count_nonzero(star3) > threshold)
    return tuple(stars)


recozh = minireco.MiniRecognizer(resources.load_pickle('minireco/NotoSansCJKsc-Medium.dat'))
reco_novecento_bold = minireco.MiniRecognizer(resources.load_pickle('minireco/Novecentosanswide_Bold.dat'))

grouptemplates = []
def _load_data():
    _, files = resources.get_entries('end_operation')
    for f in files:
        if f.endswith('.png'):
            grouptemplates.append((f[:-4], resources.load_image('end_operation/'+f, 'L')))


def tell_group(groupimg, session, bartop, barbottom, ):
    logger = get_logger(LOGFILE)
    logger.logimage(groupimg)
    grouptext = groupimg.crop((0, barbottom, groupimg.width, groupimg.height))

    thim = imgops.enhance_contrast(grouptext.convert('L'), 60)
    thim = imgops.crop_blackedge(thim)
    logger.logimage(thim)
    # groupname = recozh.recognize(thim)
    # logger.logtext(recozh.recognize(thim))

    # if len(recognized_groups) == 0 and any_in('首次', groupname):
    #     groupname = '首次掉落'
    # elif any_in('声望', groupname) and '声望&龙门币奖励' not in recognized_groups:
    #     groupname = '声望&龙门币奖励'
    # elif any_in('常规', groupname) and '常规掉落' not in recognized_groups:
    #     groupname = '常规掉落'
    # elif any_in('特殊', groupname) and '特殊掉落' not in recognized_groups:
    #     groupname = '特殊掉落'
    # elif any_in('幸运', groupname) and '幸运掉落' not in recognized_groups:
    #     groupname = '幸运掉落'
    # elif any_in('额物资', groupname) and '额外物资' not in recognized_groups:
    #     groupname = '额外物资'
    # elif any_in('报酬', groupname) and '报酬' not in recognized_groups:
    #     groupname = '报酬'
    # elif any_in('理智返还', groupname) and '理智返还' not in recognized_groups:
    #     groupname = '理智返还'

    comparsions = [(x[0], imgops.compare_ccoeff(*imgops.uniform_size(thim, x[1])))
                   for x in grouptemplates
                   if x[0] not in session.recognized_groups]
    comparsions.sort(key=lambda x: x[1], reverse=True)
    logger.logtext(repr(comparsions))
    groupname = comparsions[0][0]
    if comparsions[0][1] < 0.6:
        session.low_confidence = True
    if groupname == '幸运掉落':
        return (groupname, [('(家具)', 1)])

    vw, vh = session.vw, session.vh
    itemcount = roundint(groupimg.width / (20.370*vh))
    result = []
    for i in range(itemcount):
        itemimg = groupimg.crop((20.370*vh*i, 0.000*vh, 40.741*vh, 18.981*vh))
        # x1, _, x2, _ = (0.093*vh, 0.000*vh, 19.074*vh, 18.981*vh)
        itemimg = itemimg.crop((0.093*vh, 0, 19.074*vh, itemimg.height))
        result.append(item.tell_item(itemimg, session))
    return (groupname, result)


def find_jumping(ary, threshold):
    logger = get_logger(LOGFILE)
    ary = np.array(ary, dtype=np.int16)
    diffs = np.diff(ary)
    shit = [x for x in enumerate(diffs) if abs(x[1]) >= threshold]
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
            tuple(x[0] for x in group), weights=tuple(abs(x[1]) for x in group)))+1)
    return pts


def roundint(x): 
    return int(round(x))

# scale = 0


def check_level_up_popup(img):
    vw, vh = util.get_vwvh(img.size)

    ap_recovered_img = img.crop((50*vw+8.056*vh, 46.574*vh, 50*vw+24.907*vh, 51.296*vh)) # 理智已恢复
    ap_recovered_img = imgops.enhance_contrast(ap_recovered_img, 100, 225)
    ap_recovered_text = recozh.recognize(ap_recovered_img)
    return '理智' in ap_recovered_text


def check_end_operation(img):
    vw, vh = util.get_vwvh(img.size)

    operation_end_img = img.crop((4.722*vh, 80.278*vh, 56.389*vh, 93.889*vh))
    operation_end_img = imgops.image_threshold(operation_end_img, 225).convert('L')
    operation_end_img = imgops.scale_to_height(operation_end_img, 24)
    return '结束' in recozh.recognize(operation_end_img)

def get_dismiss_level_up_popup_rect(viewport):
    vw, vh = util.get_vwvh(viewport)
    return (100*vw-67.315*vh, 16.019*vh, 100*vw-5.185*vh, 71.343*vh)

get_dismiss_end_operation_rect = get_dismiss_level_up_popup_rect

def recognize(im):
    import time
    t0 = time.monotonic()
    vw, vh = util.get_vwvh(im.size)
    logger = get_logger(LOGFILE)

    lower = im.crop((0, 61.111*vh, 100*vw, 100*vh))
    logger.logimage(lower)

    operation_id = lower.crop((0, 4.444*vh, 23.611*vh, 11.388*vh)).convert('L')
    logger.logimage(operation_id)
    operation_id = imgops.enhance_contrast(imgops.crop_blackedge(operation_id), 80, 220)
    logger.logimage(operation_id)
    operation_id_str = reco_novecento_bold.recognize(operation_id).upper()
    # FIXME: recognizer can't recognize [0o], [-i] well (the game uses sᴍᴀʟʟ ᴄᴀᴘs and the font has sᴍᴀʟʟ ᴄᴀᴘs in ASCII range)
    # FIXME: currently, we have no 'o' and 'i' in recognizer data as '0' and '-' are used more frequently

    # operation_name = lower.crop((0, 14.074*vh, 23.611*vh, 20*vh)).convert('L')
    # operation_name = imgops.enhance_contrast(imgops.crop_blackedge(operation_name))
    # logger.logimage(operation_name)

    stars = lower.crop((23.611*vh, 6.759*vh, 53.241*vh, 16.944*vh))
    logger.logimage(stars)
    stars_status = tell_stars(stars)

    level = lower.crop((63.148*vh, 4.444*vh, 73.333*vh, 8.611*vh))
    logger.logimage(level)
    exp = lower.crop((76.852*vh, 5.556*vh, 94.074*vh, 7.963*vh))
    logger.logimage(exp)

    items = lower.crop((68.241*vh, 10.926*vh, lower.width, 35.000*vh))
    logger.logimage(items)

    x, y = 6.667*vh, 18.519*vh
    linedet = items.crop((x, y, x+1, items.height)).convert('L')
    d = np.asarray(linedet)
    linetop, linebottom, *_ = find_jumping(d.reshape(linedet.height), 32)
    linetop += y
    linebottom += y

    grouping = items.crop((0, linetop, items.width, linebottom))
    grouping = grouping.resize((grouping.width, 1), Image.BILINEAR)
    grouping = grouping.convert('L')

    logger.logimage(grouping.resize((grouping.width, 16)))

    d = np.array(grouping, dtype=np.int16)[0]
    points = [0, *find_jumping(d, 32)]
    assert(len(points) % 2 == 0)
    finalgroups = list(zip(*[iter(points)]*2))  # each_slice(2)
    logger.logtext(repr(finalgroups))

    imggroups = [items.crop((x1, 0, x2, items.height))
                 for x1, x2 in finalgroups]
    items = []

    session = RecognizeSession()
    session.vw = vw
    session.vh = vh

    for group in imggroups:
        result = tell_group(group, session, linetop, linebottom)
        session.recognized_groups.append(result[0])
        items.append(result)
        

    t1 = time.monotonic()
    if session.low_confidence:
        logger.logtext('LOW CONFIDENCE')
    logger.logtext('time elapsed: %f' % (t1-t0))
    return {
        'operation': operation_id_str,
        'stars': stars_status,
        'items': items,
        'low_confidence': session.low_confidence
    }


_load_data()


if __name__ == '__main__':
    print(globals()[sys.argv[-2]](Image.open(sys.argv[-1])))
