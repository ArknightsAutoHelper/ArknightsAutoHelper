from __future__ import annotations
from typing import Callable, Optional, overload
import os
import time
from dataclasses import dataclass

import penguin_stats.reporter
import app
from util.excutil import guard

from automator import AddonBase, cli_command
from Arknights.flags import *


@dataclass
class combat_session:
    state: Callable[['combat_session'], None] = None
    stop: bool = False
    operation_start: float = 0
    first_wait: bool = True
    mistaken_delegation: bool = False
    request_exit: bool = False
    prepare_reco: dict = None

def item_name_guard(item):
    return str(item) if item is not None else '<无法识别的物品>'

def item_qty_guard(qty):
    return str(qty) if qty is not None else '?'

def _parse_opt(argv):
    ops = []
    ops.append(lambda helper: helper.addon('CombatAddon').reset_refill())
    if len(argv) >= 2 and argv[1][:1] in ('+', '-'):
        opts = argv.pop(1)
        enable_refill = None
        for i, c in enumerate(opts):
            if c == '+':
                enable_refill = True
            elif c == '-':
                enable_refill = False
            elif c == 'r' and enable_refill is not None:
                def op(helper):
                    helper.addon('CombatAddon').use_refill = enable_refill
                    helper.addon('CombatAddon').refill_with_item = enable_refill
                ops.append(op)
            elif c == 'R' and enable_refill is not None:
                def op(helper):
                    helper.addon('CombatAddon').refill_with_originium = enable_refill
                ops.append(op)
            elif c in '0123456789' and enable_refill:
                num = int(opts[i:])
                def op(helper):
                    helper.addon('CombatAddon').max_refill_count = num
                ops.append(op)
                break
            else:
                raise ValueError('unrecognized token: %r in option %r' % (c, opts))
    return ops


class RefillConfigurationMixin:
    refill_type: str
    max_refill_count: int

    def __init_subclass__(cls) -> None:
        from app.schemadef import EnumField, IntField
        cls.refill_type = EnumField(['none', 'item', 'item+originium'], '自动回复体力', 'none：不回复\nitem：使用道具\nitem+originium：使用道具+源石')
        cls.refill_type.__set_name__(cls, 'refill_type')
        cls.max_refill_count = IntField(0, '最大回复次数', '0代表不限制\n自动选择多个应急理智小样(+10)算作一次', min=0)
        cls.max_refill_count.__set_name__(cls, 'max_refill_count')

