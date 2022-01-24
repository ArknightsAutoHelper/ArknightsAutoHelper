import logging
import json
from dataclasses import dataclass
from typing import Union
import config
from resources.event import EXTRA_KNOWN_ITEMS, event_preprocess
config.require_vendor_lib('penguin_client', 'penguin_client')
import penguin_client


logger = logging.getLogger('PenguinReporter')

REPORT_SOURCE = 'ArknightsAutoHelper'


def _object_in(collection, obj):
    for x in collection:
        if obj is x:
            return True
    return False

def _check_in_bound(bound, num):
    result = bound.lower <= num <= bound.upper 
    if bound.exceptions and num in bound.exceptions:
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
        self.client = penguin_client.ApiClient()
        self.stage_map = {}
        self.item_map = {}

    
    def set_login_state_with_last_response_cookie(self, response):
        setcookie = response.urllib3_response.headers['set-cookie']
        try:
            begin = setcookie.index('userID=')
            end = setcookie.index(';', begin)
            userid = setcookie[begin+7:end]
            self.client.cookie = 'userID=' + userid
            self.logged_in = True
            return userid
        except ValueError:
            return None

    def try_login(self, userid):
        if self.logged_in:
            return True
        acctapi = penguin_client.AccountApi(self.client)
        try:
            logger.info('登录企鹅数据，userID=%s', userid)
            jdoc = acctapi.login_using_post1(userid)
        except: 
            logger.error('登录失败', exc_info=1)
            return False
        self.set_login_state_with_last_response_cookie(self.client.last_response)
        return True

    def initialize(self):
        if self.initialized is not None:
            return self.initialized
        if config.version == 'UNKNOWN':
            logger.warn('无法获取程序版本，请通过 git clone 下载源代码')
            logger.warn('为避免产生统计偏差，已禁用汇报功能')
            self.noop = True
            self.initialized = False
            return True
        try:
            logger.info('载入企鹅数据资源...')
            stageapi = penguin_client.StageApi(self.client)
            itemsapi = penguin_client.ItemApi(self.client)
            stages = stageapi.get_all_stages_using_get1()
            items = itemsapi.get_all_items_using_get1()
            for s in stages:
                self.stage_map[s.code] = s
            for i in items:
                self.item_map[i.name] = i
            import imgreco.item
            _, _, idx2name, _ = imgreco.item.load_index_info()
            unrecognized_items = (set(self.item_map.keys())) - (set(imgreco.item.all_known_items())
                                                                | set(EXTRA_KNOWN_ITEMS) | set(idx2name))
            if unrecognized_items:
                logger.warn('企鹅数据中存在未识别的物品：%s', ', '.join(unrecognized_items))
                logger.warn('为避免产生统计偏差，已禁用汇报功能')
                self.noop = True
            self.initialized = True
        except:
            logger.error('载入企鹅数据资源出错', exc_info=True)
            self.initialized = False
        return self.initialized

    def report(self, recoresult):
        if self.initialize() == False or self.noop:
            return ReportResult.NotReported
        logger.info('向企鹅数据汇报掉落')
        if recoresult['stars'] != (True, True, True):
            logger.info('不汇报非三星过关掉落')
            return ReportResult.NotReported
        if recoresult['low_confidence']:
            logger.info('不汇报低置信度识别结果')
            return ReportResult.NotReported

        code = recoresult['operation']
        if code not in self.stage_map:
            logger.info('企鹅数据无此关卡：%s', code)
            return ReportResult.NothingToReport
        stage = self.stage_map[code]

        if stage.drop_infos is None:
            logger.info('关卡 %s 目前无掉落信息，不进行汇报', code)
            return ReportResult.NothingToReport
        if sum(1 for drop in stage.drop_infos if drop.item_id is not None and drop.item_id != 'furni') == 0:
            logger.info('关卡 %s 目前无除家具外掉落，不进行汇报', code)
            return ReportResult.NothingToReport

        itemgroups = recoresult['items']
        exclude_from_validation = []

        flattenitems = [(groupname, *item) for groupname, items in itemgroups for item in items]
        # [('常规掉落', '固源岩', 1, 'MATERIAL'), ...]

        try:
            flattenitems = list(event_preprocess(recoresult['operation'], flattenitems, exclude_from_validation))
            report_special_item = config.get('reporting/report_special_item', False)
            for item in flattenitems:
                if item[3] == 'special_report_item' and not report_special_item:
                    logger.error('掉落中包含特殊汇报的物品, 请前往企鹅物流阅读相关说明, 符合条件后可以将配置中的 '
                                 'reporting/report_special_item 改为 true 汇报掉落')
                    raise RuntimeError('不汇报特殊物品.')
        except:
            logger.error('处理活动道具时出错', exc_info=True)
            return ReportResult.NotReported
        typeddrops = []
        dropinfos = stage.drop_infos
        for itemdef in flattenitems:
            groupname, name, qty, item_type = itemdef
            if groupname == '首次掉落':
                logger.info('不汇报首次掉落')
                return ReportResult.NotReported
            if '声望&龙门币奖励' in groupname:
                continue
            if groupname == '幸运掉落':
                typeddrops.append(penguin_client.TypedDrop('FURNITURE', 'furni', 1))
                continue

            droptype = PenguinStatsReporter.GROUP_NAME_TO_TYPE_MAP.get(groupname, None)
            if droptype is None:
                logger.warning("不汇报包含 %s 分组的掉落数据", groupname)
                return ReportResult.NotReported

            item = self.item_map.get(name, None)
            if item is None:
                logger.warning("%s 不在企鹅数据物品列表内", name)
                return ReportResult.NotReported
            itemid = item.item_id
            if itemdef not in exclude_from_validation:
                filterresult = [x for x in dropinfos if x.item_id == itemid and x.drop_type == droptype]
                if filterresult:
                    dropinfo4item = filterresult[0]
                    if not _check_in_bound(dropinfo4item.bounds, qty):
                        logger.error('物品 %s（%s）数量（%d）不符合企鹅数据验证规则', name, itemid, qty)
                        return ReportResult.NotReported
                else:
                    logger.warning('物品 %s:%s（%s:%s）× %d 缺少验证规则', groupname, name, droptype, itemid, qty)
            typeddrops.append(penguin_client.TypedDrop(droptype, itemid, qty))

        for groupinfo in dropinfos:
             if groupinfo.item_id is None:
                kinds = sum(1 for x in typeddrops if x.drop_type == groupinfo.drop_type)
                if not _check_in_bound(groupinfo.bounds, kinds):
                    logger.error('分组 %s 内物品种类数量（%d）不符合企鹅数据验证规则', groupinfo.drop_type, kinds)
                    return ReportResult.NotReported

        req = penguin_client.SingleReportRequest(
            drops=typeddrops,
            server='CN',
            stage_id=stage.stage_id,
            source=REPORT_SOURCE,
            version=config.version
        )


        client = self.client
        if not self.logged_in:
            uid = config.get('reporting/penguin_stats_uid', None)
            if uid is not None:
                if not self.try_login(uid):
                    # use exclusive client instance to get response cookie
                    client = penguin_client.ApiClient()
        api = penguin_client.ReportApi(client)
        try:
            # use cookie stored in session
            resp = api.save_single_report_using_post1(req)
            if not self.logged_in:
                userid = self.set_login_state_with_last_response_cookie(client.last_response)
                if userid is not None:
                    logger.info('企鹅数据用户 ID: %s', userid)
                    config.set('reporting/penguin_stats_uid', userid)
                    config.save()
                    logger.info('已写入配置文件')
            return ReportResult.Ok(resp.report_hash)
        except:
            logger.error('汇报失败', exc_info=True)
        return ReportResult.NotReported
