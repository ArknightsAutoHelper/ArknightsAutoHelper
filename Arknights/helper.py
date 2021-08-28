import os
import json
import re
import time
import logging
from typing import Callable
from dataclasses import dataclass
from random import randint, uniform, gauss
from time import sleep, monotonic
from fractions import Fraction

import coloredlogs
import numpy as np

import config
import imgreco.common
import imgreco.main
import imgreco.task
import imgreco.map
import imgreco.imgops
import penguin_stats.reporter
from connector import auto_connect
from connector.ADBConnector import ADBConnector, ensure_adb_alive
from . import stage_path
from .frontend import DummyFrontend
from Arknights.click_location import *
from Arknights.flags import *
from util.excutil import guard

from Arknights import frontend

logger = logging.getLogger('helper')
coloredlogs.install(
    fmt=' Ξ %(message)s',
    #fmt=' %(asctime)s ! %(funcName)s @ %(filename)s:%(lineno)d ! %(levelname)s # %(message)s',
    datefmt='%H:%M:%S',
    level_styles={'warning': {'color': 'green'}, 'error': {'color': 'red'}},
    level='INFO')


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


class ArknightsHelper(object):
    def __init__(self, adb_host=None, device_connector=None, frontend=None):  # 当前绑定到的设备
        self.adb = None
        if adb_host is not None or device_connector is not None:
            self.connect_device(device_connector, adb_serial=adb_host)
        if frontend is None:
            frontend = DummyFrontend()
            if self.adb is None:
                self.connect_device(auto_connect())
        self.frontend = frontend
        self.frontend.attach(self)
        self.operation_time = []
        if DEBUG_LEVEL >= 1:
            self.__print_info()
        self.refill_with_item = config.get('behavior/refill_ap_with_item', False)
        self.refill_with_originium = config.get('behavior/refill_ap_with_originium', False)
        self.use_refill = self.refill_with_item or self.refill_with_originium
        self.loots = {}
        self.use_penguin_report = config.get('reporting/enabled', False)
        if self.use_penguin_report:
            self.penguin_reporter = penguin_stats.reporter.PenguinStatsReporter()
        self.refill_count = 0
        self.max_refill_count = None

        logger.debug("成功初始化模块")

    def ensure_device_connection(self):
        if self.adb is None:
            raise RuntimeError('not connected to device')

    def connect_device(self, connector=None, *, adb_serial=None):
        if connector is not None:
            self.adb = connector
        elif adb_serial is not None:
            self.adb = ADBConnector(adb_serial)
        else:
            self.adb = None
            return
        self.viewport = self.adb.screen_size
        if self.adb.screenshot_rotate %180:
            self.viewport = (self.viewport[1], self.viewport[0])
        if self.viewport[1] < 720 or Fraction(self.viewport[0], self.viewport[1]) < Fraction(16, 9):
            title = '设备当前分辨率（%dx%d）不符合要求' % (self.viewport[0], self.viewport[1])
            body = '需要宽高比等于或大于 16∶9，且渲染高度不小于 720。'
            details = None
            if Fraction(self.viewport[1], self.viewport[0]) >= Fraction(16, 9):
                body = '屏幕截图可能需要旋转，请尝试在 device-config 中指定旋转角度。'
                img = self.adb.screenshot()
                imgfile = os.path.join(config.SCREEN_SHOOT_SAVE_PATH, 'orientation-diagnose-%s.png' % time.strftime("%Y%m%d-%H%M%S"))
                img.save(imgfile)
                import json
                details = '参考 %s 以更正 device-config.json[%s]["screenshot_rotate"]' % (imgfile, json.dumps(self.adb.config_key))
            for msg in [title, body, details]:
                if msg is not None:
                    logger.warn(msg)
            frontend.alert(title, body, 'warn', details)

    def __print_info(self):
        logger.info('当前系统信息:')
        logger.info('分辨率:\t%dx%d', *self.viewport)
        # logger.info('OCR 引擎:\t%s', ocr.engine.info)
        logger.info('截图路径:\t%s', config.SCREEN_SHOOT_SAVE_PATH)

        if config.enable_baidu_api:
            logger.info('%s',
                        """百度API配置信息:
        APP_ID\t{app_id}
        API_KEY\t{api_key}
        SECRET_KEY\t{secret_key}
                        """.format(
                            app_id=config.APP_ID, api_key=config.API_KEY, secret_key=config.SECRET_KEY
                        )
                        )

    def __del(self):
        self.adb.run_device_cmd("am force-stop {}".format(config.ArkNights_PACKAGE_NAME))

    def destroy(self):
        self.__del()

    def check_game_active(self):  # 启动游戏 需要手动调用
        logger.debug("helper.check_game_active")
        current = self.adb.run_device_cmd('dumpsys window windows | grep mCurrentFocus').decode(errors='ignore')
        logger.debug("正在尝试启动游戏")
        logger.debug(current)
        if config.ArkNights_PACKAGE_NAME in current:
            logger.debug("游戏已启动")
        else:
            self.adb.run_device_cmd(
                "am start -n {}/{}".format(config.ArkNights_PACKAGE_NAME, config.ArkNights_ACTIVITY_NAME))
            logger.debug("成功启动游戏")

    def __wait(self, n=10,  # 等待时间中值
               MANLIKE_FLAG=True, allow_skip=False):  # 是否在此基础上设偏移量
        if MANLIKE_FLAG:
            m = uniform(0, 0.3)
            n = uniform(n - m * 0.5 * n, n + m * n)
        self.frontend.delay(n, allow_skip)

    def mouse_click(self,  # 点击一个按钮
                    XY):  # 待点击的按钮的左上和右下坐标
        assert (self.viewport == (1280, 720))
        logger.debug("helper.mouse_click")
        xx = randint(XY[0][0], XY[1][0])
        yy = randint(XY[0][1], XY[1][1])
        logger.info("接收到点击坐标并传递xx:{}和yy:{}".format(xx, yy))
        self.adb.touch_tap((xx, yy))
        self.__wait(TINY_WAIT, MANLIKE_FLAG=True)

    def tap_rect(self, rc):
        hwidth = (rc[2] - rc[0]) / 2
        hheight = (rc[3] - rc[1]) / 2
        midx = rc[0] + hwidth
        midy = rc[1] + hheight
        xdiff = max(-1, min(1, gauss(0, 0.2)))
        ydiff = max(-1, min(1, gauss(0, 0.2)))
        tapx = int(midx + xdiff * hwidth)
        tapy = int(midy + ydiff * hheight)
        self.adb.touch_tap((tapx, tapy))
        self.__wait(TINY_WAIT, MANLIKE_FLAG=True)

    def tap_quadrilateral(self, pts):
        pts = np.asarray(pts)
        acdiff = max(0, min(2, gauss(1, 0.2)))
        bddiff = max(0, min(2, gauss(1, 0.2)))
        halfac = (pts[2] - pts[0]) / 2
        m = pts[0] + halfac * acdiff
        pt2 = pts[1] if bddiff > 1 else pts[3]
        halfvec = (pt2 - m) / 2
        finalpt = m + halfvec * bddiff
        self.adb.touch_tap(tuple(int(x) for x in finalpt))
        self.__wait(TINY_WAIT, MANLIKE_FLAG=True)

    def wait_for_still_image(self, threshold=16, crop=None, timeout=60, raise_for_timeout=True, check_delay=1):
        if crop is None:
            shooter = lambda: self.adb.screenshot(False)
        else:
            shooter = lambda: self.adb.screenshot(False).crop(crop)
        screenshot = shooter()
        t0 = time.monotonic()
        ts = t0 + timeout
        n = 0
        minerr = 65025
        message_shown = False
        while (t1 := time.monotonic()) < ts:
            if check_delay > 0:
                self.__wait(check_delay, False, True)
            screenshot2 = shooter()
            mse = imgreco.imgops.compare_mse(screenshot, screenshot2)
            if mse <= threshold:
                return screenshot2
            screenshot = screenshot2
            if mse < minerr:
                minerr = mse
            if not message_shown and t1-t0 > 10:
                logger.info("等待画面静止")
        if raise_for_timeout:
            raise RuntimeError("%d 秒内画面未静止，最小误差=%d，阈值=%d" % (timeout, minerr, threshold))
        return None

    def module_login(self):
        logger.debug("helper.module_login")
        logger.info("发送坐标LOGIN_QUICK_LOGIN: {}".format(CLICK_LOCATION['LOGIN_QUICK_LOGIN']))
        self.mouse_click(CLICK_LOCATION['LOGIN_QUICK_LOGIN'])
        self.__wait(BIG_WAIT)
        logger.info("发送坐标LOGIN_START_WAKEUP: {}".format(CLICK_LOCATION['LOGIN_START_WAKEUP']))
        self.mouse_click(CLICK_LOCATION['LOGIN_START_WAKEUP'])
        self.__wait(BIG_WAIT)

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
                        self.__wait(SMALL_WAIT, MANLIKE_FLAG=True, allow_skip=True)
                    else:
                        self.__wait(BIG_WAIT, MANLIKE_FLAG=True, allow_skip=True)
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

        smobj = ArknightsHelper.operation_once_state()
        def on_prepare(smobj):
            count_times = 0
            while True:
                screenshot = self.adb.screenshot()
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
                    self.__wait(1, False)
                    if count_times <= 7:
                        logger.warning('不在关卡界面')
                        self.__wait(TINY_WAIT, False)
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
                    self.__wait(SMALL_WAIT)
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
                        self.__wait(MEDIUM_WAIT)
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
                self.__wait(TINY_WAIT, False)
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
            smobj.operation_start = monotonic()
            smobj.state = on_operation

        def on_operation(smobj):
            if smobj.first_wait:
                if len(self.operation_time) == 0:
                    wait_time = BATTLE_NONE_DETECT_TIME
                else:
                    wait_time = sum(self.operation_time) / len(self.operation_time) - 7
                logger.info('等待 %d s' % wait_time)
                self.__wait(wait_time, MANLIKE_FLAG=False, allow_skip=True)
                smobj.first_wait = False
            t = monotonic() - smobj.operation_start

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
                        self.__wait(2)
                        smobj.stop = True
                        return
                    else:
                        logger.info('放弃关卡')
                        self.tap_rect(imgreco.common.get_dialog_left_button_rect(screenshot))
                        # 关闭失败提示
                        self.wait_for_still_image()
                        self.tap_rect(imgreco.common.get_reward_popup_dismiss_rect(screenshot))
                        # FIXME: 理智返还
                        self.__wait(1)
                        smobj.stop = True
                        return
                elif dlgtype == 'yesno' and '将会恢复' in ocrresult:
                    logger.info('发现放弃行动提示，关闭')
                    self.tap_rect(imgreco.common.get_dialog_left_button_rect(screenshot))
                else:
                    logger.error('未处理的对话框：[%s] %s', dlgtype, ocrresult)
                    raise RuntimeError('unhandled dialog')

            logger.info('战斗未结束')
            self.__wait(BATTLE_FINISH_DETECT, allow_skip=True)

        def on_level_up_popup(smobj):
            self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
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


    def back_to_main(self):  # 回到主页
        logger.info("正在返回主页")
        retry_count = 0
        max_retry = 3
        while True:
            screenshot = self.adb.screenshot()

            if imgreco.main.check_main(screenshot):
                break

            # 检查是否有返回按钮
            if imgreco.common.check_nav_button(screenshot):
                logger.info('发现返回按钮，点击返回')
                self.tap_rect(imgreco.common.get_nav_button_back_rect(self.viewport))
                self.__wait(SMALL_WAIT)
                # 点击返回按钮之后重新检查
                continue

            if imgreco.common.check_get_item_popup(screenshot):
                logger.info('当前为获得物资画面，关闭')
                self.tap_rect(imgreco.common.get_reward_popup_dismiss_rect(self.viewport))
                self.__wait(SMALL_WAIT)
                continue

            # 检查是否在设置画面
            if imgreco.common.check_setting_scene(screenshot):
                logger.info("当前为设置/邮件画面，返回")
                self.tap_rect(imgreco.common.get_setting_back_rect(self.viewport))
                self.__wait(SMALL_WAIT)
                continue

            # 检测是否有关闭按钮
            rect, confidence = imgreco.common.find_close_button(screenshot)
            if confidence > 0.9:
                logger.info("发现关闭按钮")
                self.tap_rect(rect)
                self.__wait(SMALL_WAIT)
                continue

            dlgtype, ocr = imgreco.common.recognize_dialog(screenshot)
            if dlgtype == 'yesno':
                if '基建' in ocr or '停止招募' in ocr or '好友列表' in ocr:
                    self.tap_rect(imgreco.common.get_dialog_right_button_rect(screenshot))
                    self.__wait(3)
                    continue
                elif '招募干员' in ocr or '加急' in ocr:
                    self.tap_rect(imgreco.common.get_dialog_left_button_rect(screenshot))
                    self.__wait(3)
                    continue
                else:
                    raise RuntimeError('未适配的对话框')
            elif dlgtype == 'ok':
                self.tap_rect(imgreco.common.get_dialog_ok_button_rect(screenshot))
                self.__wait(1)
                continue
            retry_count += 1
            if retry_count > max_retry:
                raise RuntimeError('未知画面')
            logger.info('未知画面，尝试重新识别 {}/{} 次'.format(retry_count, max_retry))
            self.__wait(3)
        logger.info("已回到主页")

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

    def clear_task(self):
        logger.debug("helper.clear_task")
        logger.info("领取每日任务")
        self.back_to_main()
        screenshot = self.adb.screenshot()
        logger.info('进入任务界面')
        self.tap_quadrilateral(imgreco.main.get_task_corners(screenshot))
        self.__wait(SMALL_WAIT)
        screenshot = self.adb.screenshot()

        hasbeginner = imgreco.task.check_beginners_task(screenshot)
        if hasbeginner:
            logger.info('发现见习任务，切换到每日任务')
            self.tap_rect(imgreco.task.get_daily_task_rect(screenshot, hasbeginner))
            self.__wait(TINY_WAIT)
            screenshot = self.adb.screenshot()
        self.clear_task_worker()
        logger.info('切换到每周任务') #默认进入见习任务或每日任务，因此无需检测，直接切换即可
        self.tap_rect(imgreco.task.get_weekly_task_rect(screenshot, hasbeginner))
        self.clear_task_worker()

    def clear_task_worker(self):
        screenshot = self.adb.screenshot()
        kickoff = True
        while True:
            if imgreco.common.check_nav_button(screenshot) and not imgreco.task.check_collectable_reward(screenshot):
                logger.info("奖励已领取完毕")
                break
            if kickoff:
                logger.info('开始领取奖励')
                kickoff = False
            self.tap_rect(imgreco.task.get_collect_reward_button_rect(self.viewport))
            screenshot = self.adb.screenshot(cached=False)

    def recruit(self):
        import imgreco.recruit
        from . import recruit_calc
        logger.info('识别招募标签')
        tags = imgreco.recruit.get_recruit_tags(self.adb.screenshot())
        logger.info('可选标签：%s', ' '.join(tags))
        result = recruit_calc.calculate(tags)
        logger.debug('计算结果：%s', repr(result))
        return result


    def find_and_tap(self, partition, target):
        lastpos = None
        while True:
            screenshot = self.adb.screenshot()
            recoresult = imgreco.map.recognize_map(screenshot, partition)
            if recoresult is None:
                # TODO: retry
                logger.error('未能定位关卡地图')
                raise RuntimeError('recognition failed')
            if target in recoresult:
                pos = recoresult[target]
                logger.info('目标 %s 坐标: %s', target, pos)
                if lastpos is not None and tuple(pos) == tuple(lastpos):
                    logger.error('拖动后坐标未改变')
                    raise RuntimeError('拖动后坐标未改变')
                if 0 < pos[0] < self.viewport[0]:
                    logger.info('目标在可视区域内，点击')
                    self.adb.touch_tap(pos, offsets=(5, 5))
                    self.__wait(3)
                    break
                else:
                    lastpos = pos
                    originX = self.viewport[0] // 2 + randint(-100, 100)
                    originY = self.viewport[1] // 2 + randint(-100, 100)
                    if pos[0] < 0:  # target in left of viewport
                        logger.info('目标在可视区域左侧，向右拖动')
                        # swipe right
                        diff = -pos[0]
                        if abs(diff) < 100:
                            diff = 120
                        diff = min(diff, self.viewport[0] - originX)
                    elif pos[0] > self.viewport[0]:  # target in right of viewport
                        logger.info('目标在可视区域右侧，向左拖动')
                        # swipe left
                        diff = self.viewport[0] - pos[0]
                        if abs(diff) < 100:
                            diff = -120
                        diff = max(diff, -originX)
                    self.adb.touch_swipe2((originX, originY), (diff * 0.7 * uniform(0.8, 1.2), 0), max(250, diff / 2))
                    self.__wait(5)
                    continue

            else:
                raise KeyError((target, partition))

    def find_and_tap_episode_by_ocr(self, target):
        import imgreco.stage_ocr
        from resources.imgreco.map_vectors import ep2region, region2ep
        target_region = ep2region.get(target)
        if target_region is None:
            logger.error(f'未能定位章节区域, target: {target}')
            raise RuntimeError('recognition failed')
        vw, vh = imgreco.util.get_vwvh(self.viewport)
        episode_tag_rect = tuple(map(int, (35.185*vh, 39.259*vh, 50.093*vh, 43.056*vh)))
        next_ep_region_rect = (5.833*vh, 69.167*vh, 11.944*vh, 74.815*vh)
        prev_ep_region_rect = (5.833*vh, 15.370*vh, 11.944*vh, 21.481*vh)
        current_ep_rect = (50*vw+19.907*vh, 28.426*vh, 50*vw+63.426*vh, 71.944*vh)
        episode_move = (400 * self.viewport[1] / 1080)

        while True:
            screenshot = self.adb.screenshot()
            current_episode_tag = screenshot.crop(episode_tag_rect)
            current_episode_str = imgreco.stage_ocr.do_img_ocr(current_episode_tag)
            logger.info(f'当前章节: {current_episode_str}')
            if not current_episode_str.startswith('EPISODE'):
                logger.error(f'章节识别失败, current_episode_str: {current_episode_str}')
                raise RuntimeError('recognition failed')
            current_episode = int(current_episode_str[7:])
            current_region = ep2region.get(current_episode)
            if current_region is None:
                logger.error(f'未能定位章节区域, current_episode: {current_episode}')
                raise RuntimeError('recognition failed')
            if current_region == target_region:
                break
            if current_region > target_region:
                logger.info(f'前往上一章节区域')
                self.tap_rect(prev_ep_region_rect)
            else:
                logger.info(f'前往下一章节区域')
                self.tap_rect(next_ep_region_rect)
        while current_episode != target:
            move = min(abs(current_episode - target), 2) * episode_move * (1 if current_episode > target else -1)
            self.__swipe_screen(move, 10, self.viewport[0] // 4 * 3)
            screenshot = self.adb.screenshot()
            current_episode_tag = screenshot.crop(episode_tag_rect)
            current_episode_str = imgreco.stage_ocr.do_img_ocr(current_episode_tag)
            logger.info(f'当前章节: {current_episode_str}')
            current_episode = int(current_episode_str[7:])

        logger.info(f'进入章节: {current_episode_str}')
        self.tap_rect(current_ep_rect)

    def find_and_tap_stage_by_ocr(self, partition, target, partition_map=None):
        import imgreco.stage_ocr
        target = target.upper()
        if partition_map is None:
            from resources.imgreco.map_vectors import stage_maps_linear
            partition_map = stage_maps_linear[partition]
        target_index = partition_map.index(target)
        while True:
            screenshot = self.adb.screenshot()
            tags_map = imgreco.stage_ocr.recognize_all_screen_stage_tags(screenshot)
            if not tags_map:
                tags_map = imgreco.stage_ocr.recognize_all_screen_stage_tags(screenshot, allow_extra_icons=True)
                if not tags_map:
                    logger.error('未能定位关卡地图')
                    raise RuntimeError('recognition failed')
            logger.debug('tags map: ' + repr(tags_map))
            pos = tags_map.get(target)
            if pos:
                logger.info('目标在可视区域内，点击')
                self.adb.touch_tap(pos, offsets=(5, 5))
                self.__wait(1)
                return

            known_indices = [partition_map.index(x) for x in tags_map.keys() if x in partition_map]

            originX = self.viewport[0] // 2 + randint(-100, 100)
            originY = self.viewport[1] // 2 + randint(-100, 100)
            move = randint(self.viewport[0] // 4, self.viewport[0] // 3)

            if all(x > target_index for x in known_indices):
                logger.info('目标在可视区域左侧，向右拖动')
            elif all(x < target_index for x in known_indices):
                move = -move
                logger.info('目标在可视区域右侧，向左拖动')
            else:
                logger.error('未能定位关卡地图')
                raise RuntimeError('recognition failed')
            self.adb.touch_swipe2((originX, originY), (move, max(250, move // 2)))
            self.__wait(1)

    def find_and_tap_daily(self, partition, target, *, recursion=0):
        screenshot = self.adb.screenshot()
        recoresult = imgreco.map.recognize_daily_menu(screenshot, partition)
        if target in recoresult:
            pos, conf = recoresult[target]
            logger.info('目标 %s 坐标=%s 差异=%f', target, pos, conf)
            offset = self.viewport[1] * 0.12  ## 24vh * 24vh range
            self.tap_rect((*(pos - offset), *(pos + offset)))
        else:
            if recursion == 0:
                originX = self.viewport[0] // 2 + randint(-100, 100)
                originY = self.viewport[1] // 2 + randint(-100, 100)
                if partition == 'material':
                    logger.info('目标可能在可视区域左侧，向右拖动')
                    offset = self.viewport[0] * 0.2
                elif partition == 'soc':
                    logger.info('目标可能在可视区域右侧，向左拖动')
                    offset = -self.viewport[0] * 0.2
                else:
                    logger.error('未知类别')
                    raise StopIteration()
                self.adb.touch_swipe2((originX, originY), (offset, 0), 400)
                self.__wait(2)
                self.find_and_tap_daily(partition, target, recursion=recursion+1)
            else:
                logger.error('未找到目标，是否未开放关卡？')

    def goto_stage_by_ocr(self, stage):
        path = stage_path.get_stage_path(stage)
        self.back_to_main()
        logger.info('进入作战')
        self.tap_quadrilateral(imgreco.main.get_ballte_corners(self.adb.screenshot()))
        self.__wait(TINY_WAIT)
        if path[0] == 'main':
            vw, vh = imgreco.util.get_vwvh(self.viewport)
            self.tap_rect((14.316*vw, 89.815*vh, 28.462*vw, 99.815*vh))
            self.find_and_tap_episode_by_ocr(int(path[1][2:]))
            self.find_and_tap_stage_by_ocr(path[1], path[2])
        elif path[0] == 'material' or path[0] == 'soc':
            logger.info('选择类别')
            self.tap_rect(imgreco.map.get_daily_menu_entry(self.viewport, path[0]))
            self.find_and_tap_daily(path[0], path[1])
            self.find_and_tap(path[1], path[2])
        else:
            raise NotImplementedError()

    def get_credit(self):
        logger.debug("helper.get_credit")
        logger.info("领取信赖")
        self.back_to_main()
        screenshot = self.adb.screenshot()
        logger.info('进入好友列表')
        self.tap_quadrilateral(imgreco.main.get_friend_corners(screenshot))
        self.__wait(SMALL_WAIT)
        self.tap_quadrilateral(imgreco.main.get_friend_list(screenshot))
        self.__wait(SMALL_WAIT)
        logger.info('访问好友基建')
        self.tap_quadrilateral(imgreco.main.get_friend_build(screenshot))
        self.__wait(MEDIUM_WAIT)
        building_count = 0
        while building_count <= 11:
            screenshot = self.adb.screenshot()
            self.tap_quadrilateral(imgreco.main.get_next_friend_build(screenshot))
            self.__wait(MEDIUM_WAIT)
            building_count = building_count + 1
            logger.info('访问第 %s 位好友', building_count)
        logger.info('信赖领取完毕')

    def get_building(self):
        logger.debug("helper.get_building")
        logger.info("清空基建")
        self.back_to_main()
        screenshot = self.adb.screenshot()
        logger.info('进入我的基建')
        self.tap_quadrilateral(imgreco.main.get_back_my_build(screenshot))
        self.__wait(MEDIUM_WAIT + 3)
        self.tap_quadrilateral(imgreco.main.get_my_build_task(screenshot))
        self.__wait(SMALL_WAIT)
        logger.info('收取制造产物')
        self.tap_quadrilateral(imgreco.main.get_my_build_task_clear(screenshot))
        self.__wait(SMALL_WAIT)
        logger.info('清理贸易订单')
        self.tap_quadrilateral(imgreco.main.get_my_sell_task_1(screenshot))
        self.__wait(SMALL_WAIT + 1)
        self.tap_quadrilateral(imgreco.main.get_my_sell_tasklist(screenshot))
        self.__wait(SMALL_WAIT -1 )
        sell_count = 0
        while sell_count <= 6:
            screenshot = self.adb.screenshot()
            self.tap_quadrilateral(imgreco.main.get_my_sell_task_main(screenshot))
            self.__wait(TINY_WAIT)
            sell_count = sell_count + 1
        self.tap_quadrilateral(imgreco.main.get_my_sell_task_2(screenshot))
        self.__wait(SMALL_WAIT - 1)
        sell_count = 0
        while sell_count <= 6:
            screenshot = self.adb.screenshot()
            self.tap_quadrilateral(imgreco.main.get_my_sell_task_main(screenshot))
            self.__wait(TINY_WAIT)
            sell_count = sell_count + 1
        self.back_to_main()
        logger.info("基建领取完毕")

    def log_total_loots(self):
        logger.info('目前已获得：%s', ', '.join('%sx%d' % tup for tup in self.loots.items()))

    def get_inventory_items(self, show_item_name=False):
        import imgreco.inventory

        self.back_to_main()
        logger.info("进入仓库")
        self.tap_rect(imgreco.inventory.get_inventory_rect(self.viewport))

        items = []
        last_screen_items = None
        move = -randint(self.viewport[0] // 5, self.viewport[0] // 4)
        self.__swipe_screen(move)
        self.adb.touch_swipe2((self.viewport[0] // 2, self.viewport[1] - 50), (1, 1), 10)
        screenshot = self.adb.screenshot()
        while True:
            move = -randint(self.viewport[0] // 6, self.viewport[0] // 5)
            self.__swipe_screen(move)
            self.adb.touch_swipe2((self.viewport[0]//2, self.viewport[1] - 50), (1, 1), 10)
            screen_items = imgreco.inventory.get_all_item_details_in_screen(screenshot)
            screen_item_ids = set([item['itemId'] for item in screen_items])
            screen_items_map = {item['itemId']: item['quantity'] for item in screen_items}
            if last_screen_items == screen_item_ids:
                logger.info("读取完毕")
                break
            if show_item_name:
                name_map = {item['itemName']: item['quantity'] for item in screen_items}
                logger.info('name_map: %s' % name_map)
            else:
                logger.info('screen_items_map: %s' % screen_items_map)
            last_screen_items = screen_item_ids
            items += screen_items
            # break
            screenshot = self.adb.screenshot()
        if show_item_name:
            logger.info('items_map: %s' % {item['itemName']: item['quantity'] for item in items})
        return {item['itemId']: item['quantity'] for item in items}

    def __swipe_screen(self, move, rand=100, origin_x=None, origin_y=None):
        origin_x = (origin_x or self.viewport[0] // 2) + randint(-rand, rand)
        origin_y = (origin_y or self.viewport[1] // 2) + randint(-rand, rand)
        self.adb.touch_swipe2((origin_x, origin_y), (move, max(250, move // 2)), randint(600, 900))

    def create_custom_record(self, record_name, roi_size=64, wait_seconds_after_touch=1,
                             description='', back_to_main=True, prefer_mode='match_template', threshold=0.7):
        record_dir = os.path.join(os.path.realpath(os.path.join(__file__, '../../')),
                                  os.path.join('custom_record/', record_name))
        if os.path.exists(record_dir):
            c = input('已存在同名的记录, y 覆盖, n 退出: ')
            if c.strip().lower() != 'y':
                return
            import shutil
            shutil.rmtree(record_dir)
        os.mkdir(record_dir)

        if back_to_main:
            self.back_to_main()

        EVENT_LINE_RE = re.compile(r"(\S+): (\S+) (\S+) (\S+)$")
        records = []
        record_data = {
            'screen_width': self.viewport[0],
            'screen_height': self.viewport[1],
            'description': description,
            'prefer_mode': prefer_mode,
            'back_to_main': back_to_main,
            'records': records
        }
        half_roi = roi_size // 2
        logger.info('滑动屏幕以退出录制.')
        logger.info('开始录制, 请点击相关区域...')
        sock = self.adb.device_session_factory().shell_stream('getevent')
        f = sock.makefile('rb')
        while True:
            x = 0
            y = 0
            point_list = []
            touch_down = False
            screen = self.adb.screenshot()
            while True:
                line = f.readline().decode('utf-8', 'replace').strip()
                # print(line)
                match = EVENT_LINE_RE.match(line.strip())
                if match is not None:
                    dev, etype, ecode, data = match.groups()
                    if '/dev/input/event5' != dev:
                        continue
                    etype, ecode, data = int(etype, 16), int(ecode, 16), int(data, 16)
                    # print(dev, etype, ecode, data)

                    if (etype, ecode) == (1, 330):
                        touch_down = (data == 1)

                    if touch_down:
                        if 53 == ecode:
                            x = data
                        elif 54 == ecode:
                            y = data
                        elif (etype, ecode, data) == (0, 0, 0):
                            # print(f'point: ({x}, {y})')
                            point_list.append((x, y))
                    elif (etype, ecode, data) == (0, 0, 0):
                        break
            logger.debug(f'point_list: {point_list}')
            if len(point_list) == 1:
                point = point_list[0]
                x1 = max(0, point[0] - half_roi)
                x2 = min(self.viewport[0] - 1, point[0] + half_roi)
                y1 = max(0, point[1] - half_roi)
                y2 = min(self.viewport[1] - 1, point[1] + half_roi)
                roi = screen.crop((x1, y1, x2, y2))
                step = len(records)
                roi.save(os.path.join(record_dir, f'step{step}.png'))
                record = {'point': point, 'img': f'step{step}.png', 'type': 'tap',
                          'wait_seconds_after_touch': wait_seconds_after_touch,
                          'threshold': threshold, 'repeat': 1, 'raise_exception': True}
                logger.info(f'record: {record}')
                records.append(record)
                if wait_seconds_after_touch:
                    logger.info(f'请等待 {wait_seconds_after_touch}s...')
                    self.__wait(wait_seconds_after_touch)

                logger.info('继续...')
            elif len(point_list) > 1:
                # 滑动时跳出循环
                c = input('是否退出录制[Y/n]:')
                if c.strip().lower() != 'n':
                    logger.info('停止录制...')
                    break
                else:
                    # todo 处理屏幕滑动
                    continue
        with open(os.path.join(record_dir, f'record.json'), 'w', encoding='utf-8') as f:
            json.dump(record_data, f, ensure_ascii=False, indent=4, sort_keys=True)

    def replay_custom_record(self, record_name, mode=None, back_to_main=None):
        from PIL import Image
        record_dir = os.path.join(os.path.realpath(os.path.join(__file__, '../../')),
                                  os.path.join('custom_record/', record_name))
        if not os.path.exists(record_dir):
            logger.error(f'未找到相应的记录: {record_name}')
            raise RuntimeError(f'未找到相应的记录: {record_name}')

        with open(os.path.join(record_dir, 'record.json'), 'r', encoding='utf-8') as f:
            record_data = json.load(f)
        logger.info(f'record description: {record_data.get("description")}')
        records = record_data['records']
        if mode is None:
            mode = record_data.get('prefer_mode', 'match_template')
        if mode not in ('match_template', 'point'):
            logger.error(f'不支持的模式: {mode}')
            raise RuntimeError(f'不支持的模式: {mode}')
        if back_to_main is None:
            back_to_main = record_data.get('back_to_main', True)
        if back_to_main:
            self.back_to_main()
        record_height = record_data['screen_height']
        ratio = record_height / self.viewport[1]
        x, y = 0, 0
        for record in records:
            if record['type'] == 'tap':
                repeat = record.get('repeat', 1)
                raise_exception = record.get('raise_exception', True)
                threshold = record.get('threshold', 0.7)
                for _ in range(repeat):
                    if mode == 'match_template':
                        screen = self.adb.screenshot()
                        gray_screen = screen.convert('L')
                        if ratio != 1:
                            gray_screen = gray_screen.resize((int(self.viewport[0] * ratio), record_height))
                        template = Image.open(os.path.join(record_dir, record['img'])).convert('L')
                        (x, y), r = imgreco.imgops.match_template(gray_screen, template)
                        x = x // ratio
                        y = y // ratio
                        logger.info(f'(x, y), r, record: {(x, y), r, record}')
                        if r < threshold:
                            if raise_exception:
                                logger.error('无法识别的图像: ' + record['img'])
                                raise RuntimeError('无法识别的图像: ' + record['img'])
                            break
                    elif mode == 'point':
                        # 这个模式屏幕尺寸宽高比必须与记录中的保持一至
                        assert record_data['screen_width'] == int(self.viewport[0] * ratio)
                        x, y = record['point']
                        x = x // ratio
                        y = y // ratio
                    self.adb.touch_tap((x, y), offsets=(5, 5))
                    if record.get('wait_seconds_after_touch'):
                        self.__wait(record['wait_seconds_after_touch'])
