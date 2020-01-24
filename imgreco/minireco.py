import numpy as np
from PIL import Image

from . import imgops


# from skimage.measure import compare_ssim
# from skimage.measure import compare_mse


# logger = richlog.get_logger('log/richlog.html', True)

def imgcompare(img, mat):
    height, width = mat.shape
    mat2 = np.asarray(img.resize((width, height), Image.BILINEAR))
    return compare_ssim(mat, mat2)


def imgcompare2(img, mat):
    height, width = mat.shape
    mat2 = np.asarray(img.resize((width, height), Image.BILINEAR))
    return -imgops.compare_mse(mat, mat2)


def split_chars(textimg, split_threshold=127):
    """requires white chars on black background, grayscale image"""
    img = imgops.crop_blackedge(textimg, split_threshold)
    if img is None:
        return []
    # logger.logimage(img)
    mat = np.asarray(img, dtype=np.uint8)
    left = 0
    inchar = True
    chars = []
    height, width, *_ = mat.shape

    spacing_threshold = 1

    spaces = 0

    for x in range(left, width):
        col = mat[:, x]
        if inchar and (col < split_threshold).all():
            spaces += 1
            if spaces >= spacing_threshold:
                inchar = False
                if left != x:
                    chars.append(imgops.crop_blackedge(Image.fromarray(mat[:, left:x])))
        if not inchar and (col > split_threshold).any():
            left = x
            inchar = True
            spaces = 0

    if inchar and left != x:
        chars.append(imgops.crop_blackedge(Image.fromarray(mat[:, left:x])))

    # for cimg in chars:
    #     logger.logimage(cimg)

    return chars


class MiniRecognizer:
    def __init__(self, model):
        self.model = model['data']
        self.fontname = model['fontfile']
        self.chars = tuple(x[0] for x in self.model)

    def recognize_char(self, image):
        w1, h1 = image.size
        # comparsions = [(c, imgcompare(image, mat)) for c, mat in self.model]
        comparsions = []
        for c, mat in self.model:
            h2, w2 = mat.shape
            scale = h2 / h1
            w1s = w1 * scale
            ratcomp = abs(w1s - w2) / w1
            # print(c, ratcomp)
            # if ratcomp < 0.8:
            score = imgcompare2(image, mat)
            comparsions.append((c, score, ratcomp))
        if len(comparsions):
            return max(comparsions, key=lambda x: x[1] - x[2] * 0.4)[0]
        else:
            return ''

    def recognize(self, image):
        """requires white chars on black background, grayscale image"""
        if image.mode != 'L':
            image = image.convert('L')
        charimgs = split_chars(image)
        return ''.join(self.recognize_char(charimg) for charimg in charimgs)


def check_charseq(string, seq):
    lastindex = -1
    for ch in seq:
        try:
            index = string.index(ch)
        except ValueError:
            return False
        if index < lastindex:
            return False
        lastindex = index
    return True
