import time
import app
from Arknights.addons.contrib.common_cache import load_inventory, load_aog_data, load_game_data
from Arknights.addons.stage_navigator import StageNavigator, custom_stage
from automator import AddonBase
from penguin_stats import arkplanner
import logging


logger = logging.getLogger(__name__)


desc = f"""
{__file__}
==================================================================================================
长草时用的脚本, 检查库存中最少的蓝材料, 然后去 aog 上推荐的地图刷材料.
aog 地址: https://arkonegraph.herokuapp.com/

不想的刷的材料可以修改脚本中的 exclude_names.

cache_key 控制缓存的频率, 默认每周读取一次库存, 如果需要手动更新缓存, 
直接删除目录下的 aog_cache.json 和 inventory_items_cache.json 即可.

==================================================================================================
"""

# cache_key = '%Y-%m-%d'  # cache by day
cache_key = '%Y--%V'    # cache by week


aog_cache_file = app.cache_path.joinpath('aog_cache.json')
inventory_cache_file = app.cache_path.joinpath('inventory_items_cache.json')


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


def get_activities():
    return load_game_data('activity_table')['basicInfo']


def get_available_activities():
    activity_table = get_activities()
    cur_time = time.time()
    return [activity_table[aid] for aid in activity_table
            if activity_table[aid]['startTime'] < cur_time < activity_table[aid]['endTime']]


def get_available_activity_stages(force_update=False):
    available_activities = get_available_activities()
    if not available_activities:
        logger.info('No available activities.')
        return []
    zones_table = load_game_data('zone_table')['zones']
    zone_ids = [zid for zid in zones_table]
    available_zone_ids = []
    for activity in available_activities:
        aid = activity['id']
        for zid in zone_ids:
            if zid.startswith(f'{aid}_'):
                available_zone_ids.append(zid)
    if not available_zone_ids:
        logger.debug('No available activity zones.')
        return []
    stage_table = load_game_data('stage_table')['stages']
    available_stages = []
    for zid in available_zone_ids:
        for sid in stage_table:
            stage = stage_table[sid]
            if stage['zoneId'] == zid:
                available_stages.append(stage)
    available_stage_codes = [stage['code'] for stage in available_stages]
    if available_stage_codes:
        logger.info(f'Available activities: {[activity["name"] for activity in available_activities]}')
    logger.debug(f'Available stages: {available_stage_codes}')
    return available_stage_codes


def filter_items_with_activity(t3_items, available_activity_stages):
    filtered_t3_items = [item for item in t3_items if order_stage(item)['code'] in available_activity_stages]
    logger.info(f'Filtered t3 items: {[item["name"] for item in filtered_t3_items]}')
    return filtered_t3_items


def filter_latest_activity_t3_item_stage(my_items, available_activity_stages):
    from Arknights.addons.contrib.activity import get_stage_map, get_activity_info
    stage_code_map, zone_linear_map = get_stage_map()
    t3_items = load_aog_data()['tier']['t3']
    t3_ids = set([i['id'] for i in t3_items])
    item_stage_map = {}
    for stage_code in available_activity_stages:
        stage = stage_code_map.get(stage_code)
        if stage is None:
            continue
        rewards = stage['stageDropInfo'].get('displayDetailRewards')
        if not rewards:
            continue
        now = time.time() * 1000
        for reward in rewards:
            if reward["type"] == "MATERIAL" and reward["dropType"] == 2 and reward["id"] in t3_ids:
                item_stage = item_stage_map.get(reward["id"])
                stage['startTime'] = get_activity_info(stage['zoneId'])['startTime']
                if stage['startTime'] < now + 48 * 3600 * 1000:
                    continue
                if item_stage is None:
                    item_stage_map[reward['id']] = stage
                elif stage['startTime'] > item_stage['startTime']:
                    item_stage_map[reward['id']] = stage
    logger.debug(f'item_stage_map: {[(k, item_stage_map[k]["code"]) for k in item_stage_map]}')
    if item_stage_map:
        for my_item in my_items:
            if my_item['itemId'] in item_stage_map:
                return item_stage_map[my_item['itemId']]['code']


