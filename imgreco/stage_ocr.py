from functools import lru_cache

import cv2
import numpy as np

from util.richlog import get_logger
from . import common
from . import resources

idx2id = ['-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
          'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
logger = get_logger(__name__)


@lru_cache(maxsize=2)
def _load_onnx_model(model_name='chars'):
    with resources.open_file(f'stage_ocr/{model_name}.onnx') as f:
        data = f.read()
        net = cv2.dnn.readNetFromONNX(data)
        return net


def predict_cv(img, noise_size=None, model_name='chars'):
    char_imgs = crop_char_img(img, noise_size)
    if not char_imgs:
        return ''
    return predict_char_images(char_imgs, model_name)


def predict_char_images(char_imgs, model_name='chars'):
    net = _load_onnx_model(model_name)
    roi_list = [np.expand_dims(resize_char(x), 2) for x in char_imgs]
    blob = cv2.dnn.blobFromImages(roi_list)
    net.setInput(blob)
    scores = net.forward()
    predicts = scores.argmax(1)
    # softmax = [common.softmax(score) for score in scores]
    # probs = [softmax[i][predicts[i]] for i in range(len(predicts))]
    # print(probs)
    return ''.join([idx2id[p] for p in predicts])


def resize_char(img):
    h, w = img.shape[:2]
    scale = 16 / max(h, w)
    h = int(h * scale)
    w = int(w * scale)
    img2 = np.zeros((16, 16)).astype(np.uint8)
    img = cv2.resize(img, (w, h))
    img2[0:h, 0:w] = img
    # cv2.imshow('test', img2)
    # cv2.waitKey()
    return img2


def crop_char_img(img, noise_size=None):
    h, w = img.shape[:2]
    has_white = False
    last_x = None
    res = []
    if noise_size is None:
        noise_size = 3 if h > 40 else 2
    for x in range(0, w):
        for y in range(0, h - noise_size + 1):
            has_white = False
            flag = False
            if img[y][x] > 127:
                flag = True
                for i in range(noise_size):
                    if img[y+i][x] < 127:
                        flag = False
            if flag:
                has_white = True
                if not last_x:
                    last_x = x
                break
        if not has_white and last_x:
            if x - last_x >= noise_size // 2:
                min_y = None
                max_y = None
                for y1 in range(0, h):
                    has_white = False
                    for x1 in range(last_x, x):
                        if img[y1][x1] > 127:
                            has_white = True
                            if min_y is None:
                                min_y = y1
                            break
                    if not has_white and min_y is not None and max_y is None:
                        max_y = y1
                        break
                # cv2.imshow('test', img[min_y:max_y, last_x:x])
                # cv2.waitKey()
                res.append(img[min_y:max_y, last_x:x])
            last_x = None
    return res


def thresholding(image):
    img = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    if img[0, 0] > 127:
        img = ~img
    return img


def pil_to_cv_gray_img(pil_img):
    arr = np.asarray(pil_img, dtype=np.uint8)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)


def cut_tag(screen, w, pt):
    img_h, img_w = screen.shape[:2]
    tag_w, tag_h = 130, 36
    tag = thresholding(screen[pt[1] + 2:pt[1] + tag_h + 3, pt[0] + w + 3:pt[0] + tag_w + w])
    # 130 像素不一定能将 tag 截全，所以再检查一次看是否需要拓宽 tag 长度
    for i in range(3):
        for j in range(tag_h):
            if tag[j][tag_w - 4 - i] > 127:
                tag_w = 150
                if pt[0] + w + tag_w >= img_w:
                    return None
                tag = thresholding(screen[pt[1] - 1:pt[1] + tag_h, pt[0] + w + 3:pt[0] + tag_w + w])
                break
    return tag


