from __future__ import annotations
import logging
from dataclasses import dataclass
import app
from resources.event import EXTRA_KNOWN_ITEMS, event_preprocess
import requests
from requests_cache import CachedSession
from urllib.parse import urljoin
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from imgreco.end_operation import EndOperationResult
from .penguin_schemas import Item, Stage, SingleReportRequest, ArkDrop

logger = logging.getLogger('PenguinReporter')

REPORT_SOURCE = 'ArknightsAutoHelper'

API_BASE = {
    'global': 'https://penguin-stats.io/',
    'cn': 'https://penguin-stats.cn/',
}
def api_endpoint(path):
    return urljoin(API_BASE[app.config.combat.penguin_stats.endpoint], path)

def _check_in_bound(bound, num):
    result = bound['lower'] <= num <= bound['upper'] 
    if num in bound.get('exceptions', []):
        return False
    return result


class ReportResult:
    pass
@dataclass
class ReportResultOk(ReportResult):
    report_hash: str
ReportResult.Ok = ReportResultOk
ReportResult.NothingToReport = ReportResult()
ReportResult.NotReported =ReportResult()

class PenguinStatsReporter:
    GROUP_NAME_TO_TYPE_MAP = {
        '常规掉落': 'NORMAL_DROP',
        '特殊掉落': 'SPECIAL_DROP',
        '额外物资': 'EXTRA_DROP',
        '幸运掉落': 'FURNITURE',
    }

    def __init__(self):
        self.logged_in = False
        self.initialized = None
        self.noop = False
        self.stage_map: dict[str, Stage] = {}
        self.item_map: dict[str, Item] = {}
        self.item_name_map: dict[str, Item] = {}
        self.cache_client = CachedSession(backend='memory', cache_control=True)
        self.client = requests.session()

    
    def set_login_state_with_response(self, response: requests.Response):
        if userid := response.headers.get('X-Penguin-Set-Penguinid', None):
            self.logged_in = True
            self.client.headers['Authorization'] = f'PenguinID {userid}'
            logger.debug('set headers in session: %r', self.client.headers)
        return userid

    def try_login(self, userid):
        if self.logged_in:
            return True
        try:
            logger.info('登录企鹅数据，userID=%s', userid)
            resp = self.client.post(api_endpoint('/PenguinStats/api/v2/users'), data=str(userid))
            resp.raise_for_status()
        except: 
            logger.error('登录失败', exc_info=1)
            return False
        self.set_login_state_with_response(resp)
        return True

    def initialize(self):
        if self.initialized is not None:
            return self.initialized
        if app.version == 'UNKNOWN':
            logger.warn('无法获取程序版本，请通过 git clone 下载源代码')
            logger.warn('为避免产生统计偏差，已禁用汇报功能')
            self.noop = True
            self.initialized = False
            return True
        try:
            logger.info('载入企鹅数据资源...')
            self.update_penguin_data()
            self.initialized = True
        except:
            logger.error('载入企鹅数据资源出错', exc_info=True)
            self.initialized = False
        return self.initialized

    def set_penguin_data(self, stages: list[Stage], items: list[Item]):
        name_to_id_map = {}
        for s in stages:
            self.stage_map[s['code']] = s
        for i in items:
            self.item_map[i['itemId']] = i
            self.item_name_map[i['name']] = i
            name_to_id_map[i['name']] = i['itemId']
        import imgreco.itemdb
        unrecognized_items = set(self.item_map.keys()) - set(imgreco.itemdb.dnn_items_by_item_id.keys()) - set(EXTRA_KNOWN_ITEMS)
        extra_recognized_item_names = imgreco.itemdb.resources_known_items.keys()
        extra_recognized_item_ids = set(name_to_id_map.get(name, None) for name in extra_recognized_item_names)
        extra_recognized_item_ids.remove(None)
        unrecognized_items.difference_update(extra_recognized_item_ids)
        if unrecognized_items:
            logger.warn('企鹅数据中存在未识别的物品：%s', ', '.join(unrecognized_items))
            logger.warn('为避免产生统计偏差，已禁用汇报功能')
            self.noop = True

    def update_penguin_data(self):
        stages_resp = self.cache_client.get(api_endpoint('/PenguinStats/api/v2/stages'))
        items_resp = self.cache_client.get(api_endpoint('/PenguinStats/api/v2/items'))
        if self.initialized and stages_resp.from_cache and items_resp.from_cache:
            return
        stages: list[Stage] = stages_resp.json()
        items: list[Item] = items_resp.json()
        self.set_penguin_data(stages, items)

    def report(self, recoresult: EndOperationResult):
        if self.initialize() == False or self.noop:
            return ReportResult.NotReported
        logger.info('向企鹅数据汇报掉落')
        if recoresult.stars != (True, True, True):
            logger.info('不汇报非三星过关掉落')
            return ReportResult.NotReported
        if recoresult.low_confidence:
            logger.info('不汇报低置信度识别结果')
            return ReportResult.NotReported

        code = recoresult.operation

        self.update_penguin_data()
        if code not in self.stage_map:
            logger.info('企鹅数据无此关卡：%s', code)
            return ReportResult.NothingToReport
        stage = self.stage_map[code]

        if not stage.get('dropInfos'):
            logger.info('关卡 %s 目前无掉落信息，不进行汇报', code)
            return ReportResult.NothingToReport
        logger.debug('%r', stage['dropInfos'])
        if sum(1 for drop in stage['dropInfos'] if drop.get('itemId', None) != 'furni') == 0:
            logger.info('关卡 %s 目前无除家具外掉落，不进行汇报', code)
            return ReportResult.NothingToReport

        itemgroups = recoresult.items
        exclude_from_validation = []

        flattenitems = [(groupname, item) for groupname, items in itemgroups for item in items]

        try:
            flattenitems = list(event_preprocess(recoresult.operation, flattenitems, exclude_from_validation))
            report_special_item = app.config.combat.penguin_stats.report_special_item
            for item in flattenitems:
                if item[1].item_type == 'special_report_item' and not report_special_item:
                    logger.error('掉落中包含特殊汇报的物品, 请前往企鹅物流阅读相关说明, 符合条件后可以将配置中的 '
                                 'reporting/report_special_item 改为 true 汇报掉落')
                    raise RuntimeError('不汇报特殊物品.')
        except:
            logger.error('处理活动道具时出错', exc_info=True)
            return ReportResult.NotReported
        typeddrops: list[ArkDrop] = []
        dropinfos = stage['dropInfos']
        for itemdef in flattenitems:
            groupname, item = itemdef
            if groupname == '首次掉落':
                logger.info('不汇报首次掉落')
                return ReportResult.NotReported
            if '龙门币' in groupname:
                continue
            if groupname == '幸运掉落':
                typeddrops.append(ArkDrop(dropType='FURNITURE', itemId='furni', quantity=1))
                continue

            droptype = PenguinStatsReporter.GROUP_NAME_TO_TYPE_MAP.get(groupname, None)
            if droptype is None:
                logger.warning("不汇报包含 %s 分组的掉落数据", groupname)
                return ReportResult.NotReported

            if item.item_id in stage.get('recognitionOnly', []):
                logger.debug('不汇报识别结果中的物品（recognitionOnly）：%s', item.item_id)
                continue
            if item.item_type == 'special_report_item' and app.config.combat.penguin_stats.report_special_item:
                penguin_item = self.item_name_map.get(item.name, None)
            else:
                penguin_item = self.item_map.get(item.item_id, None)
            if penguin_item is None:
                logger.warning("%s 不在企鹅数据物品列表内", item.name)
                return ReportResult.NotReported
            itemid = penguin_item['itemId']
            if itemdef not in exclude_from_validation:
                filterresult = [x for x in dropinfos if x.get('itemId', None) == itemid and x['dropType'] == droptype]
                if filterresult:
                    dropinfo4item = filterresult[0]
                    if not _check_in_bound(dropinfo4item['bounds'], item.quantity):
                        logger.error('物品 %r 数量不符合企鹅数据验证规则', item)
                        return ReportResult.NotReported
                else:
                    logger.warning('物品 %s: %r 缺少验证规则', groupname, item)
            typeddrops.append(ArkDrop(dropType=droptype, itemId=itemid, quantity=item.quantity))

        for groupinfo in dropinfos:
             if groupinfo.get('itemId', None) is None:
                kinds = sum(1 for x in typeddrops if x['dropType'] == groupinfo['dropType'])
                if not _check_in_bound(groupinfo['bounds'], kinds):
                    logger.error('分组 %s 内物品种类数量（%d）不符合企鹅数据验证规则', groupinfo['dropType'], kinds)
                    return ReportResult.NotReported

        from imgreco.itemdb import model_timestamp

        req = SingleReportRequest(
            drops=typeddrops,
            server='CN',
            stageId=stage['stageId'],
            source=REPORT_SOURCE,
            version=f'{app.version},ark_material@{model_timestamp // 1000}',
        )

        logger.debug('raw request: %r', req)

        if not self.logged_in:
            uid = app.config.combat.penguin_stats.uid
            if uid is not None:
                self.try_login(uid)
        try:
            # use cookie stored in session
            resp = self.client.post(api_endpoint('/PenguinStats/api/v2/report'), json=req)
            resp.raise_for_status()
            if not self.logged_in:
                userid = self.set_login_state_with_response(resp)
                if userid is not None:
                    logger.info('企鹅数据用户 ID: %s', userid)
                    app.config.combat.penguin_stats.uid = userid
                    app.save()
                    logger.info('已写入配置文件')
            return ReportResult.Ok(resp.json().get('reportHash'))
        except:
            logger.error('汇报失败', exc_info=True)
        return ReportResult.NotReported
