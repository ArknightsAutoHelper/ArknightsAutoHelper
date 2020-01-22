"""
for test purpose

usage: python3 -m Arknights.ocr [language=zh-hans-cn] filename
"""

import sys
import os

from pprint import pprint

import Arknights.ocr as ocr
from PIL import Image

if __name__ == '__main__':
    if 'OCR_ENGINE' in os.environ:
        ocr.engine = getattr(ocr, os.environ['OCR_ENGINE'])
    if 2 <= len(sys.argv) <= 3:
        lang = 'zh-hans-cn' if len(sys.argv) == 2 else sys.argv[1]
        filename = sys.argv[-1]
        result = ocr.engine.recognize(Image.open(filename), lang)
        pprint(result, width=128)
    else:
        print('usage: %s [language=zh-hans-cn] filename' % sys.argv[0])
