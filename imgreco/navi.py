import numpy as np
import cv2
from PIL import Image

from . import resources
from . import imgops


def match_template(img, resource):
    scale = img.height / 720
    img = imgops.scale_to_height(img.convert('RGB'), 720)
    imgmat = np.asarray(img)
    match_result = imgops.match_template(imgmat, resources.load_image_cached(resource, 'RGB'))

    pos = np.asarray(match_result[0], dtype=np.int32) * scale
    pr = match_result[1]

    return pos, pr
