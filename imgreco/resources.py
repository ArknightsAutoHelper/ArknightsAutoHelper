import os
import pickle
from functools import lru_cache
import importlib.util

import numpy as np
from util import cvimage as Image

import config

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

if config.use_archived_resources:
    import zipfile
    root = 'resources/imgreco'
    archive = zipfile.ZipFile(open(config.resource_archive, 'rb'), 'r')

    filelist = archive.namelist()

    def get_path(names):
        return '/'.join([root, *names])

    def _open_file(path):
        return archive.open(path)

    def _get_index(names):
        archive_path = get_path(names)
        return ResourceArchiveIndex(archive, archive_path)

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
    root = os.path.join(config.resource_root, 'imgreco')

    def get_path(names):
        return os.path.join(root, *names)

    def _get_index(names):
        path = get_path(names)
        return FileSystemIndex(os.path.join(root, path))

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


def load_image(name, mode=None):
    im = Image.open(open_file(name))
    if mode is not None and im.mode != mode:
        im = im.convert(mode)
    return im


@lru_cache(maxsize=None)
def load_image_cached(name, mode=None):
    return load_image(name, mode)


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
