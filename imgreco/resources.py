from __future__ import annotations
import os
import pickle
from functools import lru_cache
import json
from typing import TYPE_CHECKING
import cv2
import numpy as np
from util import cvimage as Image

import app

class ResourceArchiveIndex:
    def __init__(self, archive, archive_path):
        self.archive = archive
        self.archive_path = archive_path
    def open(self):
        return self.archive.open(self.archive_path, 'r')
    def __hash__(self):
        return hash((ResourceArchiveIndex, self.archive, self.archive_path))

class FileSystemIndex:
    def __init__(self, path):
        self.path = path
    def open(self):
        return open(self.path, 'rb')
    def __hash__(self):
        return hash((FileSystemIndex, self.path))

if app.use_archived_resources:
    import zipfile
    root = 'resources/imgreco'
    archive = zipfile.ZipFile(open(app.resource_archive, 'rb'), 'r')

    filelist = archive.namelist()

    def get_path(names):
        return '/'.join([root, *names])

    def _open_file(path):
        return archive.open(path)

    def _get_index(names):
        archive_path = get_path(names)
        try:
            info = archive.getinfo(archive_path)
            return ResourceArchiveIndex(archive, info.filename)
        except KeyError:
            return None

    def get_entries(base):
        prefix = 'resources/imgreco/' + base + '/'
        dirs = []
        files = []
        for name in filelist:
            if name.startswith(prefix):
                name = name[len(prefix):]
                if len(name) == 0:
                    continue
                elif name[-1] == '/':
                    dirs.append(name[:-1])
                elif '/' in name:
                    continue
                else:
                    files.append(name)
        return dirs, files
else:
    root = app.resource_root.joinpath('imgreco')

    def get_path(names):
        return root.joinpath(*names)

    def _get_index(names):
        path = get_path(names)
        fspath = root.joinpath(path)
        if os.path.exists(fspath):
            return FileSystemIndex(fspath)
        else:
            return None

    def _open_file(path):
        return open(path, 'rb')

    def get_entries(base):
        findroot = get_path(base.split('/'))
        for _, dirs, files in os.walk(findroot):
            return (dirs, files)
        return ([], [])


def resolve(respath):
    names = respath.split('/')
    return _get_index(names)


def open_file(respath):
    if hasattr(respath, 'open'):
        return respath.open()
    return resolve(respath).open()


def load_image(name, mode=None, imread_flags=None) -> Image.Image:
    if imread_flags is None:
        im = Image.open(open_file(name))
        if mode is not None and im.mode != mode:
            im = im.convert(mode)
    else:
        im = Image.open(open_file(name), imread_flags)
    return im


@lru_cache(maxsize=None)
def load_image_cached(name, mode=None, imread_flags=None):
    return load_image(name, mode, imread_flags)


def load_image_as_ndarray(name):
    return np.asarray(load_image(name))


def load_pickle(name):
    with open_file(name) as f:
        result = pickle.load(f)
    return result


def load_minireco_model(name, filter_chars=None):
    model = load_pickle(name)
    if filter_chars is not None:
        model['data'] = [x for x in model['data'] if x[0] in filter_chars]
        model['chars'] = [x[0] for x in model['data']]
    return model


if TYPE_CHECKING:
    from .common import RegionOfInterest as RegionOfInterest_ghost

def load_roi(basename, image_mode='RGB', metafile=None, imgfile=None) -> RegionOfInterest_ghost:
    from .common import RegionOfInterest
    if metafile is None:
        metafile = basename + '.roi.json'
    if imgfile is None:
        imgfile = basename + '.png'
    imgfileindex = resolve(imgfile)
    raw_img = load_image_cached(imgfileindex, imread_flags=cv2.IMREAD_UNCHANGED) if imgfileindex is not None else None
    mask = None
    if raw_img is not None:
        if raw_img.mode.endswith('A'):
            mask = Image.fromarray(np.ascontiguousarray(raw_img.array[..., -1]), 'L')
        img = raw_img.convert(image_mode)
    try:
        with open_file(metafile) as f:
            meta = json.load(f)
        bbox_matrix = np.asmatrix(meta['bbox_matrix']) if 'bbox_matrix' in meta else None
        native_resolution = tuple(meta['native_resolution']) if 'native_resolution' in meta else None
    except:
        bbox_matrix = None
        native_resolution = None
    return RegionOfInterest(name=basename, template=img, mask=mask, bbox_matrix=bbox_matrix, native_resolution=native_resolution)
