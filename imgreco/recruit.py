import cv2 as cv
import numpy as np
from PIL import Image

from util.richlog import get_logger
from . import imgops
from . import resources
from . import util
from . import ocr

LOGFILE = 'recruit.html'
logger = get_logger(LOGFILE)

from Arknights.recruit_database import recruit_database
known_tagchars = set(z for x in recruit_database for y in x[2] for z in y)

def remove_unknown_chars(s, known_chars):
    result = ''.join(c for c in s if c in known_chars)
    return result

def get_recruit_tags(img):
    vw, vh = util.get_vwvh(img)
    tagimgs = [
        img.crop((50*vw-36.481*vh, 50.185*vh, 50*vw-17.315*vh, 56.111*vh)).convert('L'),
        img.crop((50*vw-13.241*vh, 50.185*vh, 50*vw+6.111*vh, 56.111*vh)).convert('L'),
        img.crop((50*vw+10.000*vh, 50.185*vh, 50*vw+29.259*vh, 56.111*vh)).convert('L'),
        img.crop((50*vw-36.481*vh, 60.278*vh, 50*vw-17.315*vh, 66.019*vh)).convert('L'),
        img.crop((50*vw-13.241*vh, 60.278*vh, 50*vw+6.111*vh, 66.019*vh)).convert('L')
    ]

    eng = ocr.acquire_engine_global_cached('zh-cn')
    recognize = lambda img: eng.recognize(imgops.invert_color(img), int(vh * 20),  hints=[ocr.OcrHint.SINGLE_LINE]).text
    tags = [remove_unknown_chars(recognize(img), known_tagchars) for img in tagimgs]

    for tagimg, tagtext in zip(tagimgs, tags):
        logger.logimage(tagimg)
        logger.logtext(tagtext)

    return tags
