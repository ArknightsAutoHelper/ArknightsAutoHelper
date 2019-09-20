import sys
import pickle
from functools import lru_cache

import numpy as np
from PIL import Image, ImageOps

from richlog import get_logger
from . import imgops
from . import item
from . import minireco
from . import resources

LOGFILE = 'log/b4op.html'

@lru_cache(1)
def load_data():
    reco = minireco.MiniRecognizer(resources.load_pickle('minireco/NotoSansCJKsc-Medium.dat'))
    reco2 = minireco.MiniRecognizer(resources.load_pickle('minireco/Novecentosanswide_Medium.dat'))
    return (reco, reco2)

def recognize(img):
    logger = get_logger(LOGFILE)
    vw, vh = (x/100 for x in img.size)

    apimg = img.crop((100*vw - 22.917*vh, 2.917*vh, 100*vw, 8.194*vh)).convert('L')
    reco_Noto, reco_Novecento = load_data()
    apimg = imgops.enhance_contrast(apimg, 80, 255)
    logger.logimage(apimg)
    aptext = reco_Noto.recognize(apimg)
    logger.logtext(aptext)
    # print("AP:", aptext)

    opidimg = img.crop((100*vw-55.694*vh, 11.667*vh, 100*vw-44.028*vh, 15.139*vh)).convert('L')
    opidimg = imgops.enhance_contrast(opidimg, 80, 255)
    logger.logimage(opidimg)
    opidtext = reco_Novecento.recognize(opidimg)
    if opidtext.endswith('-'):
        opidtext = opidtext[:-1]
    opidtext = opidtext.upper()
    logger.logtext(opidtext)
    # print('operation:', opidtext)

    delegateimg = img.crop((100*vw-32.778*vh, 79.444*vh, 100*vw-4.861*vh, 85.417*vh)).convert('L')
    logger.logimage(delegateimg)
    score = np.count_nonzero(np.asarray(delegateimg) > 127) / (delegateimg.width*delegateimg.height)
    delegated = score > 0.5
    # print('delegated:', delegated)

    consumeimg = img.crop((100*vw-14.306*vh, 94.028*vh, 100*vw-7.222*vh, 97.361*vh)).convert('L')
    consumeimg = imgops.enhance_contrast(consumeimg, 80, 255)
    logger.logimage(consumeimg)
    consumetext = reco_Noto.recognize(consumeimg)
    consumetext = ''.join(c for c in consumetext if c in '0123456789')
    logger.logtext(consumetext)
    
    return {
        'AP': aptext,
        'operation': opidtext,
        'delegated': delegated,
        'consume': int(consumetext)
    }
    # print('consumption:', consumetext)

if __name__ == "__main__":
    print(recognize(Image.open(sys.argv[-1])))