def remove_holes(img):
    # 去除小连通域
    h, w = img.shape[:2]
    noise_size = 15 if h > 25 else 8
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for i in range(len(contours)):
        # 计算区块面积
        area = cv2.contourArea(contours[i])
        if area < noise_size:
            # 将面积较小的点涂成黑色，以去除噪点
            cv2.drawContours(img, [contours[i]], 0, 0, -1)


def recognize_stage_tags(pil_screen, template, ccoeff_threshold=0.75):
    screen = pil_to_cv_gray_img(pil_screen)
    img_h, img_w = screen.shape[:2]
    ratio = 1080 / img_h
    if ratio != 1:
        ratio = 1080 / img_h
        screen = cv2.resize(screen, (int(img_w * ratio), 1080))
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= ccoeff_threshold)
    h, w = template.shape[:2]
    img_h, img_w = screen.shape[:2]
    tag_set = set()
    tag_set2 = set()
    res = []
    dbg_screen = None
    for pt in zip(*loc[::-1]):
        pos_key = (pt[0] // 100, pt[1] // 100)
        pos_key2 = (int(pt[0] / 100 + 0.5), int(pt[1] / 100 + 0.5))
        if pos_key in tag_set or pos_key2 in tag_set2:
            continue
        tag_set.add(pos_key)
        tag_set2.add(pos_key2)
        tag_w = 130
        # 检查边缘像素是否超出截图的范围
        if pt[0] + w + tag_w < img_w:
            tag = cut_tag(screen, w, pt)
            if tag is None:
                continue
            remove_holes(tag)
            tag_str = do_tag_ocr(tag, 3)
            if len(tag_str) < 3:
                if dbg_screen is None:
                    dbg_screen = screen.copy()
                cv2.rectangle(dbg_screen, pt, (pt[0] + w + tag_w, pt[1] + h), 0, 3)
                continue
            pos = (int((pt[0] + (tag_w / 2)) / ratio), int((pt[1] + 20) / ratio))
            # logger.logtext('pos: %s' % str(pos))
            # res.append({'tag_img': tag, 'pos': (pt[0] + (tag_w / 2), pt[1] + 20), 'tag_str': tag_str})
            res.append({'pos': pos, 'tag_str': tag_str})
    if dbg_screen is not None:
        logger.logimage(common.convert_to_pil(dbg_screen))
    return res


def do_tag_ocr(img, noise_size=None, model_name='chars'):
    logger.logimage(common.convert_to_pil(img))
    res = do_tag_ocr_dnn(img, noise_size, model_name)
    logger.logtext('res: %s' % res)
    return res


def do_tag_ocr_dnn(img, noise_size=None, model_name='chars'):
    return predict_cv(img, noise_size, model_name)


def do_img_ocr(pil_img):
    img = pil_to_cv_gray_img(pil_img)
    # cv2.imshow('test', img)
    # cv2.waitKey()
    img_avg = np.average(img)
    thresh_mode = cv2.THRESH_BINARY_INV if img_avg > 127 else cv2.THRESH_BINARY
    img = cv2.threshold(img, 100, 255, thresh_mode)[1]
    remove_holes(img)
    return do_tag_ocr(img)


stage_icon1 = pil_to_cv_gray_img(resources.load_image('stage_ocr/stage_icon1.png'))
stage_icon2 = pil_to_cv_gray_img(resources.load_image('stage_ocr/stage_icon2.png'))
stage_icon_ex1 = pil_to_cv_gray_img(resources.load_image('stage_ocr/stage_icon_ex1.png'))
normal_icons = [stage_icon1, stage_icon2]
extra_icons = [stage_icon_ex1]


def recognize_all_screen_stage_tags(pil_screen, allow_extra_icons=False):
    tags_map = {}
    if allow_extra_icons:
        for icon in extra_icons:
            for tag in recognize_stage_tags(pil_screen, icon, 0.75):
                tags_map[tag['tag_str']] = tag['pos']
    for icon in normal_icons:
        for tag in recognize_stage_tags(pil_screen, icon):
            tags_map[tag['tag_str']] = tag['pos']
    return tags_map
