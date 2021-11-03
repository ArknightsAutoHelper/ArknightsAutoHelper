from cnocr import CnOcr
from .common import *
import cv2
import numpy as np
from functools import lru_cache
import logging


is_online = False
# OCR 过程是否需要网络


info = "cnocr"


@lru_cache()
def get_ocr(model_name='densenet-lite-fc'):
    return CnOcr(name=f'imgreco-{model_name}', model_name=model_name)


cn_ocr = get_ocr('densenet-lite-fc')


# 模块说明，用于在 log 中显示

def check_supported():
    """返回模块是否可用"""
    return True


class MyCnOcr(OcrEngine):
    def recognize(self, image, ppi=70, hints=None, **kwargs):
        cv_img = cv2.cvtColor(np.asarray(image), cv2.COLOR_GRAY2RGB)
        result = cn_ocr.ocr(cv_img)
        line = [OcrLine([OcrWord(Rect(0, 0), w) for w in ocrline]) for ocrline in result]
        return OcrResult(line)


def ocr_for_single_line(img, cand_alphabet: str = None, ocr=cn_ocr):
    if cand_alphabet:
        ocr.set_cand_alphabet(cand_alphabet)
    res = ''.join(ocr.ocr_for_single_line(img)).strip()
    if cand_alphabet:
        ocr.set_cand_alphabet(None)
    return res


def search_in_list(s_list, x, min_score=0.5):
    import textdistance
    max_sim = -1
    res = None
    if (isinstance(s_list, set) or isinstance(s_list, map)) and x in s_list:
        return x, 1
    for s in s_list:
        if s == x:
            return x, 1
        sim = textdistance.sorensen(s, x)
        if sim > max_sim:
            max_sim = sim
            res = s
    if min_score <= max_sim:
        return res, max_sim


def ocr_and_correct(img, s_list, cand_alphabet: str = None, min_score=0.5, log_level=None, model_name='conv-lite-fc'):
    ocr = get_ocr(model_name)
    ocr_str = ocr_for_single_line(img, cand_alphabet, ocr)
    res = search_in_list(s_list, ocr_str, min_score)
    if log_level:
        logging.log(log_level, f'ocr_str, res: {ocr_str, res}')
    return res[0] if res else None


Engine = MyCnOcr
