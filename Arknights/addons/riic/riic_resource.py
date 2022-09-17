import sys
from pathlib import Path
from imgreco import resources
import os
import glob
import pickle
import io
import numpy as np
from util import cvimage as Image
from imgreco import imgops
import logging
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

icon_size = (36, 36)

pack_version: str = ''
icon_names: list[str]
normal_icons_stack: NDArray[np.float32]
dark_icons_stack: NDArray[np.float32]

portrait_names: list[str]
portrait_stack: NDArray[np.float32]
portrait_select_stack: NDArray[np.float32]

portrait_mask = resources.load_image('riic/portrait_mask.png', 'RGBA')
portrait_mask_64 = portrait_mask.resize((32, 64), Image.BILINEAR)

select_tint = np.array([0, 152, 220], dtype=np.float32)
select_alpha = np.float32(0.2)

__store_keys__ = ['pack_version', 'gamedata_version', 'icon_names', 'normal_icons_stack', 'dark_icons_stack', 'portrait_names', 'portrait_stack']

def build_pack(repopath: Path):
    icon_names = []
    normal_icons = []
    dark_icons = []

    with open(repopath / 'version', 'r', encoding='utf-8') as f:
        pack_version = f.read()

    with open(repopath / 'gamedata' / 'excel' / 'data_version.txt', 'r', encoding='utf-8') as f:
        gamedata_version = f.read()

    for file in glob.glob(str(repopath / 'building_skill' / '*.png')):
        name = os.path.basename(file)[:-4]
        if name.startswith('[style]'):
            continue
        im = Image.imread(file).convert('RGBA')
        if im.size != icon_size:
            im = im.resize(icon_size, Image.BILINEAR)
        background = np.full((im.height, im.width, 3), 32)
        alpha = im.array[..., 3] / 255.0
        normal_blendf = (im.array[..., 0:3] * alpha[..., np.newaxis] + (1-alpha[..., np.newaxis]) * background)
        normal_blend = normal_blendf.astype(np.uint8)
        normal_select = (normal_blendf * (1-select_alpha) + select_alpha * select_tint)

        alpha = alpha / 2.0
        dark_blendf = (im.array[..., 0:3] * alpha[..., np.newaxis] + (1-alpha[..., np.newaxis]) * background)
        dark_blend = dark_blendf.astype(np.uint8)
        dark_select = (dark_blendf * (1-select_alpha) + select_alpha * select_tint)
        icon_names.append(name)
        normal_icons.append(normal_blend)
        dark_icons.append(dark_blend)
    normal_icons_stack = np.concatenate([img[None, ...] for img in normal_icons]).astype(np.float32)
    dark_icons_stack = np.concatenate([img[None, ...] for img in dark_icons]).astype(np.float32)

    portrait_names = []
    portrait_images = []
    all_portrait_files = glob.glob(str(repopath / 'portrait' / '*.png'))
    for filename in all_portrait_files:
        portrait_names.append(os.path.basename(filename)[:-4])
        img = Image.open(filename).convert('RGBA').resize((32, 64), Image.BILINEAR)
        grayimg = img.convert('L')
        grayalpha_img = np.dstack((grayimg.array, img.array[..., -1]))
        select_img = (img.array[..., :3] * (1-select_alpha) + select_alpha * select_tint)
        grayselect_img = np.dstack((Image.fromarray(select_img.astype(np.uint8), 'RGB').convert('L').array, img.array[..., -1]))
        portrait_images.append(grayalpha_img)
    portrait_stack = np.concatenate([img[None, ...] for img in portrait_images]).astype(np.float32)

    locals_dump = locals()
    store = {k: locals_dump[k] for k in __store_keys__}
    return store


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        # allow fundamental types and ndarray.
        if module == "numpy.core.multiarray" and name == '_reconstruct':
            from numpy.core.multiarray import _reconstruct
            return _reconstruct
        if module == "numpy" and name == 'ndarray':
            return np.ndarray
        if module == "numpy" and name == 'dtype':
            return np.dtype
        # Forbid everything else.
        raise pickle.UnpicklingError(f"module {module} type {name} is forbidden")


def load_pack(stream):
    import lzma
    import time
    with lzma.LZMAFile(stream, 'rb') as f:
        store = RestrictedUnpickler(f).load()
    return store

def refresh_pack():
    try:
        from Arknights.gamedata_loader import session
        resp = session.get('https://gh.cirno.xyz/github.com/ArknightsAutoHelper/ArknightsAutoHelper/releases/download/riic_pack/riic_pack.xz')
        if pack_version != '' and resp.from_cache:
            return
        resp.raise_for_status()
        bio = io.BytesIO(resp.content)
    except:
        if pack_version != '':
            return
        import app
        bio = open(app.cache_path / 'riic_pack.xz', 'rb')
    store = load_pack(bio)
    from Arknights import gamedata_loader
    if store['gamedata_version'].strip() != gamedata_loader.get_version().strip():
        logger.warning('riic_pack gamedata version mismatch')
    bio.close()
    for k in __store_keys__:
        globals()[k] = store[k]

def update_pack(filename):
    import lzma
    import requests
    import subprocess
    import app
    need_update = True
    try:
        current_pack = requests.get('https://github.com/ArknightsAutoHelper/ArknightsAutoHelper/releases/download/riic_pack/riic_pack.xz').content
        current_version = requests.get('https://raw.githubusercontent.com/yuanyan3060/Arknights-Bot-Resource/main/version').content.decode('utf-8').strip()
        bio = io.BytesIO(lzma.decompress(current_pack))
        current_store = RestrictedUnpickler(bio).load()
        if current_store['pack_version'] == current_version:
            need_update = False
    except:
        pass
    if not need_update:
        return False
    repopath = app.cache_path / 'teddy-pack'
    if (repopath / '.git').is_dir():
        subprocess.run(['git', 'reset', '--hard', 'origin/main'], check=True, cwd=repopath)
        subprocess.run(['git', 'clean', '-fd'], check=True, cwd=repopath)
        subprocess.run(['git', 'pull', '--ff-only', 'origin', 'main'], check=True, cwd=repopath)
    else:
        subprocess.run(['git', 'clone', '--depth=1', 'https://github.com/yuanyan3060/Arknights-Bot-Resource', str(repopath)], check=True)
    store = build_pack(repopath)
    with lzma.LZMAFile(filename, 'wb') as f:
        pickle.dump(store, f)
    return True

if __name__ == '__main__':
    sys.exit(not update_pack(sys.argv[1]))
