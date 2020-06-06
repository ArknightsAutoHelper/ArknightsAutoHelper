import os
import pickle
from collections import OrderedDict
import numpy as np
from PIL import Image, ImageFont

from . import imgops


def charimg(font, char, size, threshold=32):
    mask = font.getmask(char, 'L')
    maskmat = np.asarray(mask).reshape(mask.size[::-1])
    thimg = imgops.image_threshold_mat2img(maskmat, threshold)
    left, top, right, bottom = thimg.getbbox()

    height = bottom - top
    width = right - left
    maskim = Image.new('L', mask.size)
    maskim.putdata(mask)
    scale = size / height
    scaledwidth = int(width * scale)
    return maskim.resize((scaledwidth, size), Image.BICUBIC, (left, top, right, bottom))


def charmat(font, char, size, threshold=32):
    return np.asarray(charimg(font, char, size, threshold))


def main(fontfile, sizes, chars, threshold, datafile):
    chars = list(OrderedDict.fromkeys(chars))
    datamap = {char: [] for char in chars}
    for size in sizes:
        fnt = ImageFont.truetype(fontfile, size)
        for char in chars:
            datamap[char].append(charmat(fnt, char, size, threshold))
    obj = {'fontfile': os.path.basename(fontfile), 'sizes': sizes, 'chars': chars, 'data': list(datamap.items())}
    with open(datafile, 'wb') as f:
        pickle.dump(obj, f)

def dump(file):
    with open(file, 'rb') as f:
        obj = pickle.load(f)
    list_or_ndarray = obj['data'][0][1]
    if isinstance(list_or_ndarray, np.ndarray):
        imgsizes = [list_or_ndarray.shape[::-1]]
    else:
        imgsizes = [x.shape[::-1] for x in list_or_ndarray]
    del obj['data']
    obj['actual_sizes'] = imgsizes
    import pprint
    pprint.pprint(obj)

if __name__ == '__main__':
    import sys

    if len(sys.argv) not in (2, 5, 6):
        print("usage: %s fontfile size chars [crop_threshold] datafile" % sys.argv[0])
        print("   or: %s datafile" % sys.argv[0])
        sys.exit(1)
    else:
        if len(sys.argv) == 2:
            dump(sys.argv[1])
        else:
            fontfile, sizes_str, chars, *cdr = sys.argv[1:]
            if len(cdr) == 2:
                threshold = int(cdr[0])
            else:
                threshold = 127
            datafile = cdr[-1]
            size = [int(size) for size in sizes_str.split(',')]
            main(fontfile, size, chars, threshold, datafile)
