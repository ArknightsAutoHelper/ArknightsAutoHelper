import cv2 as cv
import numpy as np
from PIL import Image

from richlog import get_logger
from . import imgops
from . import resources
from . import util
from . import ocr

LOGFILE = 'recruit.html'
logger = get_logger(LOGFILE)

def get_recruit_tags(img):
    vw, vh = util.get_vwvh(img)
    tagimgs = [
        img.crop((50*vw-36.481*vh, 50.185*vh, 50*vw-17.315*vh, 56.111*vh)).convert('L'),
        img.crop((50*vw-13.241*vh, 50.185*vh, 50*vw+6.111*vh, 56.111*vh)).convert('L'),
        img.crop((50*vw+10.000*vh, 50.185*vh, 50*vw+29.259*vh, 56.111*vh)).convert('L'),
        img.crop((50*vw-36.481*vh, 60.278*vh, 50*vw-17.315*vh, 66.019*vh)).convert('L'),
        img.crop((50*vw-13.241*vh, 60.278*vh, 50*vw+6.111*vh, 66.019*vh)).convert('L')
    ]

    tags = [ocr.engine.recognize(imgops.invert_color(img), 'zh-cn', hints=[ocr.OcrHint.SINGLE_LINE]).text.replace(' ', '') for img in tagimgs]

    for tagimg, tagtext in zip(tagimgs, tags):
        logger.logimage(tagimg)
        logger.logtext(tagtext)

    return tags
