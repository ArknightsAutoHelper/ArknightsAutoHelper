import os
import pickle
from PIL import Image
import numpy as np

root = os.path.realpath(os.path.dirname(__file__))

def get_path(*names):
    return os.path.join(root, *names)

def load_image(name):
    names = name.split('/')
    path = get_path(*names)
    im = Image.open(path)
    return im

def load_image_as_ndarray(name):
    return np.asarray(load_image(name))

def load_pickle(name):
    names = name.split('/')
    path = get_path(*names)
    with open(path, 'rb') as f:
        result = pickle.load(f)
    return result
