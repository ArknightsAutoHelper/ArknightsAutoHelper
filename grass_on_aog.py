from Arknights.helper import ArknightsHelper
from penguin_stats import arkplanner
import requests
from datetime import datetime
import json
import os


desc = """
grass_on_aog.py
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
exclude_names = ['固源岩组', '凝胶', '炽合金', '晶体元件']
print('不刷以下材料:', exclude_names)

# cache_key = '%Y-%m-%d'  # cache by day
cache_key = '%Y--%V'    # cache by week


def get_items_from_aog_api():
    resp = requests.get('https://arkonegraph.herokuapp.com/total/CN', headers=headers)
    return resp.json()


def update_aog_cache():
    data = {'aog': get_items_from_aog_api(), 'cacheTime': datetime.now().strftime(cache_key)}
    with open('aog_cache.json', 'w') as f:
        json.dump(data, f)
    return data


def load_aog_cache():
    if os.path.exists('aog_cache.json'):
        with open('aog_cache.json', 'r') as f:
            data = json.load(f)
            if data['cacheTime'] == datetime.now().strftime(cache_key):
                return data
    return update_aog_cache()


headers = {
    'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
    'Referer': 'https://arkonegraph.herokuapp.com/',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
    'Origin': 'https://arkonegraph.herokuapp.com',
    'Connection': 'keep-alive',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Dest': 'image',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}
aog_cache = load_aog_cache()
helper = ArknightsHelper()


def load_inventory():
    if os.path.exists('inventory_items_cache.json'):
        with open('inventory_items_cache.json', 'r') as f:
            data = json.load(f)
            if data['cacheTime'] == datetime.now().strftime(cache_key):
                return data
    return update_inventory()


def update_inventory():
    data = helper.get_inventory_items(True)
    data['cacheTime'] = datetime.now().strftime(cache_key)
    with open('inventory_items_cache.json', 'w') as f:
        json.dump(data, f)
    return data


if __name__ == '__main__':
    print('加载库存信息...')
    my_items = load_inventory()
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
    helper.module_battle(stage, 1000)
