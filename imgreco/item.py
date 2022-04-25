from functools import lru_cache
from dataclasses import dataclass
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

net_file = app.cache_path / 'ark_material.onnx'
index_file = app.cache_path / 'index_itemid_relation.json'

logger = logging.getLogger(__name__)

@lru_cache(1)
def _load_net():
    idx2id, id2idx, idx2name, idx2type = load_index_info()
    with open(net_file, 'rb') as f:
        data = f.read()
        net = cv2.dnn.readNetFromONNX(data)
    return net, idx2id, id2idx, idx2name, idx2type


@lru_cache(1)
def load_index_info():
    update_net()
    with open(index_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['idx2id'], data['id2idx'], data['idx2name'], data['idx2type']


def retry_get(url, max_retry=5, timeout=3):
    c = 0
    ex = None
    while c < max_retry:
        try:
            return requests.get(url, timeout=timeout)
        except Exception as e:
            c += 1
            ex = e
    raise ex


def update_net():
    local_cache_time = 0
    os.makedirs(os.path.dirname(index_file), exist_ok=True)
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            local_rel = json.load(f)
            local_cache_time = local_rel['time']
    logger.info('检查物品识别模型更新')
    resp = retry_get('https://cdn.jsdelivr.net/gh/triwinds/arknights-ml@latest/inventory/index_itemid_relation.json')
    remote_relation = resp.json()
    if remote_relation['time'] > local_cache_time:
        from datetime import datetime
        logger.info(f'更新物品识别模型, 模型生成时间: {datetime.fromtimestamp(remote_relation["time"]/1000).strftime("%Y-%m-%d %H:%M:%S")}')
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(remote_relation, f, ensure_ascii=False)
        resp = retry_get('https://cdn.jsdelivr.net/gh/triwinds/arknights-ml@latest/inventory/ark_material.onnx')
        with open(net_file, 'wb') as f:
            f.write(resp.content)
        _load_net.cache_clear()


def crop_item_middle_img(cv_item_img):
    # radius 60
    img_h, img_w = cv_item_img.shape[:2]
    ox, oy = img_w // 2, img_h // 2
    y1 = int(oy - 40)
    y2 = int(oy + 20)
    x1 = int(ox - 30)
    x2 = int(ox + 30)
    return cv_item_img[y1:y2, x1:x2]


def get_item_id(cv_img, box_size=137):
    cv_img = cv2.resize(cv_img, (box_size, box_size))
    mid_img = crop_item_middle_img(cv_img)
    ark_material_net, idx2id, id2idx, idx2name, idx2type = _load_net()
    blob = cv2.dnn.blobFromImage(mid_img)
    ark_material_net.setInput(blob)
    out = ark_material_net.forward()

    # Get a class with a highest score.
    out = out.flatten()
    probs = common.softmax(out)
    classId = np.argmax(out)
    return probs[classId], idx2id[classId], idx2name[classId], idx2type[classId]


@dataclass
class RecognizedItem:
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
        result = eng.recognize(numimg, char_whitelist='0123456789万', tessedit_pageseg_mode='13')
        qty_ocr = result.text.replace(' ', '').replace('万', '0000')
        richlogger.logtext(f'{qty_ocr=}')
        if not qty_ocr.isdigit():
            from . import itemdb
            qty_minireco, score = itemdb.num_recognizer.recognize2(numimg4legacy, subset='0123456789万')
            richlogger.logtext(f'{qty_minireco=}, {score=}')
            if score > 0.2:
                qty_ocr = qty_minireco
        return int(qty_ocr) if qty_ocr.isdigit() else None


def tell_item(itemimg, with_quantity=True, learn_unrecognized=False):
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

        prob, item_id, name, item_type = get_item_id(common.convert_to_cv(itemimg.convert('RGB')))
        richlogger.logtext(f'dnn matched {name} with prob {prob}')
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
            else:
                richlogger.logtext('no match')
                low_confidence = True
                name = None

    if name is None and learn_unrecognized:
        name = itemdb.add_item(itemimg)

    return RecognizedItem(name, quantity, low_confidence, item_type)
