from functools import lru_cache
from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np
# from skimage.measure import compare_mse
from PIL import Image

from util.richlog import get_logger
from . import imgops
from . import minireco
from . import resources


@dataclass
class RecognizedItem:
    name: str
    quantity: int
    low_confidence: bool = False


logger = get_logger(__name__)


@lru_cache(1)
def load_data():
    _, files = resources.get_entries('items')
    iconmats = {}
    itemmask = np.asarray(resources.load_image('common/itemmask.png', '1'))
    for filename in files:
        if filename.endswith('.png'):
            basename = filename[:-4]
            img = resources.load_image('items/' + filename, 'RGB')
            if img.size != (48, 48):
                img = img.resize((48, 48), Image.BILINEAR)
            mat = np.array(img)
            mat[itemmask] = 0
            iconmats[basename] = mat
    model = resources.load_pickle('minireco/NotoSansCJKsc-DemiLight-nums.dat')
    reco = minireco.MiniRecognizer(model, minireco.compare_ccoeff)
    return SimpleNamespace(itemmats=iconmats, num_recognizer=reco, itemmask=itemmask)


def tell_item(itemimg, with_quantity=True):
    logger.logimage(itemimg)
    cached = load_data()
    # l, t, r, b = scaledwh(80, 146, 90, 28)
    # print(l/itemimg.width, t/itemimg.height, r/itemimg.width, b/itemimg.height)
    # numimg = itemimg.crop(scaledwh(80, 146, 90, 28)).convert('L')
    low_confidence = False
    quantity = None
    if with_quantity:
        numimg = imgops.scalecrop(itemimg, 0.39, 0.71, 0.82, 0.84).convert('L')
        numimg = imgops.crop_blackedge2(numimg, 120)

        if numimg is not None:
            numimg = imgops.clear_background(numimg, 120)
            logger.logimage(numimg)
            numtext, score = cached.num_recognizer.recognize2(numimg, subset='0123456789万')
            logger.logtext('quantity: %s, minscore: %f' % (numtext, score))
            if score < 0.2:
                low_confidence = True
            quantity = int(numtext) if numtext.isdigit() else None


    # scale = 48/itemimg.height
    img4reco = np.array(itemimg.resize((48, 48), Image.BILINEAR).convert('RGB'))
    img4reco[cached.itemmask] = 0

    scores = []
    for name, templ in cached.itemmats.items():
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
        low_confidence = True
        name = None

    return RecognizedItem(name, quantity, low_confidence)
