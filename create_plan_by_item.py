from penguin_stats import arkplanner
import json
import math


if __name__ == '__main__':
    cache_time = arkplanner.get_cache_time()
    c = input('是否刷新企鹅物流缓存(缓存时间: %s)[y/N]:' % cache_time)
    if c.lower() == 'y':
        arkplanner.update_cache()
    materials = arkplanner.get_all_materials()
    material_index_map = {}
    material_id_map = {}
    print('材料列表：')
    for i in range(len(materials)):
        material_index_map[i] = materials[i]
        material_id_map[materials[i]['itemId']] = materials[i]
        print('序号: %s, 材料等级: %s, 名称: %s' % (i, materials[i]['rarity'], materials[i]['name']))
    required = {}
    while True:
        # s = '2/1'
        s = input('材料序号/需求数量(输入为空时结束):')
        if s.strip() == '':
            break
        a = s.strip().split('/')
        material = material_index_map[int(a[0])]
        required[material['itemId']] = int(a[1])
    # required = {'30125': 1}
    owned = {}
    c = input('是否获取当前库存材料数量(y,N):')
    if c.lower() == 'y':
        from Arknights.shell_next import _create_helper
        owned = _create_helper()[0].get_inventory_items()
    print('正在获取刷图计划...')
    plan = arkplanner.get_plan(required, owned)
    main_stage_map = arkplanner.get_main_stage_map()
    stage_task_list = []
    print(plan)
    print('刷图计划:')
    for stage in plan['stages']:
        stage_info = main_stage_map[stage['stage']]
        count = math.ceil(float(stage['count']))
        print('关卡 [%s] 次数 %s' % (stage_info['code'], count))
        stage_task_list.append({'stage': stage_info['code'], 'count': count})
    print('预计消耗理智:', plan['cost'])
    save_data = {
        'required': required,
        'owned': owned,
        'stages': stage_task_list
    }
    with open('config/plan.json', 'w') as f:
        json.dump(save_data, f, indent=4, sort_keys=True)
    print('刷图计划已保存至: config/plan.json')
