"""for test purpose"""

import sys
from pprint import pprint

import ocr
from PIL import Image

if 2 <= len(sys.argv) <= 3:
    lang = 'zh-hans-cn' if len(sys.argv) == 2 else sys.argv[1]
    filename = sys.argv[-1]
    result = ocr.engine.recognize(Image.open(filename), lang)
    pprint(result, width=128)
else:
    print('usage: %s [language=zh-hans-cn] filename' % sys.argv[0])
