import time
from addons.base import BaseAddOn
import requests
import json
import os
from penguin_stats import arkplanner

stage_cache_file = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'stage_cache.json')
activities_cache_file = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'activities_cache.json')


def get_stage_map():
    if os.path.exists(stage_cache_file):
        with open(stage_cache_file, 'r', encoding='utf-8') as f:
            stages = json.load(f)
            return process_stages(stages)
    else:
        return update_stage_map()


def update_stage_map(use_cdn=True):
    print('更新关卡信息...')
    # https://github.com/Kengxxiao/ArknightsGameData/blob/master/zh_CN/gamedata/excel/stage_table.json
    if use_cdn:
        resp = requests.get(
            'https://cdn.jsdelivr.net/gh/Kengxxiao/ArknightsGameData@master/zh_CN/gamedata/excel/stage_table.json')
    else:
        resp = requests.get(
            'https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata'
            '/excel/stage_table.json')
    stages = resp.json()['stages']
    arkplanner.update_cache()
    with open(stage_cache_file, 'w', encoding='utf-8') as f:
        json.dump(stages, f)
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
    if os.path.exists(activities_cache_file):
        with open(activities_cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return update_activities()


def update_activities(use_cdn=True):
    print('更新活动信息...')
    # https://github.com/Kengxxiao/ArknightsGameData/blob/master/zh_CN/gamedata/excel/activity_table.json
    if use_cdn:
        resp = requests.get(
            'https://cdn.jsdelivr.net/gh/Kengxxiao/ArknightsGameData@master/zh_CN/gamedata/excel/activity_table.json')
    else:
        resp = requests.get(
            'https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata'
            '/excel/activity_table.json')
    activities = resp.json()['basicInfo']
    with open(activities_cache_file, 'w', encoding='utf-8') as f:
        json.dump(activities, f)
    return activities


def get_zones(use_cdn=True):
    print('更新章节信息...')
    # https://github.com/Kengxxiao/ArknightsGameData/blob/master/zh_CN/gamedata/excel/zone_table.json
    if use_cdn:
        resp = requests.get(
            'https://cdn.jsdelivr.net/gh/Kengxxiao/ArknightsGameData@master/zh_CN/gamedata/excel/zone_table.json')
    else:
        resp = requests.get(
            'https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata'
            '/excel/zone_table.json')
    return resp.json()['zones']


def get_stage(target_stage_code):
    stage_code_map, zone_linear_map = get_stage_map()
    if target_stage_code not in stage_code_map:
        stage_code_map, zone_linear_map = update_stage_map()
    if target_stage_code not in stage_code_map:
        raise RuntimeError(f'无效的关卡: {target_stage_code}')
    target_stage = stage_code_map[target_stage_code]
    # print(target_stage)
    if not check_activity_available(target_stage['zoneId']):
        # 活动复刻关卡的 zone id 会变化, 所以需要更新关卡信息
        stage_code_map, zone_linear_map = update_stage_map(use_cdn=False)
        if target_stage_code not in stage_code_map:
            raise RuntimeError(f'无效的关卡: {target_stage_code}')
        target_stage = stage_code_map[target_stage_code]
        print(target_stage)
        if not check_activity_available(target_stage['zoneId']):
            raise RuntimeError('活动未开放')
    stage_linear = zone_linear_map.get(target_stage['zoneId'])
    # print(stage_linear)
    return target_stage, stage_linear


def get_zone_description(zone_id):
    activity_id = zone_id.split('_')[0]
    activities = update_activities()
    act_name = activities[activity_id]['name']
    zones = get_zones()
    zone_name = zones[zone_id]['zoneNameSecond']
    return f'{act_name} - {zone_name}'


def check_activity_available(zone_id):
    activity_id = zone_id.split('_')[0]
    activities = get_activities()
    if activity_id not in activities:
        return False
    activity_info = activities[activity_id]
    cur_time = time.time()
    if activity_info['startTime'] < cur_time < activity_info['endTime']:
        return True
    activities = update_activities(use_cdn=False)
    activity_info = activities[activity_id]
    return activity_info['startTime'] < cur_time < activity_info['endTime']


class ActivityAddOn(BaseAddOn):
    def run(self, target_stage_code, repeat_times=1000):
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
        self.helper.module_battle_slim(None, repeat_times)


__all__ = ['ActivityAddOn']

if __name__ == '__main__':
    addon = ActivityAddOn()
    addon.run('SV-1')
