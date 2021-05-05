from addons.base import BaseAddOn
from penguin_stats import arkplanner
import requests
from datetime import datetime
import json
import os


desc = f"""
{__file__}
==================================================================================================
长草时用的脚本, 检查库存中最少的蓝材料, 然后去 aog 上推荐的地图刷材料.
aog 地址: https://arkonegraph.herokuapp.com/

不想的刷的材料可以修改脚本中的 exclude_names.

cache_key 控制缓存的频率, 默认每周读取一次库存, 如果需要手动更新缓存, 
直接删除目录下的 aog_cache.json 和 inventory_items_cache.json 即可.

只刷常规关卡, 活动关卡不刷.

可以尝试将 config/config.yaml 中的 behavior/use_ocr_goto_stage 修改为 true 以支持更多的关卡跳转
==================================================================================================
"""
print(desc)

# 不刷以下材料
exclude_names = ['固源岩组']
print('不刷以下材料:', exclude_names)

# cache_key = '%Y-%m-%d'  # cache by day
cache_key = '%Y--%V'    # cache by week


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
                normal_stage_info = t3_item['lowest_ap_stages']['normal'][0]
                stage = normal_stage_info['code']
                print('aog stage:', stage)
                break
        self.helper.module_battle(stage, 1000)

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
