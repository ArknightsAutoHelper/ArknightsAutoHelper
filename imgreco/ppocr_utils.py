from functools import lru_cache
import numpy as np
import cv2
import textdistance
import logging

from util.cvimage import Image
from util.richlog import get_logger


logger = logging.getLogger(__name__)
richlogger = get_logger(__name__)


@lru_cache(1)
def get_ppocr():
    from ppocronnx.predict_system import TextSystem
    return TextSystem(box_thresh=0.1)


def calc_box_center(box, scale=1):
    box_y = box[:, 1]
    box_x = box[:, 0]
    return int(np.average(box_x) * scale), int(np.average(box_y) * scale)


def detect_box(screen: Image, target_name: str, drop_score=0.3, box_thresh=0.1, unclip_ratio=1.6, no_scale=False):
    scale = 1 if no_scale else screen.height / 720
    if scale != 1:
        screen = screen.resize((screen.width / scale, 720))
    dbg_screen = screen.copy()
    ppocr = get_ppocr()
    boxed_results = ppocr.detect_and_ocr(screen.array, drop_score=drop_score,
                                         box_thresh=box_thresh, unclip_ratio=unclip_ratio)
    max_score = 0
    max_res = None
    for res in boxed_results:
        # print(res.ocr_text)
        cv2.drawContours(dbg_screen.array, [np.asarray(res.box, dtype=np.int32)], 0, (255, 0, 0), 2)
        richlogger.logtext(f'{res.ocr_text} {res.score} {res.box}')
        score = textdistance.sorensen(target_name, res.ocr_text)
        if score > max_score:
            max_score = score
            max_res = res
    if not max_res:
        return None, 0
    box_center = calc_box_center(max_res.box, scale)
    cv2.drawContours(dbg_screen.array, [np.asarray(max_res.box, dtype=np.int32)], 0, (0, 255, 0), 2)
    cv2.circle(dbg_screen.array, box_center, 4, (0, 0, 255), -1)
    richlogger.logimage(dbg_screen)
    richlogger.logtext(f"result {max_res}, box_center: {box_center}")
    logger.info(f"result {max_res}, box_center: {box_center}, score: {max_score:.3f}")
    return box_center, max_score
