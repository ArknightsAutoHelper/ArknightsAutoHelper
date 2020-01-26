import logging

import cv2 as cv
import numpy as np
from PIL import Image

from richlog import get_logger
from . import imgops, util
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
    if use_anchor[2] < 0.9:
        return None
    logger.debug('use anchor: %s', repr(use_anchor))
    bias = np.asarray(use_anchor[1], dtype=np.int32) - map_vectors.stage_maps[partition][use_anchor[0]]
    logger.debug('bias: %s', bias)
    result = {name: (pos + bias) * scale for name, pos in map_vectors.stage_maps[partition].items()}
    return result


def recognize_daily_menu(img, partition):
    logger.debug('recognizing daily menu in partition %s', partition)
    names = [x[:-4] for x in resources.get_entries('maps/' + partition)[1]]
    scale = img.height / 720
    img = imgops.scale_to_height(img.convert('RGB'), 720)
    imgmat = np.asarray(img)
    match_results = [(name, *match_template(imgmat, resources.load_image_cached('maps/%s/%s.png' % (partition, name), 'RGB')))
                     for name in names]
    result = {name: (np.asarray(pos) * scale, conf) for name, pos, conf in match_results if conf > 0.85}
    return result


def get_daily_menu_entry(viewport, daily_type):
    vw, vh = util.get_vwvh(viewport)
    if daily_type == 'material':
        return (23.472*vh, 86.667*vh, 41.111*vh, 96.944*vh)
    elif daily_type == 'soc':
        return (44.583*vh, 86.667*vh, 62.083*vh, 96.944*vh)
    else:
        raise KeyError(daily_type)


if __name__ == '__main__':
    import sys
    import pprint
    pprint.pprint(globals()[sys.argv[1]](Image.open(sys.argv[2]), sys.argv[3]))
