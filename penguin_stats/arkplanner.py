from functools import lru_cache
import requests
import os
import json
from datetime import datetime

penguin_base_url = 'https://penguin-stats.io/PenguinStats'
cache_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'penguin_cache.json')


def update_cache():
    cache = {
        'cache_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'items': get_all_items_from_api(),
        'stages': get_all_stages_from_api()
    }
    with open(cache_path, 'w') as f:
        json.dump(cache, f)
    load_cache.cache_clear()
    return load_cache()


@lru_cache(1)
def load_cache():
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return json.load(f)
    else:
        return update_cache()


def get_all_items_from_api():
    return requests.get(penguin_base_url + '/api/v2/items').json()


def get_all_stages_from_api():
    return requests.get(penguin_base_url + '/api/v2/stages').json()


def get_all_items():
    return load_cache()['items']


def get_all_stages():
    return load_cache()['stages']


def get_cache_time():
    return load_cache()['cache_time']


@lru_cache(1)
def get_all_materials():
    items = get_all_items()
    materials = list(filter(lambda x: x['itemType'] == 'MATERIAL', items))
    return sorted(materials, key=lambda k: k['rarity'], reverse=True)


@lru_cache(1)
def get_main_stage_map():
    stages = get_all_stages()
    main_stages = list(filter(lambda x: x['stageType'] == 'MAIN', stages))
    stage_map = {}
    for stage in main_stages:
        stage_map[stage['stageId']] = stage
    return stage_map


def get_plan(required, owned, extra_outc=False, exp_demand=False, gold_demand=True,
             input_lang='id', output_lang='id', server='CN'):
    url = 'https://planner.penguin-stats.io/plan'
    post_data = {
        'required': required,
        'owned': owned,
        'extra_outc': extra_outc,  # 考虑合成副产物
        'exp_demand': exp_demand,  # 大量需求经验
        'gold_demand': gold_demand,  # 大量需求龙门币
        'input_lang': input_lang,
        'output_lang': output_lang,
        'server': server
    }
    print(post_data)
    resp = requests.post(url, json=post_data)
    return resp.json()


if __name__ == '__main__':
    print(get_all_materials())
