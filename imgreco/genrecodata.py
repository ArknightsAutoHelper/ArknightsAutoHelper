import pickle
from PIL import Image, ImageFont
import numpy as np
from . import imgops
import os

def charimg(font, char, size, threshold=32):
    mask = font.getmask(char, 'L')
    maskmat = np.asarray(mask).reshape(mask.size[::-1])
    thimg = imgops.image_threshold_mat2img(maskmat, threshold)
    left, top, right, bottom = thimg.getbbox()

    height = bottom-top
    width = right-left
    maskim = Image.new('L', mask.size)
    maskim.putdata(mask)
    scale = size / height
    scaledwidth = int(width * scale)
    return maskim.resize((scaledwidth, size), Image.BICUBIC, (left, top, right, bottom))

def charmat(font, char, size, threshold=32):
    return np.asarray(charimg(font, char, size, threshold))

def main(fontfile, size, chars, threshold, datafile):
    fnt = ImageFont.truetype(fontfile, size*8)
    data = [(char, charmat(fnt, char, size, threshold)) for char in chars]
    obj = {'fontfile': os.path.basename(fontfile), 'size': size, 'chars': chars, 'data': data}
    with open(datafile, 'wb') as f:
        pickle.dump(obj, f)

if __name__ == '__main__':
    import sys
    if len(sys.argv) not in (5, 6):
        print("usage: %s fontfile size chars [crop_threshold] datafile" % sys.argv[0])
        sys.exit(1)
    else:
        fontfile, sizes, chars, *cdr = sys.argv[1:]
        if len(cdr) == 2:
            threshold = int(cdr[0])
        else:
            threshold = 32
        datafile = cdr[-1]
        size = int(sizes)
        main(fontfile, size, chars, threshold, datafile)
