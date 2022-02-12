import os
import time

import app
from automator import AddonBase
from ..common_cache import load_game_data
from penguin_stats import arkplanner

from ...stage_navigator import StageNavigator, navigator
from ...record import RecordAddon

stage_cache_file = app.cache_path.joinpath('stage_cache.json')
activities_cache_file = app.cache_path.joinpath('activities_cache.json')


def get_stage_map(force_update=False):
    stages = load_game_data('stage_table', force_update)['stages']
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


def get_activities(force_update=False):
    return load_game_data('activity_table', force_update)['basicInfo']


def get_zones(force_update=False):
    return load_game_data('zone_table', force_update=force_update)['zones']


def get_stage(target_stage_code):
    stage_code_map, zone_linear_map = get_stage_map()
    if target_stage_code not in stage_code_map:
        stage_code_map, zone_linear_map = get_stage_map(force_update=True)
        if target_stage_code not in stage_code_map:
            raise RuntimeError(f'无效的关卡: {target_stage_code}')
    target_stage = stage_code_map[target_stage_code]
    # print(target_stage)
    if not check_activity_available(target_stage['zoneId']):
        # 活动复刻关卡的 zone id 会变化, 所以需要更新关卡信息
        stage_code_map, zone_linear_map = get_stage_map(force_update=True)
        if target_stage_code not in stage_code_map:
            raise RuntimeError(f'无效的关卡: {target_stage_code}')
        target_stage = stage_code_map[target_stage_code]
        # print(target_stage)
        if not check_activity_available(target_stage['zoneId']):
            raise RuntimeError('活动未开放')
    stage_linear = zone_linear_map.get(target_stage['zoneId'])
    # print(stage_linear)
    return target_stage, stage_linear


def get_zone_description(zone_id):
    activity_id = zone_id.split('_')[0]
    activities = get_activities()
    act_name = activities[activity_id]['name']
    zones = get_zones()
    zone_name = zones[zone_id]['zoneNameSecond']
    return f'{act_name} - {zone_name}'


def check_activity_available(zone_id):
    activity_id = zone_id.split('_')[0]
    activities = get_activities()
    if activity_id not in activities:
        activities = get_activities(force_update=True)
        if activity_id not in activities:
            return False
    cur_time = time.time()
    activity_info = activities[activity_id]
    return activity_info['startTime'] < cur_time < activity_info['endTime']


class ActivityAddOn(AddonBase):
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
            return self.addon(RecordAddon).get_record_path(record_name)
        self.logger.info(f"{target_stage['code']}: {target_stage['name']}, 关卡掉落: {stage_drops}")
        self.logger.info(f'执行操作记录 {record_name}')
        self.addon(RecordAddon).replay_custom_record(record_name)
        self.addon(StageNavigator).find_and_tap_stage_by_ocr(None, target_stage_code, stage_linear)

    def create_record_for_activity(self, target_stage_code):
        target_stage_code = target_stage_code.upper()
        target_stage, stage_linear = get_stage(target_stage_code)
        # print(rewards)
        record_name = f'goto_{target_stage["stageType"]}_{target_stage["zoneId"]}'
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

if __name__ == '__main__':
    addon = ActivityAddOn()
    addon.run('SV-1')
