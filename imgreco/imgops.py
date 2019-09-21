from functools import reduce

import numpy as np
from PIL import Image

def enhance_contrast(img, lower=90, upper=255):
    lut = np.zeros(256, dtype=np.uint8)
    lut[lower:upper+1] = np.linspace(0, 255, upper-lower+1, endpoint=True, dtype=np.uint8)
    lut[upper+1:] = 255
    return Image.fromarray(lut[np.asarray(img, np.uint8)])

def image_threshold_mat2img(mat, threshold=127):
    """
    threshold filter on L channel
    :param threshold: negative value means inverted output
    """
    if threshold < 0:
        resultmat = mat < -threshold
    else:
        resultmat = mat > threshold
    lut = np.zeros(256, dtype=np.uint8)
    lut[1:] = 255
    return Image.fromarray(lut[resultmat.astype(np.uint8)], 'L').convert('1')

def image_threshold(image, threshold=127):
    """
    threshold filter on L channel
    :param threshold: negative value means inverted output
    """
    grayimg = image.convert('L')
    mat = np.asarray(grayimg)
    return image_threshold_mat2img(mat, threshold)

def crop_blackedge(numimg, value_threshold=127):
    thimg = image_threshold(numimg, value_threshold)
    return numimg.crop(thimg.getbbox())

def crop_blackedge2(numimg, value_threshold=127):
    thimg = image_threshold(numimg, value_threshold)
    
    x_threshold = int(numimg.height * 0.4)
    y_threshold = 16
    mat = np.asarray(thimg)
    right = -1
    for x in range(thimg.width-1, -1, -1):
        col = mat[:, x]
        if np.any(col):
            right = x+1
            break
    left = right
    emptycnt = 0
    for x in range(right-1, -1, -1):
        col = mat[:, x]
        if np.any(col):
            left = x
            emptycnt = 0
        else:
            emptycnt += 1
            if emptycnt >= x_threshold:
                break
    top = 0
    for y in range(thimg.height):
        row = mat[y, left:right+1]
        if np.any(row):
            top = y
            break
    bottom = top
    emptycnt = 0
    for y in range(top, thimg.height):
        row = mat[y, left:right+1]
        if np.any(row):
            bottom = y+1
            emptycnt = 0
        else:
            emptycnt += 1
            if emptycnt >= y_threshold:
                break
    
    if left == right or top == bottom:
        return None
    return numimg.crop((left, top, right, bottom))

def scalecrop(img, left, top, right, bottom):
    w, h = img.size
    rect = tuple(map(int, (left*w, top*h, right*w, bottom*h)))
    return img.crop(rect)

def compare_mse(mat1, mat2):
    assert(mat1.shape == mat2.shape)
    diff = mat1.astype(np.int32) - mat2.astype(np.int32)
    se = np.sum(diff * diff)
    mse = se / reduce(lambda a, b: a*b, mat1.shape)
    return mse

def scale_to_height(img, height, algo=Image.BILINEAR):
    scale = height / img.height
    return img.resize((int(img.width*scale), height), algo)
