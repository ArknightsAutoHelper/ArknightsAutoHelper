import numpy as np
from PIL import Image

from . import imgops


# logger = richlog.get_logger('log/richlog.html', True)

def compare_ccoeff(img, mat):
    height, width = mat.shape
    mat2 = np.asarray(img.resize((width, height), Image.BILINEAR))
    return imgops.compare_ccoeff(mat, mat2)

def compare_ssim(img, mat):
    from skimage.metrics import structural_similarity as skcompare_ssim
    height, width = mat.shape
    mat2 = np.asarray(img.resize((width, height), Image.BILINEAR))
    return skcompare_ssim(mat, mat2, win_size=3)

def compare_mse(img, mat):
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
                    chars.append(imgops.crop_blackedge(Image.fromarray(mat[:, left:x+1])))
        if not inchar and (col > split_threshold).any():
            left = x
            inchar = True
            spaces = 0

    if inchar and left != x:
        chars.append(imgops.crop_blackedge(Image.fromarray(mat[:, left:x+1])))

    # for cimg in chars:
    #     logger.logimage(cimg)

    return chars


class MiniRecognizer:
    def __init__(self, model, compare=compare_mse):
        self.model = model['data']
        self.fontname = model['fontfile']
        self.chars = tuple(x[0] for x in self.model)
        self.compare = compare

    def recognize_char(self, image, subset=None):
        w1, h1 = image.size
        # comparsions = [(c, imgcompare(image, mat)) for c, mat in self.model]
        comparsions = []
        aggreate_score = lambda img_comparsion, ratio_comparsion: img_comparsion - ratio_comparsion * 0.4
        for c, mats in self.model:
            if subset is not None and c not in subset:
                continue
            if not isinstance(mats, list):
                mats = [mats]
            scores = []
            for mat in mats:
                h2, w2 = mat.shape
                ratcomp = abs((w1 * h2) / (w2 * h1) - 1)
                # print(c, ratcomp)
                # if ratcomp < 0.8:
                score = self.compare(image, mat)
                scores.append((score, ratcomp))
            comparsions.append((c, *max(scores, key=lambda x: aggreate_score(*x))))
        if len(comparsions):
            bestmatch = max(comparsions, key=lambda x: aggreate_score(*x[1:]))
            return bestmatch[0], aggreate_score(*bestmatch[1:])
        else:
            return ''

    def recognize(self, image):
        """requires white chars on black background, grayscale image"""
        return self.recognize2(image)[0]

    def recognize2(self, image, split_threshold=127, subset=None):
        """requires white chars on black background, grayscale image"""
        if image.mode != 'L':
            image = image.convert('L')
        charimgs = split_chars(image, split_threshold)
        if charimgs:
            matches = [self.recognize_char(charimg, subset) for charimg in charimgs]
            return ''.join(x[0] for x in matches), min(x[1] for x in matches)
        else:
            return '', 1

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
