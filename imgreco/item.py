import os
import pickle
from functools import lru_cache

import numpy as np
from . import imgops
# from skimage.measure import compare_mse
from PIL import Image

from . import minireco
from . import resources
from richlog import get_logger

LOGFILE = 'log/item-recognition.html'

itemmask = np.asarray(resources.load_image('common/itemmask.png', '1'))


@lru_cache(1)
def load_data():
    _, files = resources.get_entries('items')
    iconmats = {}
    for filename in files:
        if filename.endswith('.png'):
            basename = filename[:-4]
            mat = resources.load_image('items/'+filename, 'RGB')
            iconmats[basename] = mat
    reco = minireco.MiniRecognizer(resources.load_pickle('minireco/NotoSansCJKsc-DemiLight-nums.dat'))
    return (iconmats, reco)


def tell_item(itemimg, session):
    logger = get_logger(LOGFILE)
    logger.logimage(itemimg)
    #l, t, r, b = scaledwh(80, 146, 90, 28)
    #print(l/itemimg.width, t/itemimg.height, r/itemimg.width, b/itemimg.height)
    #numimg = itemimg.crop(scaledwh(80, 146, 90, 28)).convert('L')
    numimg = imgops.scalecrop(itemimg, 0.39, 0.71, 0.82, 0.84).convert('L')
    numimg = imgops.crop_blackedge2(numimg, 220)
    recodata, textreco = load_data()
    if numimg is not None:
        numimg = imgops.enhance_contrast(numimg)
        logger.logimage(numimg)
        numtext: str = textreco.recognize(numimg)
        logger.logtext('amount: '+numtext)
        amount = int(numtext) if numtext.isdigit() else None
    else:
        amount = None

    # scale = 48/itemimg.height
    img4reco = np.array(itemimg.resize((48, 48), Image.BILINEAR).convert('RGB'))
    img4reco[itemmask] = 0
    
    scores = []
    for name, templ in recodata.items():
        if templ.size != (48, 48):
            templ = templ.resize((48, 48), Image.BILINEAR)
        scores.append((name, imgops.compare_mse(img4reco, templ)))

    scores.sort(key=lambda x: x[1])
    itemname, score = scores[0]
    # maxmatch = max(scores, key=lambda x: x[1])
    logger.logtext(repr(scores[:5]))
    diffs = np.diff([a[1] for a in scores])
    if score < 800 and np.any(diffs > 600):
        logger.logtext('matched %s with mse %f' % (itemname, score))
        name = itemname
    else:
        logger.logtext('no match')
        session.low_confidence = True
        name = None

    return (name, amount)
