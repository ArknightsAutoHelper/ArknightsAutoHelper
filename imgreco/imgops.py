from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Union

from dataclasses import dataclass

import cv2 as cv
import numpy as np
from util import cvimage as Image


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


def cropbox_blackedge2(numimg, value_threshold=127, x_threshold=None):
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
    return (left, top, right, bottom)

def crop_blackedge2(numimg, value_threshold=127, x_threshold=None):
    box = cropbox_blackedge2(numimg, value_threshold, x_threshold)
    if box is None:
        return None
    return numimg.crop(box)


def scalecrop(img, left, top, right, bottom):
    w, h = img.size
    rect = tuple(map(int, (left * w, top * h, right * w, bottom * h)))
    return img.crop(rect)


def compare_mse(mat1, mat2, mask=None):
    """max 65025 (255**2) for 8bpc image"""
    mat1 = np.asarray(mat1)
    mat2 = np.asarray(mat2)
    assert (mat1.shape == mat2.shape)
    diff = mat1.astype(np.float32) - mat2.astype(np.float32)
    if mask is not None:
        mask = np.asarray(mask)
        diff[mask == 0] = 0
    mse = np.mean(diff * diff)
    return mse


def scale_to_height(img, height, algo=Image.BILINEAR):
    scale = height / img.height
    return img.resize((int(img.width * scale), height), algo)


def compare_ccoeff(img1, img2, mask=None):
    img1 = np.asarray(img1)
    img2 = np.asarray(img2)
    if mask is not None:
        mask = np.asarray(mask)
    assert (img1.shape == img2.shape)
    result = cv.matchTemplate(img1, img2, cv.TM_CCOEFF_NORMED, mask=mask)[0, 0]
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


def match_template(img, template, method=cv.TM_CCOEFF_NORMED, template_mask=None) -> tuple[tuple[int, int], float]:
    templatemat = np.asarray(template)
    mtresult = cv.matchTemplate(np.asarray(img), templatemat, method, mask=template_mask)
    minval, maxval, minloc, maxloc = cv.minMaxLoc(mtresult)
    if method == cv.TM_SQDIFF_NORMED or method == cv.TM_SQDIFF:
        useloc = minloc
        useval = minval
    else:
        useloc = maxloc
        useval = maxval
    x, y = useloc
    return (x + templatemat.shape[1] / 2, y + templatemat.shape[0] / 2), useval


@dataclass
class FeatureMatchingResult:
    template_keypooint_count: int
    matched_keypoint_count: int
    template_corners: Union[list[tuple[int, int]], np.ndarray, None] = None
    M: np.ndarray = None


def match_feature_orb(templ, haystack, *, min_match=10, templ_mask=None, haystack_mask=None, limited_transform=False) -> FeatureMatchingResult:
    templ = np.asarray(templ.convert('L'))
    haystack = np.asarray(haystack.convert('L'))

    detector = cv.ORB_create(10000)
    descriptor = cv.xfeatures2d.BEBLID_create(0.75)
    # descriptor = detector
    kp1 = detector.detect(templ, templ_mask)
    kp2 = detector.detect(haystack, haystack_mask)
    kp1, des1 = descriptor.compute(templ, kp1)
    kp2, des2 = descriptor.compute(haystack, kp2)

    index_params = dict(algorithm=6,
                        table_number=6,
                        key_size=12,
                        multi_probe_level=1)
    search_params = {}
    matcher = cv.FlannBasedMatcher(index_params, search_params)
    # matcher = cv.BFMatcher_create(cv.NORM_HAMMING)
    matches = matcher.knnMatch(des1, des2, k=2)
    good = []
    for group in matches:
        if len(group) >= 2 and group[0].distance < 0.75 * group[1].distance:
            good.append(group[0])

    result = FeatureMatchingResult(len(kp1), len(good))

    if len(good) >= min_match:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

        if limited_transform:
            M, _ = cv.estimateAffinePartial2D(src_pts, dst_pts)
        else:
            M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, 4.0)

        h, w = templ.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        if limited_transform:
            dst = cv.transform(pts, M)
        else:
            dst = cv.perspectiveTransform(pts, M)
        result.M = M
        result.template_corners = dst.reshape(-1, 2)
        # img2 = cv.polylines(haystack, [np.int32(dst)], True, 0, 2, cv.LINE_AA)
    return result


def match_feature(templ, haystack, *, min_match=10, templ_mask=None, haystack_mask=None, limited_transform=False) -> FeatureMatchingResult:
    templ = np.asarray(templ.convert('L'))
    haystack = np.asarray(haystack.convert('L'))

    detector = cv.SIFT_create()
    kp1, des1 = detector.detectAndCompute(templ, templ_mask)
    kp2, des2 = detector.detectAndCompute(haystack, haystack_mask)

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

    result = FeatureMatchingResult(len(kp1), len(good))

    if len(good) >= min_match:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

        if limited_transform:
            M, _ = cv.estimateAffinePartial2D(src_pts, dst_pts)
        else:
            M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, 4.0)

        h, w = templ.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        if limited_transform:
            dst = cv.transform(pts, M)
        else:
            dst = cv.perspectiveTransform(pts, M)
        result.M = M
        result.template_corners = dst.reshape(-1, 2)
        # img2 = cv.polylines(haystack, [np.int32(dst)], True, 0, 2, cv.LINE_AA)
    return result



def _find_homography_test(templ, haystack):
    pts = match_feature(templ, haystack).template_corners
    img2 = cv.polylines(np.asarray(haystack.convert('L')), [np.int32(pts)], True, 0, 2, cv.LINE_AA)
    img = Image.fromarray(img2, 'L')
    print(pts)
    img.show()


def compare_region_mse(img, region, template, threshold=3251, logger=None):
    if isinstance(template, str):
        from . import resources
        template = resources.load_image_cached(template, img.mode)
    img = img.crop(region)
    mat1, mat2 = uniform_size(img, template)
    mse = compare_mse(mat1, mat2)
    if logger is not None:
        logger.logimage(img)
        logger.logtext('mse=%f' % mse)
    if threshold is not None:
        return mse < threshold
    return mse

def pad(img, size, value=None):
    if value is None:
        mode = cv.BORDER_REPLICATE
    else:
        mode = cv.BORDER_CONSTANT
    mat = cv.copyMakeBorder(np.asarray(img), size, size, size, size, mode, value=value)
    return Image.fromarray(mat, img.mode)
