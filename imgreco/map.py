import logging

import cv2 as cv
import numpy as np
from util import cvimage as Image

from . import imgops, common
from . import resources

from resources.imgreco import map_vectors

logger = logging.getLogger('imgreco.map')


def recognize_map(img, partition):
    logger.debug('recognizing in partition %s', partition)
    anchors = map_vectors.map_anchors[partition]
    scale = img.height / 720
    img = imgops.scale_to_height(img.convert('RGB'), 720)
    imgmat = np.asarray(img)
    match_results = [(anchor, *imgops.match_template(imgmat, resources.load_image_cached('maps/%s/%s.png' % (partition, anchor), 'RGB')))
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
    match_results = [(name, *imgops.match_template(imgmat, resources.load_image_cached('maps/%s/%s.png' % (partition, name), 'RGB'), method=cv.TM_SQDIFF_NORMED))
                     for name in names]
    logger.debug('%s', match_results)
    result = {name: (np.asarray(pos) * scale, conf) for name, pos, conf in match_results if conf < 0.08}
    return result


def get_daily_menu_entry(viewport, daily_type):
    vw, vh = common.get_vwvh(viewport)
    if daily_type == 'material' or daily_type == 'soc':
        return 62.656*vw, 90.185*vh, 65.677*vw, 96.019*vh
    else:
        raise KeyError(daily_type)


if __name__ == '__main__':
    import sys
    import pprint
    pprint.pprint(globals()[sys.argv[1]](Image.open(sys.argv[2]), sys.argv[3]))
