import penguin_client
from functools import lru_cache
import requests

item_api = penguin_client.ItemApi()
stage_api = penguin_client.StageApi()


@lru_cache(1)
def get_all_materials():
    items = item_api.get_all_items_using_get1()
    materials = list(filter(lambda x: x.item_type == 'MATERIAL', items))
    return sorted(materials, key=lambda k: k.rarity, reverse=True)


@lru_cache(1)
def get_main_stage_map():
    stages = stage_api.get_all_stages_using_get1()
    main_stages = list(filter(lambda x: x.stage_type == 'MAIN', stages))
    stage_map = {}
    for stage in main_stages:
        stage_map[stage.stage_id] = stage
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
    resp = requests.post(url, json=post_data)
    return resp.json()


if __name__ == '__main__':
    print(get_all_materials())
