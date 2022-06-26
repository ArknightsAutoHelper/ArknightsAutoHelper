from .common import *
import cv2
import numpy as np
from functools import lru_cache
import logging
from ppocronnx.predict_system import TextSystem
from . import OcrHint

is_online = False
# OCR 过程是否需要网络


info = "ppocr"

ocr = TextSystem()


# 模块说明，用于在 log 中显示
def check_supported():
    """返回模块是否可用"""
    return True


class PaddleOcr(OcrEngine):
    def recognize(self, image, ppi=70, hints=None, **kwargs):
        if image.mode != 'BGR':
            image = image.convert('BGR')
        cv_img = image.array
        single_line_flag = image.height < 35 or image.width / 3 > image.height
        if hints is not None and OcrHint.SINGLE_LINE in hints:
            single_line_flag = True
        if single_line_flag:
            res = ocr.ocr_single_line(cv_img)
            logging.debug(f'PaddleOcr.recognize: {res}')
            if res and res[1] > 0.7:
                return OcrResult([OcrLine([OcrWord(Rect(0, 0), w) for w in res[0].strip()])])
            else:
                return OcrResult([])
        else:
            result = ocr.detect_and_ocr(cv_img)
            logging.debug(f'PaddleOcr.recognize: {result}')
            line = [OcrLine([OcrWord(Rect(0, 0), w) for w in box.ocr_text]) for box in result]
            return OcrResult(line)


def ocr_for_single_line(img, cand_alphabet: str = None):
    if cand_alphabet:
        ocr.set_char_whitelist(cand_alphabet)
    res = ocr.ocr_single_line(img)
    if res:
        res = res[0]
    if cand_alphabet:
        ocr.set_char_whitelist(None)
    return res


def do_ocr(img, cand_alphabet: str = None):
    if cand_alphabet:
        ocr.set_char_whitelist(cand_alphabet)
    res = ''
    ocr_result = ocr.detect_and_ocr(img)
    for line in ocr_result:
        for ch in line:
            res += ch
    res = res.strip()
    if cand_alphabet:
        ocr.set_char_whitelist(None)
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


def ocr_and_correct(img, s_list, cand_alphabet: str = None, min_score=0.5, log_level=None):
    ocr_str = ocr_for_single_line(img, cand_alphabet)
    res = search_in_list(s_list, ocr_str, min_score)
    if log_level:
        logging.log(log_level, f'ocr_str, res: {ocr_str, res}')
    return res[0] if res else None


Engine = PaddleOcr
