import json
import logging
import os
import time
from functools import lru_cache

import textdistance

import app
from Arknights.addons.common import CommonAddon
from Arknights.addons.contrib.common_cache import load_game_data
from Arknights.addons.record import RecordAddon
from Arknights.addons.stage_navigator import StageNavigator, navigator
from automator import AddonBase
from imgreco import main
from imgreco.ppocr_utils import detect_box, get_ppocr
from penguin_stats import arkplanner
from util.cvimage import Image

stage_cache_file = app.cache_path.joinpath('stage_cache.json')
activities_cache_file = app.cache_path.joinpath('activities_cache.json')
detect_cache_file = app.cache_path.joinpath('activity_detect_cache.json')

logger = logging.getLogger(__name__)


def get_stage_map():
    stages = load_game_data('stage_table')['stages']
    return process_stages(stages)


def process_stages(stages):
    stage_code_map = {}
    zone_linear_map = {}
    for stage_id in stages.keys():
        stage = stages[stage_id]
        if stage_code_map.get(stage['code']) is not None:
            continue
        stage_code_map[stage['code']] = stage
        l = zone_linear_map.get(stage['zoneId'], [])
        l.append(stage['code'])
        zone_linear_map[stage['zoneId']] = l
    return stage_code_map, zone_linear_map


def get_activities():
    return load_game_data('activity_table')['basicInfo']


def get_zones():
    return load_game_data('zone_table')['zones']


def get_stage(target_stage_code):
    stage_code_map, zone_linear_map = get_stage_map()
    if target_stage_code not in stage_code_map:
        raise RuntimeError(f'无效的关卡: {target_stage_code}')
    target_stage = stage_code_map[target_stage_code]
    if not check_activity_available(target_stage['zoneId']):
        raise RuntimeError('活动未开放')
    stage_linear = zone_linear_map.get(target_stage['zoneId'])
    return target_stage, stage_linear


def get_zone_description(zone_id):
    activity_id = zone_id.split('_')[0]
    activities = get_activities()
    act_name = activities[activity_id]['name']
    zones = get_zones()
    zone_name = zones[zone_id]['zoneNameSecond']
    return f'{act_name} - {zone_name}'


def get_activity_name(zone_id):
    activity_id = zone_id.split('_')[0]
    activities = get_activities()
    return activities[activity_id]['name']


def get_zone_name(zone_id):
    zones = get_zones()
    zone_name = zones[zone_id]['zoneNameSecond']
    return zone_name


def check_activity_available(zone_id):
    activity_id = zone_id.split('_')[0]
    activities = get_activities()
    if activity_id not in activities:
        return False
    cur_time = time.time()
    activity_info = activities[activity_id]
    return activity_info['startTime'] < cur_time < activity_info['endTime']


@lru_cache(1)
def load_detect_cache():
    """
    {
        'zoneId': [x, y]
    }
    if pos == [-1, -1] that means detect result is negative
    """
    if not os.path.exists(detect_cache_file):
        return {}
    with open(detect_cache_file, 'r') as f:
        return json.load(f)


def has_success_detect(zone_id):
    detect_cache = load_detect_cache()
    res = detect_cache.get(zone_id)
    return res != [-1, -1]


def get_detect_result_from_cache(zone_id):
    detect_cache = load_detect_cache()
    return detect_cache.get(zone_id)


def save_detect_result(zone_id, pos):
    detect_cache = load_detect_cache()
    detect_cache[zone_id] = pos
    with open(detect_cache_file, 'w') as f:
        json.dump(detect_cache, f)
        load_detect_cache.cache_clear()


