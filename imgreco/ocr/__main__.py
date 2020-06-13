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
    if 'OCR_IMPL' in os.environ:
        impl = ocr.get_impl(os.environ['OCR_IMPL'])
    else:
        impl = ocr.get_config_impl()
    print(impl.info)
    if 2 <= len(sys.argv) <= 3:
        lang = 'zh-hans-cn' if len(sys.argv) == 2 else sys.argv[1]
        filename = sys.argv[-1]
        result = impl.Engine(lang).recognize(Image.open(filename))
        pprint(result, width=128)
    else:
        print('usage: %s [language=zh-hans-cn] filename' % sys.argv[0])
