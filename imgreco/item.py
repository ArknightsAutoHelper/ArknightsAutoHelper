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

    scale = 48/itemimg.height
    img4reco = itemimg.resize((int(itemimg.width*scale), 48), Image.BILINEAR).convert('RGB')

    scores = []
    for name, templ in recodata.items():
        if img4reco.size != templ.size:
            img1, img2 = imgops.uniform_size(img4reco, templ)
        else:
            img1, img2 = img4reco, templ
        scores.append((name, imgops.compare_mse(img1, img2)))
    
    # minmatch = min(scores, key=lambda x: x[1])
    # maxmatch = max(scores, key=lambda x: x[1])
    scores.sort(key=lambda x: x[1])
    logger.logtext(repr(scores[:5]))
    diffs = np.diff([a[1] for a in scores])
    if (diffs > 600).any():
        logger.logtext('matched %s with mse %f' % scores[0])
        name = scores[0][0]
    else:
        logger.logtext('no match')
        session.low_confidence = True
        name = None

    return (name, amount)
