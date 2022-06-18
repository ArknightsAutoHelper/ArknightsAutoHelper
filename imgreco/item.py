from functools import lru_cache
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from types import SimpleNamespace

import numpy as np
import cv2
import json
# from skimage.measure import compare_mse
from util import cvimage as Image
import requests
import os
import logging
import app

from util.richlog import get_logger
from . import imgops
from . import minireco
from . import resources
from . import common



logger = logging.getLogger(__name__)



def crop_item_middle_img(cv_item_img):
    # radius 60
    img_h, img_w = cv_item_img.shape[:2]
    ox, oy = img_w // 2, img_h // 2
    y1 = int(oy - 40)
    y2 = int(oy + 20)
    x1 = int(ox - 30)
    x2 = int(ox + 30)
    return cv_item_img[y1:y2, x1:x2]


def predict_item_dnn(cv_img, box_size=137):
    cv_img = cv2.resize(cv_img, (box_size, box_size))
    mid_img = crop_item_middle_img(cv_img)
    from .itemdb import load_net, dnn_items_by_class
    ark_material_net = load_net()
    blob = cv2.dnn.blobFromImage(mid_img)
    ark_material_net.setInput(blob)
    out = ark_material_net.forward()

    # Get a class with a highest score.
    out = out.flatten()
    probs = common.softmax(out)
    classId = np.argmax(out)
    return probs[classId], dnn_items_by_class[classId]


@dataclass_json
@dataclass
class RecognizedItem:
    item_id: str
    name: str
    quantity: int
    low_confidence: bool = False
    item_type: str = None


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


def all_known_items():
    from . import itemdb
    return itemdb.resources_known_items.keys()


def get_quantity(itemimg):
    richlogger = get_logger(__name__)
    numimg = imgops.scalecrop(itemimg, 0.39, 0.71, 0.82, 0.855).convert('L')
    numimg = imgops.crop_blackedge2(numimg, 120)
    if numimg is not None:
        numimg = imgops.clear_background(numimg, 120)
        numimg4legacy = numimg
        numimg = imgops.pad(numimg, 8, 0)
        numimg = imgops.invert_color(numimg)
        richlogger.logimage(numimg)
        from .ocr import acquire_engine_global_cached
        eng = acquire_engine_global_cached('zh-cn')
        from imgreco.ocr import OcrHint
        result = eng.recognize(numimg, char_whitelist='0123456789.万', tessedit_pageseg_mode='13',
                               hints=[OcrHint.SINGLE_LINE])
        qty_text = result.text
        richlogger.logtext(f'{qty_text=}')
        try:
            try:
                qty_base = float(qty_text.replace(' ', '').replace('万', ''))
            except:
                from . import itemdb
                qty_minireco, score = itemdb.num_recognizer.recognize2(numimg4legacy, subset='0123456789.万')
                richlogger.logtext(f'{qty_minireco=}, {score=}')
                if score > 0.2:
                    qty_text = qty_minireco
                    qty_base = float(qty_text.replace('万', ''))
            qty_scale = 10000 if '万' in qty_text else 1
            return int(qty_base * qty_scale)
        except:
            return None
    

def tell_item(itemimg, with_quantity=True, learn_unrecognized=False) -> RecognizedItem:
    richlogger = get_logger(__name__)
    richlogger.logimage(itemimg)
    from . import itemdb
    # l, t, r, b = scaledwh(80, 146, 90, 28)
    # print(l/itemimg.width, t/itemimg.height, r/itemimg.width, b/itemimg.height)
    # numimg = itemimg.crop(scaledwh(80, 146, 90, 28)).convert('L')
    low_confidence = False
    quantity = None
    if with_quantity:
        quantity = get_quantity(itemimg)

    prob, dnnitem = predict_item_dnn(itemimg.array)
    item_id = dnnitem.item_id
    name = dnnitem.item_name
    item_type = dnnitem.item_type
    richlogger.logtext(f'dnn matched {dnnitem} with prob {prob}')
    if prob < 0.8 or item_id == 'other':
# scale = 48/itemimg.height
        img4reco = np.array(itemimg.resize((48, 48), Image.BILINEAR).convert('RGB'))
        img4reco[itemdb.itemmask] = 0

        scores = []
        for name, templ in itemdb.itemmats.items():
            scores.append((name, imgops.compare_mse(img4reco, templ)))

        scores.sort(key=lambda x: x[1])
        itemname, score = scores[0]
        # maxmatch = max(scores, key=lambda x: x[1])
        richlogger.logtext(repr(scores[:5]))
        diffs = np.diff([a[1] for a in scores])
        item_type = None
        if score < 800 and np.any(diffs > 600):
            richlogger.logtext('matched %s with mse %f' % (itemname, score))
            name = itemname
            dnnitem = itemdb.dnn_items_by_item_name.get(itemname)
            if dnnitem is not None:
                item_id = dnnitem.item_id
        else:
            richlogger.logtext('no match')
            low_confidence = True
            item_id = None
            name = '未知物品'

    if item_id is None and learn_unrecognized:
        name = itemdb.add_item(itemimg)

    return RecognizedItem(item_id, name, quantity, low_confidence, item_type)
