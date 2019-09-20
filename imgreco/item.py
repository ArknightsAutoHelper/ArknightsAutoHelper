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
    root = os.path.join(os.path.dirname(__file__), 'resources', 'items')
    _, _, files = next(os.walk(root))
    iconmats = {}
    for filename in files:
        if filename.endswith('.png'):
            basename = filename[:-4]
            mat = np.asarray(Image.open(os.path.join(root, filename)).convert('RGB'))
            iconmats[basename] = mat
    reco = minireco.MiniRecognizer(resources.load_pickle('minireco/NotoSansCJKsc-DemiLight-nums.dat'))
    return (iconmats, reco)



def tell_item(itemimg):
    logger = get_logger(LOGFILE)
    #l, t, r, b = scaledwh(80, 146, 90, 28)
    #print(l/itemimg.width, t/itemimg.height, r/itemimg.width, b/itemimg.height)
    #numimg = itemimg.crop(scaledwh(80, 146, 90, 28)).convert('L')
    numimg = imgops.scalecrop(itemimg, 0.39, 0.71, 0.82, 0.84).convert('L')
    numimg = imgops.crop_blackedge2(numimg, 220)
    if numimg is not None:
        numimg = imgops.enhance_contrast(numimg)
        logger.logimage(numimg)
        recodata, textreco = load_data()
        numtext: str = textreco.recognize(numimg)
        logger.logtext('amount: '+numtext)
        amount = int(numtext) if numtext.isdigit() else None
    else:
        amount = None

    scale = 48/itemimg.height
    img4reco = itemimg.resize((int(itemimg.width*scale), 48), Image.BILINEAR).convert('RGB')

    scores = []
    for name, mat2 in recodata.items():
        if img4reco.size != mat2.shape[:2][::-1]:
            mat1 = np.asarray(img4reco.resize(mat2.shape[:2][::-1], Image.NEAREST))
        else:
            mat1 = np.asarray(img4reco)
        scores.append((name, imgops.compare_mse(mat1, mat2)))
    
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
        name = None

    return (name, amount)
