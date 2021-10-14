import os
import time
from dataclasses import dataclass
import logging
from typing import Callable

import penguin_stats.reporter
import config
from util.excutil import guard

from Arknights.helper import AddonBase

logger = logging.getLogger(__name__)

@dataclass
class combat_session:
    state: Callable = None
    stop: bool = False
    operation_start: float = 0
    first_wait: bool = True
    mistaken_delegation: bool = False
    prepare_reco: dict = None

def item_name_guard(item):
    return str(item) if item is not None else '<无法识别的物品>'

def item_qty_guard(qty):
    return str(qty) if qty is not None else '?'

def format_recoresult(recoresult):
    result = None
    with guard(logger):
        result = '[%s] %s' % (recoresult['operation'],
            '; '.join('%s: %s' % (grpname, ', '.join('%sx%s' % (item_name_guard(itemtup[0]), item_qty_guard(itemtup[1]))
            for itemtup in grpcont))
            for grpname, grpcont in recoresult['items']))
    if result is None:
        result = '<发生错误>'
    return result

class CombatAddon(AddonBase):
    def on_attach(self):
        self.refill_with_item = config.get('behavior/refill_ap_with_item', False)
        self.refill_with_originium = config.get('behavior/refill_ap_with_originium', False)
        self.use_refill = self.refill_with_item or self.refill_with_originium
        self.loots = {}
        self.use_penguin_report = config.get('reporting/enabled', False)
        if self.use_penguin_report:
            self.penguin_reporter = penguin_stats.reporter.PenguinStatsReporter()
        self.refill_count = 0
        self.max_refill_count = None


    def module_battle_slim(self,
                           c_id=None,  # 待战斗的关卡编号
                           set_count=1000,  # 战斗次数
                           check_ai=True,  # 是否检查代理指挥
                           **kwargs):  # 扩展参数:
        '''
        :param sub 是否为子程序 (是否为module_battle所调用)
        :param auto_close 是否自动关闭, 默认为 false
        :param self_fix 是否尝试自动修复, 默认为 false
        :param MAX_TIME 最大检查轮数, 默认在 config 中设置,
            每隔一段时间进行一轮检查判断作战是否结束
            建议自定义该数值以便在出现一定失误,
            超出最大判断次数后有一定的自我修复能力
        :return:
            True 完成指定次数的作战
            False 理智不足, 退出作战
        '''
        logger.debug("helper.module_battle_slim")
        sub = kwargs["sub"] \
            if "sub" in kwargs else False
        auto_close = kwargs["auto_close"] \
            if "auto_close" in kwargs else False
        if set_count == 0:
            return c_id, 0
        self.operation_time = []
        count = 0
        remain = 0
        try:
            for _ in range(set_count):
                # logger.info("开始第 %d 次战斗", count + 1)
                self.operation_once_statemachine(c_id, )
                count += 1
                logger.info("第 %d 次作战完成", count)
                self.frontend.notify('completed-count', count)
                if count != set_count:
                    # 2019.10.06 更新逻辑后，提前点击后等待时间包括企鹅物流
                    if config.reporter:
                        self.delay(SMALL_WAIT, MANLIKE_FLAG=True, allow_skip=True)
                    else:
                        self.delay(BIG_WAIT, MANLIKE_FLAG=True, allow_skip=True)
        except StopIteration:
            # count: succeeded count
            logger.error('未能进行第 %d 次作战', count + 1)
            remain = set_count - count
            if remain > 1:
                logger.error('已忽略余下的 %d 次战斗', remain - 1)

        return c_id, remain


    def can_perform_refill(self):
        if not self.use_refill:
            return False
        if self.max_refill_count is not None:
            return self.refill_count < self.max_refill_count
        else:
            return True

    @dataclass
    class operation_once_state:
        state: Callable = None
        stop: bool = False
        operation_start: float = 0
        first_wait: bool = True
        mistaken_delegation: bool = False
        prepare_reco: dict = None

    def operation_once_statemachine(self, c_id):
        import imgreco.before_operation
        import imgreco.end_operation

        smobj = combat_session()
        def on_prepare(smobj):
            count_times = 0
            while True:
                screenshot = self.device.screenshot()
                recoresult = imgreco.before_operation.recognize(screenshot)
                if recoresult is not None:
                    logger.debug('当前画面关卡：%s', recoresult['operation'])
                    if c_id is not None:
                        # 如果传入了关卡 ID，检查识别结果
                        if recoresult['operation'] != c_id:
                            logger.error('不在关卡界面')
                            raise StopIteration()
                    break
                else:
                    count_times += 1
                    self.delay(1, False)
                    if count_times <= 7:
                        logger.warning('不在关卡界面')
                        self.delay(TINY_WAIT, False)
                        continue
                    else:
                        logger.error('{}次检测后都不再关卡界面，退出进程'.format(count_times))
                        raise StopIteration()

            self.CURRENT_STRENGTH = int(recoresult['AP'].split('/')[0])
            ap_text = '理智' if recoresult['consume_ap'] else '门票'
            logger.info('当前%s %d, 关卡消耗 %d', ap_text, self.CURRENT_STRENGTH, recoresult['consume'])
            if self.CURRENT_STRENGTH < int(recoresult['consume']):
                logger.error(ap_text + '不足 无法继续')
                if recoresult['consume_ap'] and self.can_perform_refill():
                    logger.info('尝试回复理智')
                    self.tap_rect(recoresult['start_button'])
                    self.delay(SMALL_WAIT)
                    screenshot = self.adb.screenshot()
                    refill_type = imgreco.before_operation.check_ap_refill_type(screenshot)
                    confirm_refill = False
                    if refill_type == 'item' and self.refill_with_item:
                        logger.info('使用道具回复理智')
                        confirm_refill = True
                    if refill_type == 'originium' and self.refill_with_originium:
                        logger.info('碎石回复理智')
                        confirm_refill = True
                    # FIXME: 道具回复量不足时也会尝试使用
                    if confirm_refill:
                        self.tap_rect(imgreco.before_operation.get_ap_refill_confirm_rect(self.viewport))
                        self.refill_count += 1
                        self.delay(MEDIUM_WAIT)
                        return  # to on_prepare state
                    logger.error('未能回复理智')
                    self.tap_rect(imgreco.before_operation.get_ap_refill_cancel_rect(self.viewport))
                raise StopIteration()

            if not recoresult['delegated']:
                logger.info('设置代理指挥')
                self.tap_rect(recoresult['delegate_button'])
                return  # to on_prepare state

            logger.info("理智充足 开始行动")
            self.tap_rect(recoresult['start_button'])
            smobj.prepare_reco = recoresult
            smobj.state = on_troop

        def on_troop(smobj):
            count_times = 0
            while True:
                self.delay(TINY_WAIT, False)
                screenshot = self.adb.screenshot()
                recoresult = imgreco.before_operation.check_confirm_troop_rect(screenshot)
                if recoresult:
                    logger.info('确认编队')
                    break
                else:
                    count_times += 1
                    if count_times <= 7:
                        logger.warning('等待确认编队')
                        continue
                    else:
                        logger.error('{} 次检测后不再确认编队界面'.format(count_times))
                        raise StopIteration()
            self.tap_rect(imgreco.before_operation.get_confirm_troop_rect(self.viewport))
            smobj.operation_start = time.monotonic()
            smobj.state = on_operation

        def on_operation(smobj):
            if smobj.first_wait:
                if len(self.operation_time) == 0:
                    wait_time = BATTLE_NONE_DETECT_TIME
                else:
                    wait_time = sum(self.operation_time) / len(self.operation_time) - 7
                logger.info('等待 %d s' % wait_time)
                self.delay(wait_time, MANLIKE_FLAG=False, allow_skip=True)
                smobj.first_wait = False
            t = time.monotonic() - smobj.operation_start

            logger.info('已进行 %.1f s，判断是否结束', t)
            screenshot = self.adb.screenshot()
            if imgreco.end_operation.check_level_up_popup(screenshot):
                logger.info("等级提升")
                self.operation_time.append(t)
                smobj.state = on_level_up_popup
                return

            end_flag = imgreco.end_operation.check_end_operation(smobj.prepare_reco['style'], not smobj.prepare_reco['no_friendship'], screenshot)
            if not end_flag and t > 300:
                if imgreco.end_operation.check_end_operation2(screenshot):
                    self.tap_rect(imgreco.end_operation.get_end2_rect(screenshot))
                    screenshot = self.adb.screenshot()
                    end_flag = imgreco.end_operation.check_end_operation_main(screenshot)
            if end_flag:
                logger.info('战斗结束')
                self.operation_time.append(t)
                crop = imgreco.end_operation.get_still_check_rect(self.viewport)
                if self.wait_for_still_image(crop=crop, timeout=15, raise_for_timeout=True):
                    smobj.state = on_end_operation
                return
            dlgtype, ocrresult = imgreco.common.recognize_dialog(screenshot)
            if dlgtype is not None:
                if dlgtype == 'yesno' and '代理指挥' in ocrresult:
                    logger.warning('代理指挥出现失误')
                    self.frontend.alert('代理指挥', '代理指挥出现失误', 'warn')
                    smobj.mistaken_delegation = True
                    if config.get('behavior/mistaken_delegation/settle', False):
                        logger.info('以 2 星结算关卡')
                        self.tap_rect(imgreco.common.get_dialog_right_button_rect(screenshot))
                        self.delay(2)
                        smobj.stop = True
                        return
                    else:
                        logger.info('放弃关卡')
                        self.tap_rect(imgreco.common.get_dialog_left_button_rect(screenshot))
                        # 关闭失败提示
                        self.wait_for_still_image()
                        self.tap_rect(imgreco.common.get_reward_popup_dismiss_rect(screenshot))
                        # FIXME: 理智返还
                        self.delay(1)
                        smobj.stop = True
                        return
                elif dlgtype == 'yesno' and '将会恢复' in ocrresult:
                    logger.info('发现放弃行动提示，关闭')
                    self.tap_rect(imgreco.common.get_dialog_left_button_rect(screenshot))
                else:
                    logger.error('未处理的对话框：[%s] %s', dlgtype, ocrresult)
                    raise RuntimeError('unhandled dialog')

            logger.info('战斗未结束')
            self.delay(BATTLE_FINISH_DETECT, allow_skip=True)

        def on_level_up_popup(smobj):
            self.delay(SMALL_WAIT, MANLIKE_FLAG=True)
            logger.info('关闭升级提示')
            self.tap_rect(imgreco.end_operation.get_dismiss_level_up_popup_rect(self.viewport))
            self.wait_for_still_image()
            smobj.state = on_end_operation

        def on_end_operation(smobj):
            screenshot = self.adb.screenshot()
            logger.info('离开结算画面')
            self.tap_rect(imgreco.end_operation.get_dismiss_end_operation_rect(self.viewport))
            reportresult = penguin_stats.reporter.ReportResult.NotReported
            try:
                # 掉落识别
                drops = imgreco.end_operation.recognize(smobj.prepare_reco['style'], screenshot, True)
                logger.debug('%s', repr(drops))
                logger.info('掉落识别结果：%s', format_recoresult(drops))
                log_total = len(self.loots)
                for _, group in drops['items']:
                    for name, qty, item_type in group:
                        if name is not None and qty is not None:
                            self.loots[name] = self.loots.get(name, 0) + qty
                self.frontend.notify("combat-result", drops)
                self.frontend.notify("loots", self.loots)
                if log_total:
                    self.log_total_loots()
                if self.use_penguin_report:
                    reportresult = self.penguin_reporter.report(drops)
                    if isinstance(reportresult, penguin_stats.reporter.ReportResult.Ok):
                        logger.debug('report hash = %s', reportresult.report_hash)
            except Exception as e:
                logger.error('', exc_info=True)
            if self.use_penguin_report and reportresult is penguin_stats.reporter.ReportResult.NotReported:
                filename = os.path.join(config.SCREEN_SHOOT_SAVE_PATH, '未上报掉落-%d.png' % time.time())
                with open(filename, 'wb') as f:
                    screenshot.save(f, format='PNG')
                logger.error('未上报掉落截图已保存到 %s', filename)
            smobj.stop = True

        smobj.state = on_prepare
        smobj.stop = False
        smobj.operation_start = 0

        while not smobj.stop:
            oldstate = smobj.state
            smobj.state(smobj)
            if smobj.state != oldstate:
                logger.debug('state changed to %s', smobj.state.__name__)

        if smobj.mistaken_delegation and config.get('behavior/mistaken_delegation/skip', True):
            raise StopIteration()

    def module_battle(self,  # 完整的战斗模块
                      c_id,  # 选择的关卡
                      set_count=1000):  # 作战次数
        logger.debug("helper.module_battle")
        c_id = c_id.upper()
        if stage_path.is_stage_supported_ocr(c_id):
            self.goto_stage_by_ocr(c_id)
        else:
            logger.error('不支持的关卡：%s', c_id)
            raise ValueError(c_id)
        return self.module_battle_slim(c_id,
                                set_count=set_count,
                                check_ai=True,
                                sub=True)

    def main_handler(self, task_list, clear_tasks=False, auto_close=True):
        if len(task_list) == 0:
            logger.fatal("任务清单为空!")

        for c_id, count in task_list:
            # if not stage_path.is_stage_supported(c_id):
            #     raise ValueError(c_id)
            logger.info("开始 %s", c_id)
            flag = self.module_battle(c_id, count)

        logger.info("任务清单执行完毕")

    def log_total_loots(self):
        logger.info('目前已获得：%s', ', '.join('%sx%d' % tup for tup in self.loots.items()))
