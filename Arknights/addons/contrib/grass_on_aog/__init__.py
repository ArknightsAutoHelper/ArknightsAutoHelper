import app
from Arknights.addons.contrib.common_cache import load_inventory, load_aog_data
from Arknights.addons.stage_navigator import StageNavigator, custom_stage
from automator import AddonBase
from penguin_stats import arkplanner

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


class GrassAddOn(AddonBase):
    @custom_stage('grass', ignore_count=True, title='一键长草', description='检查库存中最少的蓝材料, 然后去 aog 上推荐的地图刷材料')
    def run(self, _):
        exclude_names = app.config.grass_on_aog.exclude
        self.logger.info('不刷以下材料: %r', exclude_names)
        self.logger.info('加载库存信息...')
        aog_cache = load_aog_data(cache_key=cache_key)

        my_items = load_inventory(self.helper, cache_key=cache_key)
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
        aog_items = aog_cache
        t3_items = aog_items['tier']['t3']
        stage = ''
        for t3_item in t3_items:
            if t3_item['name'] == l[0]['name']:
                # print(t3_item)
                stage_info = order_stage(t3_item)
                stage = stage_info['code']
                self.logger.info('aog stage: %s', stage)
                break
        self.addon(StageNavigator).navigate_and_combat(stage, 1000)


__all__ = ['GrassAddOn']


if __name__ == '__main__':
    from Arknights.configure_launcher import helper
    helper.addon(GrassAddOn).run()