class CombatAddon(AddonBase):
    def on_attach(self):
        self.operation_time = []
        self.reset_refill()
        self.loots = {}
        self.use_penguin_report = app.config.combat.penguin_stats.enabled
        if self.use_penguin_report:
            self.penguin_reporter = penguin_stats.reporter.PenguinStatsReporter()
        self.refill_count = 0
        self.max_refill_count = None

        # self.helper.register_gui_handler(self.gui_handler)

    def _configure_refill_with_values(self, with_item: Optional[bool] = None, with_originium: Optional[bool] = None, count: Optional[int] = None):
        if with_item is not None:
            self.refill_with_item = bool(with_item)
        if with_originium is not None:
            self.refill_with_originium = bool(with_originium)
        self.use_refill = self.refill_with_item or self.refill_with_originium
        if count is not None:
            self.max_refill_count = count
        return self

    def _configure_refill_with_schema(self, config: RefillConfigurationMixin):
        if config.refill_type == 'none':
            self._configure_refill_with_values(False, False)
        elif config.refill_type == 'item':
            self._configure_refill_with_values(True, False, count=config.max_refill_count)
        elif config.refill_type == 'item+originium':
            self._configure_refill_with_values(True, True, count=config.max_refill_count)
        else:
            raise ValueError('invalid refill_type: %r' % config.refill_type)

    @overload
    def configure_refill(self, with_item: Optional[bool] = None, with_originium: Optional[bool] = None, count: Optional[int] = None):
        ...
    
    @overload
    def configure_refill(self, config: RefillConfigurationMixin):
        ...
    
    def configure_refill(self, with_item = None, with_originium = None, count = None):
        if isinstance(with_item, RefillConfigurationMixin):
            self._configure_refill_with_schema(with_item)
        else:
            self._configure_refill_with_values(with_item, with_originium, count)

    def reset_refill(self):
        return self.configure_refill(False, False)

    def format_recoresult(self, recoresult):
        result = None
        with guard(self.logger):
            result = '[%s] %s' % (recoresult['operation'],
                '; '.join('%s: %s' % (grpname, ', '.join('%sx%s' % (item_name_guard(itemtup[0]), item_qty_guard(itemtup[1]))
                for itemtup in grpcont))
                for grpname, grpcont in recoresult['items']))
        if result is None:
            result = '<发生错误>'
        return result

    def combat_on_current_stage(self,
                           desired_count=1000,  # 战斗次数
                           c_id=None,  # 待战斗的关卡编号
                           **kwargs):  # 扩展参数:
        '''
        :param MAX_TIME 最大检查轮数, 默认在 config 中设置,
            每隔一段时间进行一轮检查判断作战是否结束
            建议自定义该数值以便在出现一定失误,
            超出最大判断次数后有一定的自我修复能力
        :return:
            True 完成指定次数的作战
            False 理智不足, 退出作战
        '''
        if desired_count == 0:
            return c_id, 0
        self.operation_time = []
        count = 0
        remain = 0
        try:
            for _ in range(desired_count):
                # self.logger.info("开始第 %d 次战斗", count + 1)
                self.operation_once_statemachine(c_id, )
                count += 1
                self.logger.info("第 %d 次作战完成", count)
                self.frontend.notify('completed-count', count)
                if count != desired_count:
                    # 2019.10.06 更新逻辑后，提前点击后等待时间包括企鹅物流
                    if app.config.combat.penguin_stats.enabled:
                        self.delay(SMALL_WAIT, MANLIKE_FLAG=True, allow_skip=True)
                    else:
                        self.delay(BIG_WAIT, MANLIKE_FLAG=True, allow_skip=True)
        except StopIteration:
            # count: succeeded count
            self.logger.error('未能进行第 %d 次作战', count + 1)
            remain = desired_count - count
            if remain > 1:
                self.logger.error('已忽略余下的 %d 次战斗', remain - 1)

        return c_id, remain


    def can_perform_refill(self):
        if not self.use_refill:
            return False
        if self.max_refill_count is not None:
            return self.refill_count < self.max_refill_count
        else:
            return True

    def operation_once_statemachine(self, c_id):
        import imgreco.before_operation

        smobj = combat_session()
        def on_prepare(smobj):
            count_times = 0
            while True:
                screenshot = self.device.screenshot()
                recoresult = imgreco.before_operation.recognize(screenshot)
                if recoresult is not None:
                    self.logger.debug('当前画面关卡：%s', recoresult['operation'])
                    if c_id is not None:
                        # 如果传入了关卡 ID，检查识别结果
                        if recoresult['operation'] != c_id:
                            self.logger.error('不在关卡界面')
                            raise StopIteration()
                    break
                else:
                    count_times += 1
                    self.delay(1, False)
                    if count_times <= 7:
                        self.logger.warning('不在关卡界面')
                        self.delay(TINY_WAIT, False)
                        continue
                    else:
                        self.logger.error('{}次检测后都不再关卡界面，退出进程'.format(count_times))
                        raise StopIteration()

            current_ap = int(recoresult['AP'].split('/')[0])
            ap_text = '理智' if recoresult['consume_ap'] else '门票'
            self.logger.info('当前%s %d, 关卡消耗 %d', ap_text, current_ap, recoresult['consume'])
            if current_ap < int(recoresult['consume']):
                self.logger.error(ap_text + '不足 无法继续')
                if recoresult['consume_ap'] and self.can_perform_refill():
                    self.logger.info('尝试回复理智')
                    self.tap_rect(recoresult['start_button'])
                    self.delay(SMALL_WAIT)
                    screenshot = self.device.screenshot()
                    refill_type = imgreco.before_operation.check_ap_refill_type(screenshot)
                    confirm_refill = False
                    if refill_type == 'item' and self.refill_with_item:
                        self.logger.info('使用道具回复理智')
                        confirm_refill = True
                    if refill_type == 'originium' and self.refill_with_originium:
                        self.logger.info('碎石回复理智')
                        confirm_refill = True
                    # FIXME: 道具回复量不足时也会尝试使用
                    if confirm_refill:
                        self.tap_rect(imgreco.before_operation.get_ap_refill_confirm_rect(self.viewport))
                        self.refill_count += 1
                        self.delay(MEDIUM_WAIT)
                        return  # to on_prepare state
                    self.logger.error('未能回复理智')
                    self.tap_rect(imgreco.before_operation.get_ap_refill_cancel_rect(self.viewport))
                raise StopIteration()

            if not recoresult['delegated']:
                self.logger.info('设置代理指挥')
                self.tap_rect(recoresult['delegate_button'])
                return  # to on_prepare state

            self.logger.info("理智充足 开始行动")
            self.tap_rect(recoresult['start_button'])
            smobj.prepare_reco = recoresult
            smobj.state = on_troop

        def on_troop(smobj):
            count_times = 0
            while True:
                self.delay(TINY_WAIT, False)
                screenshot = self.device.screenshot()
                recoresult = imgreco.before_operation.check_confirm_troop_rect(screenshot)
                if recoresult:
                    self.logger.info('确认编队')
                    break
                else:
                    count_times += 1
                    if count_times <= 7:
                        self.logger.warning('等待确认编队')
                        continue
                    else:
                        self.logger.error('{} 次检测后不再确认编队界面'.format(count_times))
                        raise StopIteration()
            self.tap_rect(imgreco.before_operation.get_confirm_troop_rect(self.viewport))
            smobj.operation_start = time.monotonic()
            smobj.state = on_operation

        def on_operation(smobj):
            import imgreco.end_operation
            import imgreco.common
            if smobj.first_wait:
                if len(self.operation_time) == 0:
                    wait_time = BATTLE_NONE_DETECT_TIME
                else:
                    wait_time = sum(self.operation_time) / len(self.operation_time) - 7
                self.logger.info('等待 %d s' % wait_time)
                smobj.first_wait = False
            else:
                wait_time = BATTLE_FINISH_DETECT

            t = time.monotonic() - smobj.operation_start


            if smobj.request_exit:
                self.delay(1, allow_skip=True)
            else:
                self.delay(wait_time, allow_skip=True)
                t = time.monotonic() - smobj.operation_start
                self.logger.info('已进行 %.1f s，判断是否结束', t)

            screenshot = self.device.screenshot()

            if self.match_roi('combat/topbar', method='ccoeff', screenshot=screenshot):
                if self.match_roi('combat/lun', method='ccoeff', screenshot=screenshot) and not smobj.mistaken_delegation:
                    self.logger.info('伦了。')
                    smobj.mistaken_delegation = True
                else:
                    return

            if self.match_roi('combat/topbar_camp', method='ccoeff', screenshot=screenshot):
                if self.match_roi('combat/lun_camp', method='ccoeff', screenshot=screenshot) and not smobj.mistaken_delegation:
                    self.logger.info('伦了。')
                    smobj.mistaken_delegation = True
                else:
                    return

            if smobj.mistaken_delegation and not app.config.combat.mistaken_delegation.settle:
                if not smobj.request_exit:
                    self.logger.info('退出关卡')
                    self.tap_rect(self.load_roi('combat/exit_button').bbox)
                    smobj.request_exit = True
                    return

            if self.match_roi('combat/failed', screenshot=screenshot):
                self.logger.info("行动失败")
                smobj.mistaken_delegation = True
                smobj.request_exit = True
                self.tap_rect((20*self.vw, 20*self.vh, 80*self.vw, 80*self.vh))
                return

            if self.match_roi('combat/ap_return', screenshot=screenshot):
                self.logger.info("确认理智返还")
                self.tap_rect((20*self.vw, 20*self.vh, 80*self.vw, 80*self.vh))
                return

            if imgreco.end_operation.check_level_up_popup(screenshot):
                self.logger.info("等级提升")
                self.operation_time.append(t)
                smobj.state = on_level_up_popup
                return

            end_flag = imgreco.end_operation.check_end_operation(smobj.prepare_reco['style'], not smobj.prepare_reco['no_friendship'], screenshot)
            if not end_flag and t > 300:
                if imgreco.end_operation.check_end_operation2(screenshot):
                    self.tap_rect(imgreco.end_operation.get_end2_rect(screenshot))
                    screenshot = self.device.screenshot()
                    end_flag = imgreco.end_operation.check_end_operation_legacy(screenshot)
            if end_flag:
                self.logger.info('战斗结束')
                self.operation_time.append(t)
                if self.wait_for_still_image(timeout=15, raise_for_timeout=True, check_delay=0.5, iteration=3):
                    smobj.state = on_end_operation
                return
            dlgtype, ocrresult = imgreco.common.recognize_dialog(screenshot)
            if dlgtype is not None:
                if dlgtype == 'yesno' and '代理指挥' in ocrresult:
                    self.logger.warning('代理指挥出现失误')
                    self.frontend.alert('代理指挥', '代理指挥出现失误', 'warn')
                    smobj.mistaken_delegation = True
                    if app.config.combat.mistaken_delegation.settle:
                        self.logger.info('以 2 星结算关卡')
                        self.tap_rect(imgreco.common.get_dialog_right_button_rect(screenshot))
                        self.delay(2)
                        smobj.stop = True
                        return
                    else:
                        self.logger.info('放弃关卡')
                        self.tap_rect(imgreco.common.get_dialog_left_button_rect(screenshot))
                        # 关闭失败提示
                        self.wait_for_still_image()
                        return
                elif dlgtype == 'yesno' and '将会恢复' in ocrresult:
                    if smobj.mistaken_delegation and not app.config.combat.mistaken_delegation.settle:
                        self.logger.info('确认退出关卡')
                        self.tap_rect(imgreco.common.get_dialog_right_button_rect(screenshot))
                    else:
                        self.logger.info('发现放弃行动提示，关闭')
                        self.tap_rect(imgreco.common.get_dialog_left_button_rect(screenshot))
                    return
                else:
                    self.logger.error('未处理的对话框：[%s] %s', dlgtype, ocrresult)
                    raise RuntimeError('unhandled dialog')

            self.logger.info('战斗未结束')

        def on_level_up_popup(smobj):
            import imgreco.end_operation
            self.delay(SMALL_WAIT, MANLIKE_FLAG=True)
            self.logger.info('关闭升级提示')
            self.tap_rect(imgreco.end_operation.get_dismiss_level_up_popup_rect(self.viewport))
            self.wait_for_still_image()
            smobj.state = on_end_operation

        def on_end_operation(smobj):
            import imgreco.end_operation
            screenshot = self.device.screenshot()
            reportresult = penguin_stats.reporter.ReportResult.NotReported
            try:
                # 掉落识别
                drops = imgreco.end_operation.recognize(smobj.prepare_reco['style'], screenshot, True)
                self.logger.debug('%s', repr(drops))
                self.logger.info('掉落识别结果：%s', self.format_recoresult(drops))
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
                        self.logger.debug('report hash = %s', reportresult.report_hash)
            except Exception as e:
                self.logger.error('', exc_info=True)
            if self.use_penguin_report and reportresult is penguin_stats.reporter.ReportResult.NotReported:
                filename = app.screenshot_path / ('未上报掉落-%d.png' % time.time())
                with open(filename, 'wb') as f:
                    screenshot.save(f, format='PNG')
                self.logger.error('未上报掉落截图已保存到 %s', filename)
            self.logger.info('离开结算画面')
            self.tap_rect(imgreco.end_operation.get_dismiss_end_operation_rect(self.viewport))
            smobj.stop = True

        smobj.state = on_prepare
        smobj.stop = False
        smobj.operation_start = 0

        while not smobj.stop:
            oldstate = smobj.state
            smobj.state(smobj)
            if smobj.state != oldstate:
                self.logger.debug('state changed to %s', smobj.state.__name__)

        if smobj.mistaken_delegation and app.config.combat.mistaken_delegation.skip:
            raise StopIteration()

    def log_total_loots(self):
        self.logger.info('目前已获得：%s', ', '.join('%sx%d' % tup for tup in self.loots.items()))

    @cli_command('quick')
    def cli_quick(self, argv):
        """
        quick [+-rR[N]] [n]
        重复挑战当前画面关卡特定次数或直到理智不足
        +r/-r 是否自动回复理智，最多回复 N 次
        +R/-R 是否使用源石回复理智（需要同时开启 +r）
        """

        ops = _parse_opt(argv)
        if len(argv) == 2:
            count = int(argv[1])
        else:
            count = 114514
        for op in ops:
            op(self)
        with self.helper.frontend.context:
            self.combat_on_current_stage(count)
        return 0


