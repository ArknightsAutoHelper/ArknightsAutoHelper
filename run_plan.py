from Arknights.helper import ArknightsHelper, logger
import config
import json
import os


if __name__ == '__main__':
    if not os.path.exists('config/plan.json'):
        logger.error('未能检测到刷图计划文件.')
        exit(-1)
    with open('config/plan.json', 'r') as f:
        plan = json.load(f)
    helper = ArknightsHelper()
    if plan['stages']:
        update_flag = False
        has_remain_sanity = True
        for task in plan['stages']:
            remain = task.get('remain', task['count'])
            if remain == 0:
                continue
            logger.info('准备执行关卡 [%s], 计划次数: %s, 剩余次数: %s' % (task['stage'], task['count'], remain))
            update_flag = True
            c_id, remain = helper.module_battle(task['stage'], remain)
            task['remain'] = remain
            if remain > 0:
                logger.info('理智不足, 退出计划执行')
                has_remain_sanity = False
                break
        if update_flag:
            with open('config/plan.json', 'w') as f:
                json.dump(plan, f, indent=4, sort_keys=True)
            print('刷图计划已更新至: config/plan.json')
        if has_remain_sanity and config.get('plan/idle_stage', None) is not None:
            # todo recheck
            idle_stage = config.get('plan/idle_stage')
            logger.info('刷图计划已执行完毕, 理智还有剩余, 执行 idle stage [%s]' % idle_stage)
            helper.refill_with_item = config.get('plan/refill_ap_with_item', False)
            helper.refill_with_originium = config.get('plan/refill_ap_with_originium', False)
            helper.module_battle(idle_stage, 1000)
    else:
        logger.error('未能检测到刷图计划')
