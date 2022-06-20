import logging
from logging import DEBUG, INFO

import cv2
import numpy as np

import app
from Arknights.addons.contrib.common_cache import read_from_common_cache, save_to_common_cache
from automator import AddonBase
from imgreco import inventory, common
from imgreco.stage_ocr import do_tag_ocr
from util import cvimage
from util.cvimage import Image

logger = logging.getLogger(__name__)
credit_store_item_values_file = app.config_path.joinpath('credit_store_item_values.yaml')


def get_credit_price(cv_screen, item_pos, ratio):
    x, y = item_pos
    x = x - int(50 * ratio)
    y = y + int(77 * ratio)
    price_img = cv_screen.array[y:y + int(28 * ratio), x:x + int(120 * ratio)]
    price_img = cv2.cvtColor(price_img, cv2.COLOR_BGR2GRAY)
    price_img = cv2.threshold(price_img, 180, 255, cv2.THRESH_BINARY)[1]
    cv2.rectangle(cv_screen.array, (x, y), (x + int(120 * ratio), y + int(28 * ratio)), (0, 255, 0))
    # show_img(price_img)
    res = do_tag_ocr(price_img)
    return int(res)


def solve(total_credit, values, prices):
    total_items = len(values) - 1
    dp = np.zeros((total_items + 1, total_credit + 1), dtype=np.int32)
    for i in range(1, total_items + 1):
        for j in range(1, total_credit + 1):
            if prices[i] <= j:
                dp[i, j] = max(dp[i - 1, j - prices[i]] + values[i], dp[i - 1, j])
            else:
                dp[i, j] = dp[i - 1, j]
    item = [0]*len(values)
    find_what(dp, total_items, total_credit, values, prices, item)
    return item


def find_what(dp, i, j, values, prices, item):  # 最优解情况
    if i >= 0:
        if dp[i][j] == dp[i - 1][j]:
            item[i] = 0
            find_what(dp, i - 1, j, values, prices, item)
        elif j - prices[i] >= 0 and dp[i][j] == dp[i - 1][j - prices[i]] + values[i]:
            item[i] = 1
            find_what(dp, i - 1, j - prices[i], values, prices, item)


def crop_image_only_outside(gray_img, raw_img, threshold=128, padding=3):
    mask = gray_img > threshold
    m, n = gray_img.shape[:2]
    mask0, mask1 = mask.any(0), mask.any(1)
    col_start, col_end = mask0.argmax(), n - mask0[::-1].argmax()
    row_start, row_end = mask1.argmax(), m - mask1[::-1].argmax()
    return raw_img[row_start - padding:row_end + padding, col_start - padding:col_end + padding]


