"""
for test purpose

usage: python3 -m Arknights.ocr [language=zh-hans-cn] filename
"""
import importlib
import sys
import os

from pprint import pprint

ocr = importlib.import_module(__package__)
from PIL import Image

if __name__ == '__main__':
    if 'OCR_ENGINE' in os.environ:
        engine = ocr.get_engine(os.environ['OCR_ENGINE'])
    else:
        engine = ocr.get_config_engine()
    if 2 <= len(sys.argv) <= 3:
        lang = 'zh-hans-cn' if len(sys.argv) == 2 else sys.argv[1]
        filename = sys.argv[-1]
        result = engine.recognize(Image.open(filename), lang)
        pprint(result, width=128)
    else:
        print('usage: %s [language=zh-hans-cn] filename' % sys.argv[0])
