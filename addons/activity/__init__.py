import os
import time

from addons.base import BaseAddOn
from addons.common_cache import load_game_data
from penguin_stats import arkplanner

stage_cache_file = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'stage_cache.json')
activities_cache_file = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'activities_cache.json')


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


class ActivityAddOn(BaseAddOn):
    def run(self, target_stage_code, repeat_times=1000, allow_extra_stage_icons=False):
        target_stage_code = target_stage_code.upper()
        target_stage, stage_linear = get_stage(target_stage_code)
        all_items_map = arkplanner.get_all_items_map()
        rewards = target_stage['stageDropInfo']['displayDetailRewards']
        # print(rewards)
        stage_drops = [all_items_map[reward["id"]]["name"] for reward in rewards
                       if reward["type"] == "MATERIAL" and reward["dropType"] == 2]
        print(f"{target_stage['code']}: {target_stage['name']}, 重复次数: {repeat_times}, 关卡掉落: {stage_drops}")
        record_name = f'goto_{target_stage["stageType"]}_{target_stage["zoneId"]}'
        while True:
            try:
                print(f'执行操作记录 {record_name}')
                self.helper.replay_custom_record(record_name)
                break
            except RuntimeError as e:
                if '未找到相应的记录' in str(e):
                    wait_seconds_after_touch = 5
                    c = input(f'{str(e)}, 是否录制相应操作记录(需要使用 MuMu 模拟器)[y/N]:').strip().lower()
                    if c != 'y':
                        return
                    print('录制到进入活动关卡选择界面即可, 无需点击具体的某个关卡.')
                    print(f'如果需要重新录制, 删除 custom_record 下的 {record_name} 文件夹即可.')
                    print(f'请在点击后等待 {wait_seconds_after_touch} s , 待控制台出现 "继续..." 字样, 再进行下一次点击.')
                    print(f'请在点击后等待 {wait_seconds_after_touch} s , 待控制台出现 "继续..." 字样, 再进行下一次点击.')
                    print(f'请在点击后等待 {wait_seconds_after_touch} s , 待控制台出现 "继续..." 字样, 再进行下一次点击.')
                    print(f'准备开始录制 {record_name}...')
                    self.helper.create_custom_record(record_name, roi_size=32,
                                                     description=get_zone_description(target_stage["zoneId"]),
                                                     wait_seconds_after_touch=wait_seconds_after_touch)
                else:
                    raise e
        self.helper.find_and_tap_stage_by_ocr(None, target_stage_code, stage_linear)
        return self.helper.module_battle_slim(target_stage_code, repeat_times)


if __name__ == '__main__':
    addon = ActivityAddOn()
    addon.run('SV-1')
