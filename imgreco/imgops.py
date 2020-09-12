from functools import reduce

import cv2 as cv
import numpy as np
from PIL import Image




def enhance_contrast(img, lower=90, upper=None):
    img = np.asarray(img, dtype=np.uint8)
    if upper is None:
        upper = np.max(img)
    lut = np.zeros(256, dtype=np.uint8)
    lut[lower:upper + 1] = np.linspace(0, 255, upper - lower + 1, endpoint=True, dtype=np.uint8)
    lut[upper + 1:] = 255
    return Image.fromarray(lut[np.asarray(img, np.uint8)])


def clear_background(img, threshold=90):
    mat = np.array(img, dtype=np.uint8)
    mask = mat < threshold
    mat[mask] = 0
    return Image.fromarray(mat)


def image_threshold_mat2img(mat, threshold=127):
    """
    threshold filter on L channel
    :param threshold: negative value means inverted output
    """
    if threshold < 0:
        resultmat = mat <= -threshold
    else:
        resultmat = mat >= threshold
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
    if numimg.width == 0 or numimg.height == 0:
        return None
    thimg = image_threshold(numimg, value_threshold)
    return numimg.crop(thimg.getbbox())


def crop_blackedge2(numimg, value_threshold=127, x_threshold=None):
    thimg = image_threshold(numimg, value_threshold)

    if x_threshold is None:
        x_threshold = int(numimg.height * 0.25)
    y_threshold = 16
    mat = np.asarray(thimg)
    right = -1
    for x in range(thimg.width - 1, -1, -1):
        col = mat[:, x]
        if np.any(col):
            right = x + 1
            break
    left = right
    emptycnt = 0
    for x in range(right - 1, -1, -1):
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
        row = mat[y, left:right + 1]
        if np.any(row):
            top = y
            break
    bottom = top
    emptycnt = 0
    for y in range(top, thimg.height):
        row = mat[y, left:right + 1]
        if np.any(row):
            bottom = y + 1
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
    rect = tuple(map(int, (left * w, top * h, right * w, bottom * h)))
    return img.crop(rect)


def compare_mse(mat1, mat2):
    """max 65025 (255**2) for 8bpc image"""
    mat1 = np.asarray(mat1)
    mat2 = np.asarray(mat2)
    assert (mat1.shape == mat2.shape)
    diff = mat1.astype(np.float32) - mat2.astype(np.float32)
    mse = np.mean(diff * diff)
    return mse


def scale_to_height(img, height, algo=Image.BILINEAR):
    scale = height / img.height
    return img.resize((int(img.width * scale), height), algo)


def compare_ccoeff(img1, img2):
    img1 = np.asarray(img1)
    img2 = np.asarray(img2)
    assert (img1.shape == img2.shape)
    result = cv.matchTemplate(img1, img2, cv.TM_CCOEFF_NORMED)[0, 0]
    return result


def uniform_size(img1, img2):
    if img1.height < img2.height:
        img2 = img2.resize(img1.size, Image.BILINEAR)
    elif img1.height > img2.height:
        img1 = img1.resize(img2.size, Image.BILINEAR)
    elif img1.width != img2.width:
        img1 = img1.resize(img2.size, Image.BILINEAR)
    return (img1, img2)


def invert_color(img):
    mat = np.asarray(img)
    lut = np.linspace(255, 0, 256, dtype=np.uint8)
    resultmat = lut[mat]
    return Image.fromarray(resultmat, img.mode)


def match_template(img, template, method=cv.TM_CCOEFF_NORMED):
    templatemat = np.asarray(template)
    mtresult = cv.matchTemplate(np.asarray(img), templatemat, method)
    if method == cv.TM_SQDIFF_NORMED or method == cv.TM_SQDIFF:
        selector = np.argmin
    else:
        selector = np.argmax
    maxidx = np.unravel_index(selector(mtresult), mtresult.shape)
    y, x = maxidx
    return (x + templatemat.shape[1] / 2, y + templatemat.shape[0] / 2), mtresult[maxidx]


def find_homography(templ, haystack, *, min_match=10):
    templ = np.asarray(templ.convert('L'))
    haystack = np.asarray(haystack.convert('L'))

    detector = cv.SIFT_create()
    kp1, des1 = detector.detectAndCompute(templ, None)
    kp2, des2 = detector.detectAndCompute(haystack, None)

    # index_params = dict(algorithm=6,
    #                     table_number=6,
    #                     key_size=12,
    #                     multi_probe_level=2)
    index_params = dict(algorithm=0, trees=5)  # algorithm=FLANN_INDEX_KDTREE
    search_params = {}
    flann = cv.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)
    good = []
    for group in matches:
        if len(group) >= 2 and group[0].distance < 0.75 * group[1].distance:
            good.append(group[0])

    if len(good) >= min_match:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

        M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, 5.0)
        matchesMask = mask.ravel().tolist()

        h, w = templ.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        dst = cv.perspectiveTransform(pts, M)

        # img2 = cv.polylines(haystack, [np.int32(dst)], True, 0, 2, cv.LINE_AA)
        return dst
    else:
        raise RuntimeError("Not enough matches are found - %d/%d" % (len(good), min_match))
        matchesMask = None


def _find_homography_test(templ, haystack):
    pts = find_homography(templ, haystack)
    img2 = cv.polylines(np.asarray(haystack.convert('L')), [np.int32(pts)], True, 0, 2, cv.LINE_AA)
    img = Image.fromarray(img2, 'L')
    print(pts)
    img.show()
