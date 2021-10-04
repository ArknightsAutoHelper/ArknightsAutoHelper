import cv2 as cv
import numpy as np
from util import cvimage as Image

from util.richlog import get_logger
from . import imgops
from . import resources
from . import util
from . import ocr

LOGFILE = 'recruit.html'
logger = get_logger(__name__)

from resources.recruit_database import recruit_database
known_tags = set(y for x in recruit_database for y in x[2])
known_tags.update(('资深干员', '高级资深干员'))
known_tagchars = ''.join(set(c for t in known_tags for c in t))

def remove_unknown_chars(s, known_chars):
    result = ''.join(c for c in s if c in known_chars)
    return result

def get_recruit_tags(img):
    import textdistance
    vw, vh = util.get_vwvh(img)
    tagimgs = [
        img.crop((50*vw-36.481*vh, 50.185*vh, 50*vw-17.315*vh, 56.111*vh)).convert('L'),
        img.crop((50*vw-13.241*vh, 50.185*vh, 50*vw+6.111*vh, 56.111*vh)).convert('L'),
        img.crop((50*vw+10.000*vh, 50.185*vh, 50*vw+29.259*vh, 56.111*vh)).convert('L'),
        img.crop((50*vw-36.481*vh, 60.278*vh, 50*vw-17.315*vh, 66.019*vh)).convert('L'),
        img.crop((50*vw-13.241*vh, 60.278*vh, 50*vw+6.111*vh, 66.019*vh)).convert('L')
    ]

    eng = ocr.acquire_engine_global_cached('zh-cn')
    recognize = lambda img: eng.recognize(imgops.invert_color(img), int(vh * 20), hints=[ocr.OcrHint.SINGLE_LINE], char_whitelist=known_tagchars).text.replace(' ', '')
    cookedtags = []
    for img in tagimgs:
        logger.logimage(img)
        tag = recognize(img)
        logger.logtext(tag)
        if not tag:
            continue
        if tag in known_tags:
            cookedtags.append(tag)
            continue
        distances = [(target, textdistance.levenshtein(tag, target)) for target in known_tags.difference(cookedtags)]
        distances.sort(key=lambda x: x[1])
        mindistance = distances[0][1]
        matches = [x[0] for x in distances if x[1] == mindistance]
        if mindistance > 2:
            logger.logtext('autocorrect: minimum distance %d too large' % mindistance)
            cookedtags.append(tag)
        elif len(matches) == 1:
            logger.logtext('autocorrect to %s, distance %d' % (matches[0], mindistance))
            cookedtags.append(matches[0])
        else:
            logger.logtext('autocorrect: failed to match in %s with distance %d' % (','.join(matches), mindistance))
            cookedtags.append(tag)

    return cookedtags
