import logging
import os
import random
import time
from functools import lru_cache

import cv2
import numpy as np

import imgreco.main
from automator import AddonBase
from ..activity import get_stage_map
from ..base import pil2cv, crop_cv_by_rect, show_img
from ..common_cache import load_game_data
from imgreco.ocr.cnocr import ocr_and_correct
from ...common import CommonAddon
from ...stage_navigator import StageNavigator
from ...record import RecordAddon
from imgreco import resources

icon1 = resources.load_image('contrib/start_sp_stage/icon1.png', imread_flags=cv2.IMREAD_GRAYSCALE).array
icon2 = resources.load_image('contrib/start_sp_stage/icon2.png', imread_flags=cv2.IMREAD_GRAYSCALE).array


special_zone_actions = {
    'act11d7_zone2': {'type': 'custom_record', 'record_name': 'switch_to_act11d7_zone2'}
}


@lru_cache(maxsize=1)
def get_activity_infos():
    return load_game_data('activity_table')['basicInfo']


@lru_cache()
def get_available_activity(display_type=None):
    activity_infos = get_activity_infos()
    name_set = set()
    for aid, info in activity_infos.items():
        if info.get('displayType') in {'SIDESTORY', 'BRANCHLINE'}:
            if info['displayType'] == 'BRANCHLINE' or info.get('isReplicate'):
                raw_name = info['name'][:-3] if info.get('isReplicate') else info['name']
                if display_type is None or display_type == info['displayType']:
                    name_set.add(raw_name)
    return name_set


def get_activity_name(activity):
    name = activity['name']
    if activity['isReplicate']:
        return name[:-3]
    return name


def crop_image_only_outside(gray_img, raw_img, threshold=128, padding=3):
    mask = gray_img > threshold
    m, n = gray_img.shape
    mask0, mask1 = mask.any(0), mask.any(1)
    col_start, col_end = mask0.argmax(), n - mask0[::-1].argmax()
    row_start, row_end = mask1.argmax(), m - mask1[::-1].argmax()
    return raw_img[row_start - padding:row_end + padding, col_start - padding:col_end + padding]


