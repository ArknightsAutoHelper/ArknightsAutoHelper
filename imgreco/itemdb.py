from dataclasses import dataclass
import os
import logging
import json
from functools import lru_cache

import cv2
import numpy as np

import app
from util import cvimage as Image

logger = logging.getLogger(__name__)

net_file = app.cache_path / 'ark_material.onnx'
index_file = app.cache_path / 'index_itemid_relation.json'
model_timestamp = 0

@dataclass
class DnnItemRecord:
    class_id: int
    item_id: str
    item_name: str
    item_type: str

dnn_items_by_class : dict[int, DnnItemRecord] = {}
dnn_items_by_item_id : dict[str, DnnItemRecord] = {}
dnn_items_by_item_name : dict[str, DnnItemRecord] = {}

@lru_cache(1)
def load_net():
    update_index_info()
    with open(net_file, 'rb') as f:
        data = f.read()
        net = cv2.dnn.readNetFromONNX(data)
    return net


@lru_cache(1)
def _update_index_info():
    with open(index_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    global model_timestamp
    model_timestamp = data['time']
    idx2id, id2idx, idx2name, idx2type = data['idx2id'], data['id2idx'], data['idx2name'], data['idx2type']
    dnn_items_by_class.clear()
    dnn_items_by_item_id.clear()
    dnn_items_by_item_name.clear()
    for index, item_id in enumerate(idx2id):
        record = DnnItemRecord(index, item_id, idx2name[index], idx2type[index])
        dnn_items_by_class[index] = record
        dnn_items_by_item_id[item_id] = record
        dnn_items_by_item_name[idx2name[index]] = record

def update_index_info():
    update_net()
    return _update_index_info()

def retry_get(url, max_retry=5, timeout=3):
    import requests
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
    import time
    os.makedirs(os.path.dirname(index_file), exist_ok=True)
    try:
        stat = os.stat(index_file)
        cache_mtime = stat.st_mtime
        with open(index_file, 'r', encoding='utf-8') as f:
            local_rel = json.load(f)
            model_gen_time = local_rel['time'] / 1000
        now = time.time()
        logger.debug(f'{cache_mtime=} {now=} {model_gen_time=}')
        if cache_mtime > model_gen_time and now - cache_mtime < 60 * 60 * 8:
            return
    except:
        pass
    logger.info('检查物品识别模型更新')
    resp = retry_get('https://gh.cirno.xyz/raw.githubusercontent.com/triwinds/arknights-ml/master/inventory/index_itemid_relation.json')
    remote_relation = resp.json()
    if remote_relation['time'] > local_cache_time:
        from datetime import datetime
        logger.info(f'更新物品识别模型, 模型生成时间: {datetime.fromtimestamp(remote_relation["time"]/1000).strftime("%Y-%m-%d %H:%M:%S")}')
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(remote_relation, f, ensure_ascii=False)
        resp = retry_get('https://gh.cirno.xyz/raw.githubusercontent.com/triwinds/arknights-ml/master/inventory/ark_material.onnx')
        with open(net_file, 'wb') as f:
            f.write(resp.content)
        _update_index_info.cache_clear()
    else:
        os.utime(index_file, None)


def _update_mat_collection(collection, name, img):
    global itemmask
    if img.size != (48, 48):
        img = img.resize((48, 48), Image.BILINEAR)
    mat = np.array(img)
    mat[itemmask] = 0
    collection[name] = mat


resources_known_items = {}


def load():
    from . import resources
    from . import minireco
    resource_files = [(x[:-4], resources.resolve('items/' + x)) for x in resources.get_entries('items')[1] if x.endswith('.png')]
    global resources_itemmats, num_recognizer, itemmask, resources_known_items
    resources_itemmats = {}
    itemmask = np.asarray(resources.load_image('common/itemmask.png', '1'))
    for name, index in resource_files:
        img = resources.load_image(index, 'RGB')
        _update_mat_collection(resources_itemmats, name, img)

    model = resources.load_pickle('minireco/NotoSansCJKsc-DemiLight-nums.dat')
    reco = minireco.MiniRecognizer(model, minireco.compare_ccoeff)
    num_recognizer=reco

    for prefix in ['items', 'items/archive', 'items/not-loot']:
        _, files = resources.get_entries(prefix)
        for filename in files:
            itemname = filename[:-4] if filename.endswith('.png') else filename
            path = prefix + '/' + filename
            resources_known_items[itemname] = resources.resolve(path)
    update_extra_items()


def update_extra_items():
    import app

    new_mtime = os.path.getmtime(app.extra_items_path)

    if new_mtime <= update_extra_items.old_mtime:
        return
    from . import resources
    from glob import glob
    extra_files = [(os.path.basename(x)[:-4], resources.FileSystemIndex(x)) for x in glob(os.path.join(
        app.extra_items_path, '*.png'))]
    extra_known_items = {}
    extra_itemmats = {}
    for key, value in extra_files:
        for name, index in extra_files:
            img = resources.load_image(index, 'RGB')
            _update_mat_collection(extra_itemmats, name, img)
        extra_known_items[key] = value
    global itemmats
    itemmats = {}
    itemmats.update(resources_itemmats)
    itemmats.update(extra_itemmats)
    global all_known_items
    all_known_items = {}
    all_known_items.update(resources_known_items)
    all_known_items.update(extra_known_items)
    update_extra_items.old_mtime = new_mtime

update_extra_items.old_mtime = 0

def add_item(image) -> str:
    import os
    import time
    import app
    date = time.strftime('%Y-%m-%d')
    index = add_item.last_index + 1
    while True:
        name = '未知物品-%s-%d' % (date, index)
        filename = app.extra_items_path.joinpath(name + '.png')
        if not os.path.exists(filename):
            break
        index += 1
    add_item.last_index = index
    image.save(filename)
    update_extra_items()
    return name

add_item.last_index = 0

load()
