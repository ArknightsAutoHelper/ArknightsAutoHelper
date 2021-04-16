from functools import lru_cache
import cv2
import numpy as np
from . import resources
import zipfile
from . import common
from util.richlog import get_logger
import config


idx2id = ['-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
          'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
prefer_svm = config.get('ocr/stage_prefer_svm', True)
logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _load_svm():
    with resources.open_file('resources/imgreco/stage_ocr/svm_data.zip') as f:
        zf = zipfile.ZipFile(f, 'r')
        ydoc = zf.read('svm_data.dat').decode('utf-8')
        fs = cv2.FileStorage(ydoc, cv2.FileStorage_READ | cv2.FileStorage_MEMORY)
        svm = cv2.ml.SVM_create()
        svm.read(fs.getFirstTopLevelNode())
        assert svm.isTrained()
        return svm


@lru_cache(maxsize=1)
def _load_onnx_model():
    with resources.open_file('resources/imgreco/stage_ocr/chars.onnx') as f:
        data = f.read()
        net = cv2.dnn.readNetFromONNX(data)
        return net


def predict_cv(img):
    net = _load_onnx_model()
    char_imgs = crop_char_img(img)
    if not char_imgs:
        return ''
    roi_list = [np.expand_dims(resize_char(x), 2) for x in char_imgs]
    blob = cv2.dnn.blobFromImages(roi_list)
    net.setInput(blob)
    scores = net.forward()
    predicts = scores.argmax(1)
    # softmax = [common.softmax(score) for score in scores]
    # probs = [softmax[i][predicts[i]] for i in range(len(predicts))]
    # print(probs)
    return ''.join([idx2id[p] for p in predicts])


def get_img_feature(img):
    return resize_char(img).reshape((256, 1))


def resize_char(img):
    h, w = img.shape[:2]
    scale = 16 / max(h, w)
    h = int(h * scale)
    w = int(w * scale)
    img2 = np.zeros((16, 16)).astype(np.uint8)
    img = cv2.resize(img, (w, h))
    img2[0:h, 0:w] = ~img
    return img2


def predict(gray_img):
    svm = _load_svm()
    res = svm.predict(np.float32([get_img_feature(gray_img)]))
    return chr(res[1][0][0])


def crop_char_img(img):
    h, w = img.shape[:2]
    has_black = False
    last_x = None
    res = []
    for x in range(0, w):
        for y in range(0, h):
            has_black = False
            if img[y][x] < 127:
                has_black = True
                if not last_x:
                    last_x = x
                break
        if not has_black and last_x:
            if x - last_x >= 3:
                min_y = None
                max_y = None
                for y1 in range(0, h):
                    has_black = False
                    for x1 in range(last_x, x):
                        if img[y1][x1] < 127:
                            has_black = True
                            if min_y is None:
                                min_y = y1
                            break
                    if not has_black and min_y is not None and max_y is None:
                        max_y = y1
                        break
                res.append(img[min_y:max_y, last_x:x])
            last_x = None
    return res


def thresholding(image):
    img = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    if img[0, 0] < 127:
        img = ~img
    return img


def pil_to_cv_gray_img(pil_img):
    arr = np.asarray(pil_img, dtype=np.uint8)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)


def invert_cv_gray_img_color(img):
    return ~img


def cut_tag(screen, w, pt):
    img_h, img_w = screen.shape[:2]
    tag_w = 130
    tag = thresholding(screen[pt[1] - 1:pt[1] + 40, pt[0] + w + 3:pt[0] + tag_w + w])
    # 130 像素不一定能将 tag 截全，所以再检查一次看是否需要拓宽 tag 长度
    for i in range(3):
        for j in range(40):
            if tag[j][tag_w - 4 - i] < 127:
                tag_w = 160
                if pt[0] + w + tag_w >= img_w:
                    return None
                tag = thresholding(screen[pt[1] - 1:pt[1] + 40, pt[0] + w + 3:pt[0] + tag_w + w])
                break
    return tag


def remove_holes(img):
    # 去除小连通域
    # findContours 只能处理黑底白字的图像, 所以需要进行一下翻转
    contours, hierarchy = cv2.findContours(~img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for i in range(len(contours)):
        # 计算区块面积
        area = cv2.contourArea(contours[i])
        if area < 8:
            # 将面积较小的点涂成白色，以去除噪点
            cv2.drawContours(img, [contours[i]], 0, 255, -1)


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
            tag_str = do_tag_ocr(tag)
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


def do_tag_ocr(img):
    logger.logimage(common.convert_to_pil(img))
    res = do_tag_ocr_svm(img) if prefer_svm else do_tag_ocr_dnn(img)
    logger.logtext('%s, res: %s' % ('svm' if prefer_svm else 'dnn', res))
    return res


def do_tag_ocr_svm(img):
    char_imgs = crop_char_img(img)
    s = ''
    for char_img in char_imgs:
        c = predict(char_img)
        s += c
    return s


def do_tag_ocr_dnn(img):
    return predict_cv(img)


def do_img_ocr(pil_img):
    img = pil_to_cv_gray_img(pil_img)
    # cv2.imshow('test', img)
    # cv2.waitKey()
    img = thresholding(img)
    remove_holes(img)
    return do_tag_ocr(img)


stage_icon1 = pil_to_cv_gray_img(resources.load_image('stage_ocr/stage_icon1.png'))
stage_icon2 = pil_to_cv_gray_img(resources.load_image('stage_ocr/stage_icon2.png'))


def recognize_all_screen_stage_tags(pil_screen):
    tags_map = {}
    for tag in recognize_stage_tags(pil_screen, stage_icon1):
        tags_map[tag['tag_str']] = tag['pos']
    for tag in recognize_stage_tags(pil_screen, stage_icon2):
        tags_map[tag['tag_str']] = tag['pos']
    return tags_map