def get_stage(aog_items, my_items, prefer_activity=True):
    t3_items = aog_items['tier']['t3']
    normal_action = app.config.grass_on_aog.normal_action
    if prefer_activity:
        available_activity_stages = set(get_available_activity_stages())
        if not available_activity_stages:
            logger.debug('No available activity stage, skip filtering.')
            return get_stage_with_action(normal_action, my_items, t3_items)
        else:
            filtered_t3_items = filter_items_with_activity(t3_items, available_activity_stages)
            if filtered_t3_items:
                return get_stage_with_action('auto_t3', my_items, filtered_t3_items)
            else:
                logger.info('Refresh aog data.')
                t3_items = load_aog_data(True)['tier']['t3']
                filtered_t3_items = filter_items_with_activity(t3_items, available_activity_stages)
                if filtered_t3_items:
                    return get_stage_with_action('auto_t3', my_items, filtered_t3_items)
                else:
                    stage = filter_latest_activity_t3_item_stage(my_items, available_activity_stages)
                    if stage:
                        logger.info(f'没有在 aog 中找到活动关卡相关的材料, 尝试刷最近活动的 t3 材料关卡 [{stage}]')
                        return stage
                logger.info('没有在 aog 中找到活动关卡相关的材料, 这可能是因为 aog 数据还没有更新, 或者这次活动关卡的效率还不如普通关卡.')
                logger.info('可以试试在一段时间后删除 cache/aog_cache.json 以强制刷新 aog 数据缓存.')
                no_aog_data_action = app.config.grass_on_aog.no_aog_data_action
                logger.info(f'no_aog_data_action: {no_aog_data_action}.')
                return get_stage_with_action(no_aog_data_action, my_items, t3_items)
    return get_stage_with_action(normal_action, my_items, t3_items)


def get_stage_with_action(action, my_items, t3_items):
    if action == 'none' or action is None:
        logger.info('根据配置, 不执行任何操作.')
    elif action == 'auto_t3':
        for my_item in my_items:
            for t3_item in t3_items:
                if t3_item['name'] == my_item['name']:
                    logger.info('require item: %s, owned: %s' % (my_item['name'], my_item['count']))
                    return order_stage(t3_item)['code']
    else:
        logger.info(f'根据配置, 刷 [{action}].')
        return action


class GrassAddOn(AddonBase):
    @custom_stage('grass', ignore_count=True, title='一键长草', description='检查库存中最少的蓝材料, 然后去 aog 上推荐的地图刷材料')
    def run(self, *args):
        exclude_names = app.config.grass_on_aog.exclude
        self.logger.info('不刷以下材料: %r', exclude_names)
        self.logger.info('加载库存信息...')
        aog_cache = load_aog_data(cache_key=cache_key)

        my_items = load_inventory(self.helper, cache_key=cache_key)
        all_items = arkplanner.get_all_items()

        my_items_with_count = []
        for item in all_items:
            if item['itemType'] in ['MATERIAL'] and item['name'] not in exclude_names and item['rarity'] == 2 \
                    and len(item['itemId']) > 4:
                my_items_with_count.append({'name': item['name'],
                          'itemId': item['itemId'],
                          'count': my_items.get(item['itemId'], 0),
                          'rarity': item['rarity']})
        my_items_with_count = sorted(my_items_with_count, key=lambda x: x['count'])
        stage = get_stage(aog_cache, my_items_with_count, prefer_activity=app.config.grass_on_aog.prefer_activity_stage)
        if stage:
            return self.addon(StageNavigator).navigate_and_combat(stage, 1000)


__all__ = ['GrassAddOn']


if __name__ == '__main__':
    from Arknights.configure_launcher import helper
    helper.addon(GrassAddOn).run()
