import os
import numpy as np
from PIL import Image

def _update_mat_collection(collection, name, img):
    global itemmask
    if img.size != (48, 48):
        img = img.resize((48, 48), Image.BILINEAR)
    mat = np.array(img)
    mat[itemmask] = 0
    collection[name] = mat

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

    resources_known_items = {}
    for prefix in ['items', 'items/archive', 'items/not-loot']:
        _, files = resources.get_entries(prefix)
        for filename in files:
            itemname = filename[:-4] if filename.endswith('.png') else filename
            path = prefix + '/' + filename
            resources_known_items[itemname] = resources.resolve(path)
    update_extra_items()


def update_extra_items():
    import config

    new_mtime = os.path.getmtime(config.extra_items_path)

    if new_mtime <= update_extra_items.old_mtime:
        return
    from . import resources
    import time
    from glob import glob
    extra_files = [(os.path.basename(x)[:-4], resources.FileSystemIndex(x)) for x in glob(os.path.join(config.extra_items_path, '*.png'))]
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
    from . import resources
    import config
    date = time.strftime('%Y-%m-%d')
    index = add_item.last_index + 1
    while True:
        name = '未知物品-%s-%d' % (date, index)
        filename = os.path.join(config.extra_items_path, name+'.png')
        if not os.path.exists(filename):
            break
        index += 1
    add_item.last_index = index
    image.save(filename)
    update_extra_items()
    return name

add_item.last_index = 0

load()