def _find_template2(template, gray_screen, scale, center_pos=False):
    res = cv2.matchTemplate(gray_screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if center_pos:
        h, w = template.shape[:2]
        max_loc = (int(max_loc[0] + w / 2), int(max_loc[1] + h / 2))
    if scale != 1:
        max_loc = (int(max_loc[0] * scale), int(max_loc[1] * scale))
    # print(max_val, max_loc)
    return max_val, max_loc


def get_default_override_map():
    return {
        '家具零件': 0.001,
        '碳素': 0.001,
        '碳': 0.001,
        '加急许可': 0.001,
        '龙门币': 0.0036  # CE-6
    }


class AutoCreditStoreAddOn(AddonBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.info('信用商店价值数据从 credit_store_item_values.yaml 中加载, 其代表的是单位物品的理智价值, '
                         '设定为负数则永远不会购买.')
        with open(credit_store_item_values_file, 'r', encoding='utf-8') as f:
            self.value_map = app.yaml.load(f)
        self.log_text(f'store value map: {self.value_map}', DEBUG)

    def get_credit(self):
        self.logger.debug('尝试收取商店的信用点')
        res = self.match_roi('contrib/auto_credit_store/get_store_credit_btn')
        if not res:
            self.logger.debug('没有可收取的信用点')
            return
        self.logger.info('收取信用点...')
        self.tap_rect(res.bbox, post_delay=2)
        if common.check_get_item_popup(self.screenshot()):
            self.tap_rect(common.get_reward_popup_dismiss_rect(self.viewport), post_delay=2)
            self.logger.info('成功收取商店中的信用点.')

    def goto_credit_store(self):
        from Arknights.addons.record import RecordAddon
        self.addon(RecordAddon).replay_custom_record('goto_credit_store')

    def get_credit_from_friends(self):
        date = read_from_common_cache('get_credit_from_friends')
        from datetime import datetime, timedelta, timezone
        today = datetime.now().astimezone(tz=timezone(timedelta(hours=4))).strftime('%Y-%m-%d')
        if date == today:
            self.logger.debug('今天已经收取过信用点了.')
            return
        self.logger.info('尝试收取好友的信用点')
        from Arknights.addons.record import RecordAddon
        self.addon(RecordAddon).replay_custom_record('get_credit')
        save_to_common_cache('get_credit_from_friends', today)

    def run(self, get_credit_from_friends=True):
        if get_credit_from_friends:
            self.get_credit_from_friends()
        self.goto_credit_store()
        self.get_credit()
        screen = self.screenshot()
        picked_items = self.calc_items(screen)
        for picked_item in picked_items:
            self.log_text(f'buy item: {picked_item}')
            self.tap_point(picked_item['itemPos'])
            from Arknights.addons.record import RecordAddon
            self.addon(RecordAddon).replay_custom_record('buy_credit_item', quiet=True)

    def get_total_credit(self, screen):
        vh, vw = self.vh, self.vw
        rect = tuple(map(int, (100 * vw - 20.139 * vh, 3.333 * vh, 100 * vw - 2.361 * vh, 7.500 * vh)))
        credit_img = screen.crop(rect).array
        credit_img = cv2.cvtColor(credit_img, cv2.COLOR_BGR2GRAY)
        credit_img = cv2.threshold(credit_img, 140, 255, cv2.THRESH_BINARY)[1]
        return int(do_tag_ocr(credit_img, 1))

    def get_value(self, item_id: str, item_name: str, item_type: str, quantity: int):
        quantity = quantity or 1
        if item_name in self.value_map:
            sanity = self.value_map[item_name]
            return int(quantity * sanity * 100)
        self.logger.warning(f'未定义价值的物品: {item_name}')
        return 0

    def calc_items(self, screen: Image):
        self.richlogger.logimage(screen)
        total_credit = self.get_total_credit(screen)
        self.log_text(f'total_credit: {total_credit}')
        infos = inventory.get_all_item_details_in_screen(screen, exclude_item_ids={'other'},
                                                         only_normal_items=False)
        cv_screen = screen
        h, w = cv_screen.height, cv_screen.width
        ratio = h / 720
        values, prices = [0], [0]
        self.log_text(f"[itemId-itemName] x quantity: price/item_value", DEBUG)
        item_pos_map = {}
        for info in infos:
            item_value = self.get_value(info['itemId'], info['itemName'], info['itemType'], info['quantity'])
            quantity = info['quantity'] or 1
            price = get_credit_price(cv_screen, info['itemPos'], ratio)
            cv2.circle(cv_screen.array, info['itemPos'], 4, (0, 0, 255), -1)
            self.log_text(f"[{info['itemId']}-{info['itemName']}] x {quantity}: {price}/{item_value}", DEBUG)
            values.append(item_value)
            prices.append(price)
            item_pos_map[info['itemPos']] = info
        solve_items = solve(total_credit, values, prices)[1:]
        picked_items = []
        for i in range(len(solve_items)):
            if solve_items[i] == 1:
                pos = infos[i]['itemPos']
                cv2.rectangle(cv_screen.array, (pos[0] - int(64 * ratio), pos[1] - int(64 * ratio)),
                              (pos[0] + int(64 * ratio), pos[1] + int(64 * ratio)), (255, 0, 255), 2)
                picked_items.append(infos[i])
        self.richlogger.logimage(cv_screen)
        if not picked_items:
            self.log_text('信用点不足以购买任何商品.')
            return picked_items
        picked_names = [picked_item['itemName'] for picked_item in picked_items]
        self.log_text(f"picked items: {', '.join(picked_names)}")
        return picked_items

    def log_text(self, text, level=INFO):
        self.richlogger.logtext(text)
        self.logger.log(level, text)


if __name__ == '__main__':
    from Arknights.configure_launcher import helper
    helper.addon(AutoCreditStoreAddOn).run(True)