class StartSpStageAddon(AddonBase):
    def on_attach(self):
        self.addon(StageNavigator).register_navigator(
            self.__class__.__name__,
            lambda stage: self.run(stage, query_only=True),
            lambda stage: self.run(stage, query_only=False)
        )

    def apply_scale(self, value):
        if self.scale == 1:
            return value
        return int(value * self.scale)

    def run(self, stage_code: str, query_only=False):
        stage_code = stage_code.upper()
        stage_code_map, zone_linear_map = get_stage_map()
        if query_only:
            return stage_code in stage_code_map
        if stage_code not in stage_code_map:
            raise RuntimeError(f'无效的关卡: {stage_code}')
        self.scale = self.viewport[1] / 720
        if self.viewport != (1280, 720):
            self.logger.warning('It may produce some weird effects when the resolution is not 1280x720.')
        stage = stage_code_map[stage_code]
        activity_id = stage['zoneId'].split('_')[0]
        activity_infos = get_activity_infos()
        activity = activity_infos[activity_id]
        self.logger.debug(f'stage: {stage}, activity: {activity}')
        self.enter_activity(activity)
        self.after_enter_activity(stage)
        stage_linear = zone_linear_map[stage['zoneId']]
        self.logger.info(f"stage zone id: {stage['zoneId']}, stage_linear: {stage_linear}")
        self.addon(StageNavigator).find_and_tap_stage_by_ocr(None, stage_code, stage_linear)

    def after_enter_activity(self, stage):
        zone_id = stage['zoneId']
        if zone_id in special_zone_actions:
            zone_act = special_zone_actions[zone_id]
            if zone_act['type'] == 'custom_record':
                self.addon(RecordAddon).replay_custom_record(zone_act['record_name'])

    def enter_activity(self, activity):
        vh = self.vh
        act_name = get_activity_name(activity)
        if act_name not in get_available_activity():
            raise RuntimeError(f'无效的活动: {act_name}')
        self.open_terminal()
        if activity['displayType'] == 'BRANCHLINE':
            self.tap_branch_line()
        else:
            self.tap_side_story()
        crop_flag = activity['displayType'] == 'SIDESTORY'
        act_pos_map = self.get_all_act_pos(crop_flag)
        if act_name not in act_pos_map:
            if activity['displayType'] == 'BRANCHLINE':
                raise RuntimeError(f'找不到相应活动: {act_name}')
            last_acts = act_pos_map.keys()
            while True:
                origin_x = random.randint(int(5.833 * vh), int(24.861 * vh))
                origin_y = random.randint(int(57.222 * vh), int(77.917 * vh))
                move = -random.randint(int(vh // 5), int(vh // 4))
                self.device.touch_swipe2((origin_x, origin_y),
                                             (random.randint(-20, 20), move), random.randint(900, 1200))
                act_pos_map = self.get_all_act_pos(crop_flag)
                if act_name in act_pos_map:
                    break
                if last_acts == act_pos_map.keys():
                    raise RuntimeError(f'找不到相应活动: {act_name}')
                last_acts = act_pos_map.keys()
        self.logger.info(f'switch to {act_name}')
        self.tap_point(act_pos_map[act_name], 1)
        self.tap_enter_activity()

    def tap_back(self):
        vw, vh = self.vw, self.vh
        self.helper.tap_rect((2.222 * vh, 1.944 * vh, 22.361 * vh, 8.333 * vh))
        self.delay(0.5)

    def screenshot(self):
        return self.device.screenshot()

    def get_all_act_pos(self, crop=False):
        act_map = {}
        screen = self.screenshot()
        cv_screen = pil2cv(screen)
        for icon in [icon1, icon2]:
            act_map.update(self.get_act_pos_by_icon(cv_screen, icon, crop))
        self.logger.info(act_map)
        return act_map

    def get_act_pos_by_icon(self, cv_screen, icon, crop=False):
        vh, vw = self.vh, self.vw
        raw_screen = cv_screen.copy()
        if self.scale != 1:
            cv_screen = cv2.resize(cv_screen, (int(self.helper.viewport[0] / self.scale), 720))
        roi = crop_cv_by_rect(cv_screen, (0, 0, 10.000 * vh, 100.000 * vh))
        roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        result = cv2.matchTemplate(roi, icon, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= 0.8)
        tag_set = set()
        tag_set2 = set()
        res = {}
        dbg_screen = raw_screen.copy()
        available_activity = get_available_activity()
        for pt in zip(*loc[::-1]):
            pos_key = (pt[0] // 100, pt[1] // 100)
            pos_key2 = (int(pt[0] / 100 + 0.5), int(pt[1] / 100 + 0.5))
            if pos_key in tag_set or pos_key2 in tag_set2:
                continue
            tag_set.add(pos_key)
            tag_set2.add(pos_key2)
            if icon1 is icon:
                x, y = (int(pt[0]) + 35, int(pt[1]) - 6)
                tw, th = map(self.apply_scale, (180, 40))
            else:
                x, y = (int(pt[0]) + 35, int(pt[1]) - 3)
                tw, th = map(self.apply_scale, (150, 30))
            l, t = map(self.apply_scale, (x, y))
            tag_img = raw_screen[t:t + th, l:l + tw]
            if crop:
                gray_tag = cv2.cvtColor(tag_img, cv2.COLOR_RGB2GRAY)
                tag_img = crop_image_only_outside(gray_tag, tag_img, 160)
            factor = 2.5 - self.scale
            if factor > 1:
                # print(factor)
                tag_img = cv2.resize(tag_img, (0, 0), fx=factor, fy=factor, interpolation=cv2.INTER_LINEAR)
            # show_img(tag_img)
            # conv-lite-fc has better accuracy, but it is slower than densenet-lite-fc.
            name = ocr_and_correct(tag_img, available_activity, model_name='densenet-lite-fc', log_level=logging.INFO)
            if name:
                res[name] = (int(l + 85 * self.scale), int(t + 20 * self.scale))
            cv2.rectangle(dbg_screen, (l, t), (l + tw, t + th), (255, 255, 0), 2)
        # show_img(dbg_screen)
        return res

    def tap_side_story(self):
        vh, vw = self.vh, self.vw
        self.logger.info('open side story view')
        self.helper.tap_rect((44.297 * vw, 88.611 * vh, 56.406 * vw, 98.750 * vh))
        self.delay(1)

    def tap_branch_line(self):
        self.logger.info('open branch line view')
        vh, vw = self.vh, self.vw
        self.helper.tap_rect((29.375 * vw, 88.611 * vh, 41.719 * vw, 98.750 * vh))
        self.delay(1)

    def tap_enter_activity(self):
        self.logger.info('enter activity')
        vh, vw = self.vh, self.vw
        self.helper.tap_rect((100 * vw - 24.583 * vh, 69.167 * vh, 100 * vw - 8.750 * vh, 75.556 * vh))
        self.delay(1)

    def open_terminal(self):
        self.addon(CommonAddon).back_to_main()
        self.logger.info('open terminal')
        self.helper.tap_quadrilateral(imgreco.main.get_ballte_corners(self.screenshot()))
        self.delay(1)


if __name__ == '__main__':
    StartSpStageAddon().run('OF-F4', 0, False)
    # StartSpStageAddon().get_all_act_pos()
