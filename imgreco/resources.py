import os
import pickle
from functools import lru_cache
import importlib.util

import numpy as np
from PIL import Image

import config

if config.use_archived_resources:
    import zipfile
    root = 'resources/imgreco'
    archive = zipfile.ZipFile(open(config.resource_archive, 'rb'), 'r')
    filelist = archive.namelist()

    def get_path(names):
        return '/'.join([root, *names])

    def open_file(path):
        return archive.open(path)

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
    root = os.path.join(config.root, 'resources', 'imgreco')

    def get_path(names):
        return os.path.join(root, *names)

    def open_file(path):
        return open(path, 'rb')

    def get_entries(base):
        findroot = get_path(base.split('/'))
        _, dirs, files = next(os.walk(findroot))
        return (dirs, files)


def load_image(name, mode=None):
    names = name.split('/')
    path = get_path(names)
    im = Image.open(open_file(path))
    if mode is not None and im.mode != mode:
        im = im.convert(mode)
    return im


@lru_cache(maxsize=None)
def load_image_cached(name, mode=None):
    return load_image(name, mode)


def load_image_as_ndarray(name):
    return np.asarray(load_image(name))


def load_pickle(name):
    names = name.split('/')
    path = get_path(names)
    with open_file(path) as f:
        result = pickle.load(f)
    return result


def load_minireco_model(name, filter_chars=None):
    model = load_pickle(name)
    if filter_chars is not None:
        model['data'] = [x for x in model['data'] if x[0] in filter_chars]
        model['chars'] = [x[0] for x in model['data']]
    return model


map_vectors = __import__('resources.imgreco.map_vectors')