class ActivityAddOn(AddonBase):
    def __init__(self, helper):
        super().__init__(helper)
        self.delay_after_open_activity = 5

    @navigator
    def nav(self, stage):
        return self.run(stage, query_only=True)

    @nav.navigate
    def run(self, target_stage_code, query_only=False):
        target_stage_code = target_stage_code.upper()
        try:
            target_stage, stage_linear = get_stage(target_stage_code)
        except Exception:
            if query_only:
                return False
            raise
        all_items_map = arkplanner.get_all_items_map()
        rewards = target_stage['stageDropInfo']['displayDetailRewards']
        # print(rewards)
        stage_drops = [all_items_map[reward["id"]]["name"] for reward in rewards
                       if reward["type"] == "MATERIAL" and reward["dropType"] == 2]
        record_name = f'goto_{target_stage["stageType"]}_{target_stage["zoneId"]}'
        if query_only:
            return self.addon(RecordAddon).get_record_path(record_name) or has_success_detect(target_stage["zoneId"])
        self.logger.info(f"{target_stage['code']}: {target_stage['name']}, 关卡掉落: {stage_drops}")
        if has_success_detect(target_stage["zoneId"]) or not self.addon(RecordAddon).get_record_path(record_name):
            pos = self.try_detect_and_enter_zone(target_stage)
            if pos != [-1, -1]:
                self.try_find_and_tap_stage_by_ocr(target_stage['zoneId'], target_stage_code, stage_linear, pos)
            elif self.create_record_for_activity(target_stage['code'], record_name):
                self.logger.info(f'执行操作记录 {record_name}')
                self.addon(RecordAddon).replay_custom_record(record_name)
                self.addon(StageNavigator).find_and_tap_stage_by_ocr(None, target_stage_code, stage_linear)
        elif self.addon(RecordAddon).try_replay_record(record_name, True):
            self.addon(StageNavigator).find_and_tap_stage_by_ocr(None, target_stage_code, stage_linear)

    def nav_and_combat(self, target_stage_code, times=1000):
        self.run(target_stage_code)
        from Arknights.addons.combat import CombatAddon
        return self.addon(CombatAddon).combat_on_current_stage(times)

    def create_record_for_activity(self, target_stage_code, record_name):
        target_stage_code = target_stage_code.upper()
        target_stage, stage_linear = get_stage(target_stage_code)
        wait_seconds_after_touch = 5
        print('录制到进入活动关卡选择界面即可, 无需点击具体的某个关卡.')
        print(f'如果需要重新录制, 删除 custom_record 下的 {record_name} 文件夹即可.')
        print(f'请在点击后等待 {wait_seconds_after_touch} s , 待控制台出现 "继续..." 字样, 再进行下一次点击.')
        print(f'请在点击后等待 {wait_seconds_after_touch} s , 待控制台出现 "继续..." 字样, 再进行下一次点击.')
        print(f'请在点击后等待 {wait_seconds_after_touch} s , 待控制台出现 "继续..." 字样, 再进行下一次点击.')
        print(f'准备开始录制 {record_name}...')
        self.addon(RecordAddon).create_custom_record(record_name, roi_size=32,
                                            description=get_zone_description(target_stage["zoneId"]),
                                            wait_seconds_after_touch=wait_seconds_after_touch)
        return True

    def try_detect_and_enter_zone(self, target_stage):
        detect_result = get_detect_result_from_cache(target_stage['zoneId'])
        if detect_result is None:
            logger.info('No detect cache found, try to detect zone with ppocr.')
            self.open_target_activity(target_stage)
            return self.detect_and_enter_zone(target_stage)
        elif detect_result != [-1, -1]:
            self.open_target_activity(target_stage)
            logger.info(f'get detect result from cache: {detect_result}')
            self.tap_point(detect_result, 2, randomness=(2, 2))
        return detect_result

    def detect_and_enter_zone(self, target_stage):
        zone_name = get_zone_name(target_stage['zoneId'])
        logger.info(f"target zone name: {zone_name}")
        screen = self.screenshot()
        box_center, max_score = detect_box(screen, zone_name)
        self.tap_point(box_center, 2, randomness=(2, 2))
        return box_center

    def open_terminal(self):
        logger.info('open terminal')
        self.tap_quadrilateral(main.get_ballte_corners(self.screenshot()))
        self.delay(1)

    def open_target_activity(self, target_stage):
        self.addon(CommonAddon).back_to_main()
        activity_name = get_activity_name(target_stage['zoneId'])
        if activity_name.endswith('·复刻'):
            activity_name = activity_name[:-3]
        if self.open_activity_from_homepage(activity_name):
            return
        self.open_terminal()
        screen = self.screenshot()
        if self.check_current_activity(screen, activity_name):
            vh, vw = self.vh, self.vw
            activity_rect = (14.583 * vh, 71.944 * vh, 57.639 * vh, 83.333 * vh)
            logger.info('open current activity')
            self.tap_rect(activity_rect)
            self.delay(self.delay_after_open_activity)
        else:
            box_center = self.detect_middle_activity(screen, activity_name)
            if box_center is None:
                self.logger.error(f'cannot find activity {activity_name}')
                raise RuntimeError(f'cannot find activity {activity_name}')
            self.logger.info(f'open activity {activity_name}')
            self.tap_point(box_center, self.delay_after_open_activity, randomness=(2, 2))

    def check_current_activity(self, screen: Image, activity_name):
        vh, vw = self.vh, self.vw
        activity_rect = screen.crop((12.083*vh, 72.222*vh, 54.167*vh, 80.278*vh))
        results = get_ppocr().detect_and_ocr(activity_rect.array)
        max_score = 0
        max_text = ''
        for result in results:
            text = result.ocr_text
            try:
                idx = text.index('<') + 1
                text = text[idx:]
            except:
                pass
            try:
                idx = text.index('>')
                text = text[:idx]
            except:
                pass
            score = textdistance.sorensen(activity_name, text)
            if score > max_score:
                max_score = score
                max_text = text
        self.logger.info(f'check current activity, max text: {max_text}, score: {max_score}')
        return max_score > 0.3

    def detect_middle_activity(self, screen: Image, activity_name):
        vh, vw = self.vh, self.vw
        middle_rect = screen.crop((43.750*vw, 14.722*vh, 71.406*vw, 83.056*vh))
        box_center, max_score = detect_box(middle_rect, activity_name, no_scale=True)
        if max_score > 0.3:
            return box_center[0] + 43.750*vw, box_center[1] + 14.722*vh

    def open_activity_from_homepage(self, activity_name):
        screen = self.screenshot()
        w, h = self.viewport
        start_x = w - w // 3
        right_area = screen.crop((start_x, 0, w, h // 2))
        box_center, max_score = detect_box(right_area, activity_name, no_scale=True)
        if max_score > 0.4:
            logger.info(f"检测到 {activity_name} 活动, 可能是当前活动, 尝试打开...")
            box_center = box_center[0] + start_x, box_center[1]
            self.tap_point(box_center, self.delay_after_open_activity)
            return True
        return False

    def try_find_and_tap_stage_by_ocr(self, zone_id, target_stage_code, stage_linear, pos):
        try:
            self.logger.debug(f'target stage code: {target_stage_code}, stage linear: {stage_linear}')
            self.addon(StageNavigator).find_and_tap_stage_by_ocr(None, target_stage_code, stage_linear)
            save_detect_result(zone_id, pos)
        except Exception as e:
            save_detect_result(zone_id, [-1, -1])
            raise e


if __name__ == '__main__':
    from Arknights.configure_launcher import helper
    helper.addon(ActivityAddOn).nav_and_combat('dv-8', 1)
