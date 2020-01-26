import logging

import cv2 as cv
import numpy as np
from PIL import Image

from richlog import get_logger
from . import imgops
from . import resources

from .resources import map_vectors

logger = logging.getLogger('imgreco.map')

def match_template(img, template):
    templatemat = np.asarray(template)
    mtresult = cv.matchTemplate(np.asarray(img), templatemat, cv.TM_CCOEFF_NORMED)
    maxidx = np.unravel_index(np.argmax(mtresult), mtresult.shape)
    y, x = maxidx
    return (x + templatemat.shape[1] / 2, y + templatemat.shape[0] / 2), mtresult[maxidx]


def recognize_map(img, partition):
    logger.debug('recognizing in partition %s', partition)
    anchors = map_vectors.map_anchors[partition]
    scale = img.height / 720
    img = imgops.scale_to_height(img.convert('RGB'), 720)
    imgmat = np.asarray(img)
    match_results = [(anchor, *match_template(imgmat, resources.load_image_cached('maps/%s/%s.png' % (partition, anchor), 'RGB')))
                     for anchor in anchors]
    logger.debug('anchor match results: %s', repr(match_results))
    use_anchor = max(match_results, key=lambda x: x[2])
    logger.debug('use anchor: %s', repr(use_anchor))
    bias = np.asarray(use_anchor[1], dtype=np.int32) - map_vectors.stage_maps[partition][use_anchor[0]]
    logger.debug('bias: %s', bias)
    result = {name: (pos + bias) * scale for name, pos in map_vectors.stage_maps[partition].items()}
    return result

if __name__ == '__main__':
    import sys
    import pprint
    pprint.pprint(recognize_map(Image.open(sys.argv[1]), sys.argv[2]))
