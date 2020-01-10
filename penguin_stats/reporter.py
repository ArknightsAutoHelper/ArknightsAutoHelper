import logging

import config
from . import loader
from . import event

logger = logging.getLogger('PenguinReporter')

REPORT_SOURCE = 'ArknightsAutoHelper'


def _object_in(collection, obj):
    for x in collection:
        if obj is x:
            return True
    return False


def report(recoresult):
    if recoresult['stars'] != (True, True, True):
        logger.info('不汇报非三星过关掉落')
        return None
    if recoresult['low_confidence']:
        logger.info('不汇报低置信度识别结果')
        return None

    code = recoresult['operation']
    stage = loader.stages.get_by_code(code)
    if stage is None:
        logger.info('企鹅数据无此关卡：%s', code)
        return False

    flattenitems = {}
    groupcount = 0
    furncount = 0
    itemgroups = recoresult['items']
    exclude_from_validation = []
    flattenitems4validate = {}
    try:
        itemgroups = event.event_preprocess(recoresult['operation'], itemgroups, exclude_from_validation)
    except:
        logger.error('处理活动道具时出错', exc_info=True)
        return None

    for groupname, items in itemgroups:
        if groupname == '首次掉落':
            logger.info('不汇报首次掉落')
            return None
        if '声望&龙门币奖励' in groupname:
            continue
        groupcount += 1
        if groupname == '幸运掉落':
            furncount += 1
            continue
        for tup in items:
            name, qty = tup
            item = loader.items.get_by_name(name)
            if item is None:
                logger.warning("%s 不在企鹅数据物品列表内", name)
                return None
            itemid = item.id
            flattenitems[itemid] = flattenitems.get(itemid, 0) + qty
            if not _object_in(exclude_from_validation, tup):
                flattenitems4validate[itemid] = flattenitems4validate.get(itemid, 0) + qty

    validator = loader.constraints.get_validator_for_stage(stage)

    for itemid in flattenitems4validate:
        qty = flattenitems4validate[itemid]
        if not validator.validate_item_quantity(itemid, qty):
            logger.error('物品 %s 数量不符合企鹅数据验证规则', repr(loader.items.get_by_id(itemid)))
            return None

    if not validator.validate_group_count(groupcount):
        logger.error('物品分组数量不符合企鹅数据验证规则')
        return None

    jobj = {
        'stageId': stage.id,
        'drops': [{'itemId': x[0], 'quantity': x[1]} for x in flattenitems.items()],
        'furnitureNum': furncount,
        'source': REPORT_SOURCE,
        'version': config.version
    }

    uid = config.get('reporting/penguin_stats_uid', None)
    try:
        # use cookie stored in session
        resp = loader.session.post('https://penguin-stats.io/PenguinStats/api/report', json=jobj)
        resp.raise_for_status()
        report_id = resp.text
        if uid is None and 'userID' in resp.cookies:
            uid = resp.cookies.get('userID')
            logger.info('企鹅数据用户 ID: %s', uid)
            config.set('reporting/penguin_stats_uid', uid)
            config.save()
            logger.info('已写入配置文件')
        return report_id
    except:
        logger.error('汇报失败', exc_info=True)
    return None
