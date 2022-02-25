import os
import json
import math

import app
from penguin_stats import arkplanner
from automator import AddonBase, cli_command
from ..stage_navigator import StageNavigator, custom_stage
from ..inventory import InventoryAddon

record_path = app.config_path.joinpath('record.json')

class PlannerAddOn(AddonBase):
    @cli_command('arkplanner')
    def cli_arkplanner(self, argv):
        """
        arkplanner
        输入材料需求创建刷图计划。使用 auto plan 命令执行刷图计划。
        """
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
            owned = self.addon(InventoryAddon).get_inventory_items()
        calc_mode = app.config.plan.calc_mode
        print('正在获取刷图计划...')
        if calc_mode == 'online':
            plan = arkplanner.get_plan(required, owned)
        elif calc_mode == 'local-aog':
            from penguin_stats.MaterialPlanning import MaterialPlanning
            mp = MaterialPlanning()
            plan = mp.get_plan(requirement_dct=required, deposited_dct=owned)
        else:
            raise RuntimeError(f'不支持的模式: {calc_mode}')
        stage_task_list = []
        print(plan)
        print('刷图计划:')
        for stage in plan['stages']:
            if calc_mode == 'online':
                stages = arkplanner.get_all_stages()
                stage_map = {s['stageId']: s for s in stages}
                stage_id = stage['stage']
                stage_id = stage_id[:-5] if stage_id.endswith('_perm') else stage_id
                stage_info = stage_map[stage_id]
                stage_code = stage_info['code']
            else:
                stage_info = stage
                stage_code = stage_info['stage']
            count = math.ceil(float(stage['count']))
            print('关卡 [%s] 次数 %s' % (stage_code, count))
            stage_task_list.append({'stage': stage_code, 'count': count})
        print('预计消耗理智:', plan['cost'])
        save_data = {
            'required': required,
            'owned': owned,
            'stages': stage_task_list
        }
        with open('config/plan.json', 'w') as f:
            json.dump(save_data, f, indent=4, sort_keys=True)
        print('刷图计划已保存至: config/plan.json')

    @custom_stage('plan', ignore_count=True, title='执行刷图计划', description='使用 arkplanner 命令创建刷图计划。执行过程会自动更新计划进度。')
    def run_plan(self, count):
        if not record_path.exists():
            self.logger.error('未能检测到刷图计划文件.')
            return
        with open(record_path, 'r') as f:
            plan = json.load(f)
        if plan['stages']:
            update_flag = False
            has_remain_sanity = True
            for task in plan['stages']:
                remain = task.get('remain', task['count'])
                if remain == 0:
                    continue
                self.logger.info('准备执行关卡 [%s], 计划次数: %s, 剩余次数: %s' % (task['stage'], task['count'], remain))
                update_flag = True
                c_id, remain = self.addon(StageNavigator).navigate_and_combat(task['stage'], remain)
                task['remain'] = remain
                if remain > 0:
                    self.logger.info('理智不足, 退出计划执行')
                    break
            if update_flag:
                with open(record_path, 'w') as f:
                    json.dump(plan, f, indent=4, sort_keys=True)
                print('刷图计划已更新至: config/plan.json')
        else:
            self.logger.error('未能检测到刷图计划')
