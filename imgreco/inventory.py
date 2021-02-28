import numpy as np
import cv2
from . import item, imgops, util
from . import stage_svm_ocr
from PIL import Image
from . import resources
import json
from util.richlog import get_logger

logger = get_logger(__name__)


def _load_net():
    with resources.open_file('resources/imgreco/inventory/ark_material.onnx') as f:
        data = f.read()
        net = cv2.dnn.readNetFromONNX(data)
        return net


ark_material_net = _load_net()


def _load_index():
    with resources.open_file('resources/imgreco/inventory/index_itemid_relation.json') as f:
        data = json.load(f)
        return data['idx2id'], data['id2idx']


idx2id, id2idx = _load_index()


def convert_pil_screen(pil_screen):
    # 720p
    cv_screen = cv2.cvtColor(np.asarray(pil_screen), cv2.COLOR_BGR2RGB)
    img_h, img_w = cv_screen.shape[:2]
    ratio = 720 / img_h
    if ratio != 1:
        ratio = 720 / img_h
        cv_screen = cv2.resize(pil_screen, (int(img_w * ratio), 720))
    return cv_screen


def get_all_item_img_in_screen(pil_screen):
    cv_screen = convert_pil_screen(pil_screen)
    gray_screen = cv2.cvtColor(cv_screen, cv2.COLOR_BGR2GRAY)
    circles = get_circles(gray_screen)
    img_h, img_w = cv_screen.shape[:2]
    if circles is None:
        return []
    res = []
    for c in circles:
        x, y, box_size = int(c[0] - int(c[2] * 2.4) // 2), int(c[1] - int(c[2] * 2.4) // 2), int(c[2] * 2.4)
        if x > 0 and x + box_size < img_w:
            # cv2.rectangle(cv_screen, (x, y), (x + box_size, y + box_size), (7, 249, 151), 3)
            cv_item_img = cv_screen[y:y + box_size, x:x + box_size, :]
            cv_item_img2 = crop_item_middle_img(cv_item_img, c[2])
            num_img = crop_number_img(cv_item_img, c[2])
            # item_img = crop_item_img(cv_screen, gray_screen, c)
            res.append({'item_img': cv_item_img, 'num_img': num_img, 'middle_img': cv_item_img2})
    return res


def get_circles(gray_img, min_radius=55, max_radius=65):
    circles = cv2.HoughCircles(gray_img, cv2.HOUGH_GRADIENT, 1, 100, param1=50,
                               param2=30, minRadius=min_radius, maxRadius=max_radius)
    return circles[0]


def crop_item_middle_img(cv_item_img, radius):
    img_h, img_w = cv_item_img.shape[:2]
    ox, oy = img_w // 2, img_h // 2
    ratio = radius / 60
    y1 = int(oy - (40 * ratio))
    y2 = int(oy + (24 * ratio))
    x1 = int(ox - (32 * ratio))
    x2 = int(ox + (32 * ratio))
    return cv2.resize(cv_item_img[y1:y2, x1:x2], (64, 64))


def crop_number_img(cv_item_img, radius):
    img_h, img_w = cv_item_img.shape[:2]
    ox, oy = img_w // 2, img_h // 2
    ratio = radius / 60
    y1 = int(oy + (28 * ratio))
    y2 = int(oy + (54 * ratio))
    x1 = int(ox - (20 * ratio))
    x2 = int(ox + (46 * ratio))
    return cv_item_img[y1:y2, x1:x2]


def show_img(cv_img):
    cv2.imshow('test', cv_img)
    cv2.waitKey()


def get_item_id(cv_img):
    blob = cv2.dnn.blobFromImage(cv_img)
    ark_material_net.setInput(blob)
    out = ark_material_net.forward()

    # Get a class with a highest score.
    out = out.flatten()
    classId = np.argmax(out)
    return idx2id[classId]


def get_quantity(num_img):
    logger.logimage(convert_to_pil(num_img))
    threshold = cv2.cvtColor(num_img, cv2.COLOR_BGR2GRAY)
    threshold = cv2.threshold(threshold, 170, 255, cv2.THRESH_BINARY)[1]
    remove_holes(threshold)
    logger.logimage(convert_to_pil(threshold))
    numimg = convert_to_pil(threshold)
    numimg = imgops.crop_blackedge2(numimg, 120)

    if numimg is not None:
        numimg = imgops.clear_background(numimg, 120)
        logger.logimage(numimg)
        cached = item.load_data()
        numtext, score = cached.num_recognizer.recognize2(numimg, subset='0123456789万')
        logger.logtext('quantity: %s, minscore: %f' % (numtext, score))
        quantity = int(numtext) if numtext.isdigit() else None
        return quantity

    return None


def convert_to_pil(cv_img):
    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))


def remove_holes(img):
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for i in range(len(contours)):
        (x, y, w, h) = cv2.boundingRect(contours[i])
        # area = cv2.contourArea(contours[i])
        # cv2.rectangle()
        area = np.count_nonzero(img[y:y+h, x:x+w])
        if area < 28 or area > 100:
            cv2.drawContours(img, [contours[i]], 0, 0, -1)


def get_all_item_in_screen(screen):
    imgs = get_all_item_img_in_screen(screen)
    item_count_map = {}
    for item_img in imgs:
        logger.logimage(convert_to_pil(item_img['item_img']))
        item_id = get_item_id(item_img['middle_img'])
        logger.logtext('item_id: %s' % item_id)
        if item_id == 'other':
            continue
        quantity = get_quantity(item_img['num_img'])
        item_count_map[item_id] = quantity
        # print(item_id, quantity)
        # show_img(item_img['item_img'])
    logger.logtext('item_count_map: %s' % item_count_map)
    return item_count_map


def get_inventory_rect(viewport):
    vw, vh = util.get_vwvh(viewport)
    return 100 * vw - 17.361 * vh, 81.944 * vh, 100 * vw - 6.111 * vh, 96.806 * vh

