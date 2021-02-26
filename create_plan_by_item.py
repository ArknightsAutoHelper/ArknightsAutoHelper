from penguin_stats import arkplanner
import json


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
        s = input('材料序号/需求数量(输入 q 结束):')
        if s.strip() == 'q':
            break
        a = s.strip().split('/')
        required[a[0]] = int(a[1])
    # required = {'30125': 1}
    # todo 检查已有的数量
    owns = {}
    print('正在获取刷图计划...')
    plan = arkplanner.get_plan(required, owns)
    print('正在获取关卡信息...')
    main_stage_map = arkplanner.get_main_stage_map()
    stage_task_list = []
    print('刷图计划:')
    for stage in plan['stages']:
        stage_info = main_stage_map[stage['stage']]
        print('关卡 [%s] 次数 %s' % (stage_info['code'], stage['count']))
        stage_task_list.append({'stage': stage_info['code'], 'count': int(stage['count'])})
    print('预计消耗理智:', plan['cost'])
    save_data = {
        'required': required,
        'stages': stage_task_list
    }
    with open('config/plan.json', 'w') as f:
        json.dump(save_data, f, indent=4, sort_keys=True)
    print('刷图计划已保存至: config/plan.json')
