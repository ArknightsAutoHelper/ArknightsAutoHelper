import numpy as np
import cv2
from . import item, imgops, common
from util import cvimage as Image
from util.richlog import get_logger

logger = get_logger(__name__)
exclude_items = {'32001', 'other', '3401'}

# circle size 128x128
item_circle_radius = 64
itemreco_box_size = 142  # dimension that compatible with imgreco.item
half_box = itemreco_box_size // 2


def scale_screen(screen: np.ndarray):
    # 720p
    cv_screen = screen
    img_h, img_w = cv_screen.shape[:2]
    ratio = 720 / img_h
    if ratio != 1:
        ratio = 720 / img_h
        cv_screen = cv2.resize(cv_screen, (int(img_w * ratio), 720))
    return cv_screen


def group_pos(ys):
    tmp = {}
    for y in ys:
        flag = True
        for k, v in tmp.items():
            if abs(y - k) < 20:
                v.append(y)
                flag = False
                break
        if flag:
            tmp[y] = [y]
    res = [sum(v) // len(v) for v in tmp.values()]
    res.sort()
    return res


def get_all_item_img_in_screen(screen, use_group_pos=True):
    cv_screen = scale_screen(screen.array)
    gray_screen = cv2.cvtColor(cv_screen, cv2.COLOR_BGR2GRAY)
    dbg_screen = cv_screen.copy()
    # cv2.HoughCircles seems works fine for now
    circles: np.ndarray = get_circles(gray_screen)
    img_h, img_w = cv_screen.shape[:2]
    if circles is None:
        return []
    res = []
    if use_group_pos:
        center_ys = group_pos(circles[:, 1])
        center_xs = group_pos(circles[:, 0])
        for center_x in center_xs:
            if center_x - half_box < 0 or center_x + half_box > img_w:
                continue
            xf = center_x - half_box
            x = int(xf)
            x2 = x + itemreco_box_size
            if x2 < img_w:
                for center_y in center_ys:
                    res.append(get_item_img(screen, cv_screen, dbg_screen, center_x, center_y))
    for center_x, center_y, r in circles:
        cv2.circle(dbg_screen, (int(center_x), int(center_y)), int(r), (0, 0, 255), 2)
        if not use_group_pos:
            res.append(get_item_img(screen, cv_screen, dbg_screen, center_x, center_y))

    logger.logimage(Image.fromarray(dbg_screen, 'BGR'))
    return res


def get_item_img(pil_screen, cv_screen, dbg_screen, center_x, center_y):
    img_h, img_w = cv_screen.shape[:2]
    x, y = int(center_x - half_box), int(center_y - half_box)
    if x < 0 or x + itemreco_box_size > img_w:
        return None
    cv_item_img = cv_screen[y:y + itemreco_box_size, x:x + itemreco_box_size]

    # use original size for better quantity recognition
    ratio = img_h / pil_screen.height
    original_item_img = pil_screen.crop((int(x / ratio), int(y / ratio), int((x + itemreco_box_size) / ratio),
                                         int((y + itemreco_box_size) / ratio)))
    numimg = imgops.scalecrop(original_item_img, 0.39, 0.705, 0.82, 0.85).convert('L')
    cv2.rectangle(dbg_screen, (x, y), (x + itemreco_box_size, y + itemreco_box_size), (255, 0, 0), 2)
    return {'item_img': cv_item_img, 'num_img': numimg,
            'item_pos': (int((x + itemreco_box_size // 2) / ratio), int((y + itemreco_box_size // 2) / ratio))}


def remove_holes(img):
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for i in range(len(contours)):
        area = cv2.contourArea(contours[i])
        if area < 8:
            cv2.drawContours(img, [contours[i]], 0, 0, -1)


def crop_num_img(item_img):
    img_h, img_w = item_img.shape[:2]
    l, t, r, b = tuple(map(int, (img_w * 0.39, img_h * 0.68, img_w * 0.82, img_h * 0.87)))
    return item_img[t:b, l:r]


def get_circles(gray_img, min_radius=56, max_radius=68):
    circles = cv2.HoughCircles(gray_img, cv2.HOUGH_GRADIENT, 1, 100, param1=128,
                               param2=30, minRadius=min_radius, maxRadius=max_radius)
    return circles[0]

def convert_to_pil(cv_img):
    return Image.fromarray(cv_img)


def get_all_item_in_screen(screen):
    imgs = get_all_item_img_in_screen(screen)
    item_count_map = {}
    for item_img in imgs:
        logger.logimage(Image.fromarray(item_img['item_img'], 'BGR'))
        itemreco = item.tell_item(Image.fromarray(item_img['item_img'], 'BGR'), with_quantity=True)
        logger.logtext('%r' % itemreco)
        if itemreco.item_id is None or itemreco.item_id in exclude_items or itemreco.item_type == 'ACTIVITY_ITEM':
            continue
        item_count_map[itemreco.item_id] = itemreco.quantity
        # print(item_id, quantity)
        # show_img(item_img['item_img'])
    logger.logtext('item_count_map: %s' % item_count_map)
    return item_count_map


def get_all_item_details_in_screen(screen, exclude_item_ids=None, exclude_item_types=None, only_normal_items=True):
    if exclude_item_ids is None:
        exclude_item_ids = exclude_items
    if exclude_item_types is None:
        exclude_item_types = {'ACTIVITY_ITEM'}
    imgs = get_all_item_img_in_screen(screen)
    res = []
    for item_img in imgs:
        logger.logimage(Image.fromarray(item_img['item_img'], 'BGR'))
        itemreco = item.tell_item(Image.fromarray(item_img['item_img']), with_quantity=True)
        logger.logtext('%r' % itemreco)
        if itemreco.item_id is None:
            continue
        if itemreco.item_id in exclude_item_ids or itemreco.item_type in exclude_item_types:
            continue
        if only_normal_items and (not itemreco.item_id.isdigit() or len(itemreco.item_id) < 5 or itemreco.item_type != 'MATERIAL'):
            continue
        res.append({'itemId': itemreco.item_id, 'itemName': itemreco.name, 'itemType': itemreco.item_type,
                    'quantity': itemreco.quantity, 'itemPos': item_img['item_pos']})
    logger.logtext('res: %s' % res)
    return res


def get_inventory_rect(viewport):
    vw, vh = common.get_vwvh(viewport)
    return 100 * vw - 17.361 * vh, 81.944 * vh, 100 * vw - 6.111 * vh, 96.806 * vh
