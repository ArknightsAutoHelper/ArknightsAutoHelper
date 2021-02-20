import cv2
import numpy as np
from . import resources


# 目前可以识别的字符: ['-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T', 'W', 'X']
svm = cv2.ml.SVM_load('resources/imgreco/stage_ocr/svm_data.dat')


def get_img_feature(img):
    return cv2.resize(img, (16, 16)).reshape((256, 1))


def predict(gray_img):
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
            if x - last_x > 5:
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
    img = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
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


def recognize_stage_tags(pil_screen, template):
    screen = pil_to_cv_gray_img(pil_screen)
    img_h, img_w = screen.shape[:2]
    ratio = 1080 / img_h
    if ratio != 1:
        ratio = 1080 / img_h
        screen = cv2.resize(screen, (int(img_w * ratio), 1080))
    # cv2.imshow('test', screen)
    # cv2.waitKey()
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where(result >= threshold)
    h, w = template.shape[:2]
    img_h, img_w = screen.shape[:2]
    tag_set = set()
    res = []
    for pt in zip(*loc[::-1]):
        pos_key = '%d-%d' % (pt[0] / 100, pt[1] / 100)
        if pos_key in tag_set:
            continue
        tag_set.add(pos_key)
        # cv2.rectangle(screen, pt, (pt[0] + w, pt[1] + h), (7, 249, 151), 3)
        tag_w = 130
        # 检查边缘像素是否超出截图的范围
        if pt[0] + w + tag_w < img_w:
            tag = cut_tag(screen, w, pt)
            if tag is None:
                continue
            remove_holes(tag)
            tag_str = do_tag_ocr(tag)
            # res.append({'tag_img': tag, 'pos': (pt[0] + (tag_w / 2), pt[1] + 20), 'tag_str': tag_str})
            res.append({'pos': (int((pt[0] + (tag_w / 2)) / ratio), int((pt[1] + 20) / ratio)), 'tag_str': tag_str})
    return res


def do_tag_ocr(img):
    char_imgs = crop_char_img(img)
    s = ''
    for char_img in char_imgs:
        c = predict(char_img)
        s += c
    return s


stage_icon1 = pil_to_cv_gray_img(resources.load_image('stage_ocr/stage_icon1.png'))
stage_icon2 = pil_to_cv_gray_img(resources.load_image('stage_ocr/stage_icon2.png'))


def recognize_all_screen_stage_tags(pil_screen):
    tags_map = {}
    for tag in recognize_stage_tags(pil_screen, stage_icon1):
        tags_map[tag['tag_str']] = tag['pos']
    for tag in recognize_stage_tags(pil_screen, stage_icon2):
        tags_map[tag['tag_str']] = tag['pos']
    return tags_map
