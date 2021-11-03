from addons.base import BaseAddOn
from penguin_stats import arkplanner
import requests
from datetime import datetime
import json
import os
import config
from Arknights.helper import logger


desc = f"""
{__file__}
==================================================================================================
长草时用的脚本, 检查库存中最少的蓝材料, 然后去 aog 上推荐的地图刷材料.
aog 地址: https://arkonegraph.herokuapp.com/

不想的刷的材料可以修改脚本中的 exclude_names.

cache_key 控制缓存的频率, 默认每周读取一次库存, 如果需要手动更新缓存, 
直接删除目录下的 aog_cache.json 和 inventory_items_cache.json 即可.

活动关卡需要安装 cnocr 并将 addons/grass_on_aog/use_start_sp_stage 配置为 true.
==================================================================================================
"""
print(desc)

# 不刷以下材料
exclude_names = ['固源岩组']
print('不刷以下材料:', exclude_names)

# cache_key = '%Y-%m-%d'  # cache by day
cache_key = '%Y--%V'    # cache by week


use_start_sp_stage = config.get('addons/grass_on_aog/use_start_sp_stage', False)


aog_cache_file = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'aog_cache.json')
inventory_cache_file = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'inventory_items_cache.json')


def get_items_from_aog_api():
    resp = requests.get('https://arkonegraph.herokuapp.com/total/CN')
    return resp.json()


def update_aog_cache():
    data = {'aog': get_items_from_aog_api(), 'cacheTime': datetime.now().strftime(cache_key)}
    with open(aog_cache_file, 'w') as f:
        json.dump(data, f)
    return data


def load_aog_cache():
    if os.path.exists(aog_cache_file):
        with open(aog_cache_file, 'r') as f:
            data = json.load(f)
            if data['cacheTime'] == datetime.now().strftime(cache_key):
                return data
    return update_aog_cache()


def order_stage(item):
    if item['lowest_ap_stages']['normal'] and item['lowest_ap_stages']['event']:
        stage_type = 'lowest_ap_stages'
    elif item['balanced_stages']['normal'] and item['balanced_stages']['event']:
        stage_type = 'balanced_stages'
    else:
        stage_type = 'drop_rate_first_stages'
    event = item[stage_type]['event'][0]
    normal = item[stage_type]['normal'][0]
    return event if event['efficiency'] >= normal['efficiency'] else normal


class GrassAddOn(BaseAddOn):
    def run(self, **kwargs):
        print('加载库存信息...')
        aog_cache = load_aog_cache()
        my_items = self.load_inventory()
        all_items = arkplanner.get_all_items()

        l = []
        for item in all_items:
            if item['itemType'] in ['MATERIAL'] and item['name'] not in exclude_names and item['rarity'] == 2 \
                    and len(item['itemId']) > 4:
                l.append({'name': item['name'],
                          'itemId': item['itemId'],
                          'count': my_items.get(item['itemId'], 0),
                          'rarity': item['rarity']})
        l = sorted(l, key=lambda x: x['count'])
        print('require item: %s, owned: %s' % (l[0]['name'], l[0]['count']))
        aog_items = aog_cache['aog']
        t3_items = aog_items['tier']['t3']
        stage = ''
        for t3_item in t3_items:
            if t3_item['name'] == l[0]['name']:
                # print(t3_item)
                stage_info = order_stage(t3_item)
                stage = stage_info['code']
                print('aog stage:', stage)
                break
        try:
            self.helper.module_battle(stage, 1000)
        except Exception as e:
            if use_start_sp_stage:
                from addons.start_sp_stage import StartSpStageAddon
                logger.info('尝试进入活动关卡')
                StartSpStageAddon(self.helper).run(stage, 1000)
            else:
                raise e

    def load_inventory(self):
        if os.path.exists(inventory_cache_file):
            with open(inventory_cache_file, 'r') as f:
                data = json.load(f)
                if data['cacheTime'] == datetime.now().strftime(cache_key):
                    return data
        return self.update_inventory()

    def update_inventory(self):
        data = self.helper.get_inventory_items(True)
        data['cacheTime'] = datetime.now().strftime(cache_key)
        with open(inventory_cache_file, 'w') as f:
            json.dump(data, f)
        return data


__all__ = ['GrassAddOn']


if __name__ == '__main__':
    addon = GrassAddOn()
    addon.run()
