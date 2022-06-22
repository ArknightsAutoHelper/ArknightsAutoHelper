import json
import os
from datetime import datetime

import requests

import app
from automator import BaseAutomator

common_cache_config = {
    'character_table': {
        'type': 'net_json',
        'filename': 'character_table_cache.json',
        'url': 'https://gh.cirno.xyz/raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/character_table.json',
        'encoding': 'utf-8'
    },
}


def get_cache_path(cache_file_name):
    return app.cache_path.joinpath(cache_file_name)


common_cache_file = get_cache_path('common_cache.json')
inventory_cache_file = app.cache_path.joinpath('inventory_items_cache.json')


def update_net_cache(cache_file_name, url):
    filepath = get_cache_path(cache_file_name)
    resp = requests.get(url)
    with open(filepath, 'wb') as f:
        f.write(resp.content)


def load_bytes_cache(cache_file_name, url, force_update=False):
    filepath = get_cache_path(cache_file_name)
    if not os.path.exists(filepath) or force_update:
        update_net_cache(cache_file_name, url)
    with open(filepath, 'rb') as f:
        return f.read()


def load_net_json_cache(cache_file_name, url, encoding='utf-8', force_update=False):
    filepath = get_cache_path(cache_file_name)
    if not os.path.exists(filepath) or force_update:
        update_net_cache(cache_file_name, url)
    with open(filepath, 'r', encoding=encoding) as f:
        return json.load(f)


def load_common_cache(cache_name, force_update=False):
    info = common_cache_config.get(cache_name)
    if not info:
        raise RuntimeError(f'[{cache_name}] is not exists.')
    if info['type'] == 'net_json':
        return load_net_json_cache(info['filename'], info['url'], info.get('encoding', 'utf-8'), force_update)
    raise RuntimeError(f"Unknown type {info['type']}.")


def load_game_data(table_name, force_update=False):
    url = f'https://gh.cirno.xyz/raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/{table_name}.json'
    return load_net_json_cache(f'{table_name}_cache.json', url, 'utf-8', force_update)


def _check_is_need_to_force_update(cache_name: str, cache_time_key: str):
    from datetime import datetime
    current_time = datetime.now().strftime(cache_time_key)
    if not common_cache_file.exists():
        with open(common_cache_file, 'w') as f:
            json.dump({}, f)
    with open(common_cache_file, 'r') as f:
        common_cache = json.load(f)
        update_time = common_cache.get(cache_name, current_time)
    return current_time != update_time


def update_common_cache_by_cache_time_key(cache_name: str, cache_time_key: str):
    from datetime import datetime
    current_time = datetime.now().strftime(cache_time_key)
    with open(common_cache_file, 'r') as f:
        common_cache = json.load(f)
        common_cache[cache_name] = current_time
    with open(common_cache_file, 'w') as f:
        json.dump(common_cache, f)


def read_from_common_cache(cache_name: str):
    with open(common_cache_file, 'r') as f:
        common_cache = json.load(f)
        return common_cache.get(cache_name)


def save_to_common_cache(cache_name: str, cache_value):
    with open(common_cache_file, 'r') as f:
        common_cache = json.load(f)
        common_cache[cache_name] = cache_value
    with open(common_cache_file, 'w') as f:
        json.dump(common_cache, f)


def load_aog_data(force_update: bool = None, cache_key='%Y--%V'):
    if force_update is None:
        force_update = _check_is_need_to_force_update('aog_data', cache_key) \
                       or not get_cache_path('aog_cache.json').exists()
    url = 'https://arkonegraph.herokuapp.com/total/CN'
    data = load_net_json_cache('aog_cache.json', url, 'utf-8', force_update)
    if force_update:
        update_common_cache_by_cache_time_key('aog_data', cache_key)
    return data


def load_inventory(helper: BaseAutomator, force_update=False, cache_key='%Y--%V'):
    if os.path.exists(inventory_cache_file) and not force_update:
        with open(inventory_cache_file, 'r') as f:
            data = json.load(f)
            if data['cacheTime'] == datetime.now().strftime(cache_key):
                return data
    return update_inventory(helper)


def update_inventory(helper: BaseAutomator, cache_key='%Y--%V'):
    from Arknights.addons.inventory import InventoryAddon
    data = helper.addon(InventoryAddon).get_inventory_items(True, False)
    data['cacheTime'] = datetime.now().strftime(cache_key)
    with open(inventory_cache_file, 'w') as f:
        json.dump(data, f)
    return data
