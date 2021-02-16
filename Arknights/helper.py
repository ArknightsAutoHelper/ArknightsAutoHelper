import os
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
import imgreco
import imgreco.imgops
import penguin_stats.reporter
from connector.ADBConnector import ADBConnector, ensure_adb_alive
from . import stage_path
from Arknights.click_location import *
from Arknights.flags import *
from util.exc_guard import guard

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
    def __init__(self,
                 current_strength=None,  # 当前理智
                 adb_host=None,  # 当前绑定到的设备
                 out_put=True,  # 是否有命令行输出
                 call_by_gui=False):  # 是否为从 GUI 程序调用
        ensure_adb_alive()
        self.adb = ADBConnector(adb_serial=adb_host)
        self.__is_game_active = False
        self.__call_by_gui = call_by_gui
        self.is_called_by_gui = call_by_gui
        self.viewport = self.adb.screen_size
        self.operation_time = []
        self.delay_impl = sleep
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
        if Fraction(self.viewport[0], self.viewport[1]) < Fraction(16, 9):
            logger.warn('当前分辨率（%dx%d）不符合要求', self.viewport[0], self.viewport[1])
            if Fraction(self.viewport[1], self.viewport[0]) >= Fraction(16, 9):
                logger.info('屏幕截图可能需要旋转，请尝试在 device-config 中指定旋转角度')
                img = self.adb.screenshot()
                imgfile = os.path.join(config.SCREEN_SHOOT_SAVE_PATH, 'orientation-diagnose-%s.png' % time.strftime("%Y%m%d-%H%M%S"))
                img.save(imgfile)
                import json
                logger.info('参考 %s 以更正 device-config.json[%s]["screenshot_rotate"]', imgfile, json.dumps(self.adb.config_key))

        logger.debug("成功初始化模块")

    def __print_info(self):
        logger.info('当前系统信息:')
        logger.info('ADB 服务器:\t%s:%d', *config.ADB_SERVER)
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
            self.__is_game_active = True
            logger.debug("游戏已启动")
        else:
            self.adb.run_device_cmd(
                "am start -n {}/{}".format(config.ArkNights_PACKAGE_NAME, config.ArkNights_ACTIVITY_NAME))
            logger.debug("成功启动游戏")
            self.__is_game_active = True

    def __wait(self, n=10,  # 等待时间中值
               MANLIKE_FLAG=True):  # 是否在此基础上设偏移量
        if MANLIKE_FLAG:
            m = uniform(0, 0.3)
            n = uniform(n - m * 0.5 * n, n + m * n)
        self.delay_impl(n)

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

    def wait_for_still_image(self, threshold=16, crop=None, timeout=60, raise_for_timeout=True):
        if crop is None:
            shooter = lambda: self.adb.screenshot()
        else:
            shooter = lambda: self.adb.screenshot().crop(crop)
        screenshot = shooter()
        t0 = time.monotonic()
        ts = t0 + timeout
        n = 0
        minerr = 65025
        while time.monotonic() < ts:
            self.__wait(1)
            screenshot2 = shooter()
            mse = imgreco.imgops.compare_mse(screenshot, screenshot2)
            if mse <= threshold:
                return screenshot2
            screenshot = screenshot2
            if mse < minerr:
                minerr = mse
            n += 1
            if n == 9:
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
        if not sub:
            logger.info("战斗-选择{}...启动".format(c_id))
        if set_count == 0:
            return True
        self.operation_time = []
        count = 0
        try:
            for count in range(set_count):
                # logger.info("开始第 %d 次战斗", count + 1)
                self.operation_once_statemachine(c_id, )
                logger.info("第 %d 次作战完成", count + 1)
                if count != set_count - 1:
                    # 2019.10.06 更新逻辑后，提前点击后等待时间包括企鹅物流
                    if config.reporter:
                        self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
                    else:
                        self.__wait(BIG_WAIT, MANLIKE_FLAG=True)
        except StopIteration:
            logger.error('未能进行第 %d 次作战', count + 1)
            remain = set_count - count - 1
            if remain > 0:
                logger.error('已忽略余下的 %d 次战斗', remain)

        if not sub:
            if auto_close:
                logger.info("简略模块{}结束，系统准备退出".format(c_id))
                self.__wait(120, False)
                self.__del()
            else:
                logger.info("简略模块{}结束".format(c_id))
                return True
        else:
            logger.info("当前任务{}结束，准备进行下一项任务".format(c_id))
            return True

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
                    self.tap_rect(imgreco.before_operation.get_start_operation_rect(self.viewport))
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
                self.tap_rect(imgreco.before_operation.get_delegate_rect(self.viewport))
                return  # to on_prepare state

            logger.info("理智充足 开始行动")
            self.tap_rect(imgreco.before_operation.get_start_operation_rect(self.viewport))
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
                self.__wait(wait_time, MANLIKE_FLAG=False)
                smobj.first_wait = False
            t = monotonic() - smobj.operation_start

            logger.info('已进行 %.1f s，判断是否结束', t)

            screenshot = self.adb.screenshot()
            if imgreco.end_operation.check_level_up_popup(screenshot):
                logger.info("等级提升")
                self.operation_time.append(t)
                smobj.state = on_level_up_popup
                return

            if smobj.prepare_reco['consume_ap']:
                detector = imgreco.end_operation.check_end_operation
            else:
                detector = imgreco.end_operation.check_end_operation_alt
            if detector(screenshot):
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
                    smobj.mistaken_delegation = True
                    if config.get('behavior/mistaken_delegation/settle', False):
                        logger.info('以 2 星结算关卡')
                        self.tap_rect(imgreco.common.get_dialog_right_button_rect(screenshot))
                        self.__wait(2)
                        return
                    else:
                        logger.info('放弃关卡')
                        self.tap_rect(imgreco.common.get_dialog_left_button_rect(screenshot))
                        # 关闭失败提示
                        self.wait_for_still_image()
                        self.tap_rect(imgreco.common.get_reward_popup_dismiss_rect(screenshot))
                        self.__wait(1)
                        return
                elif dlgtype == 'yesno' and '将会恢复' in ocrresult:
                    logger.info('发现放弃行动提示，关闭')
                    self.tap_rect(imgreco.common.get_dialog_left_button_rect(screenshot))
                else:
                    logger.error('未处理的对话框：[%s] %s', dlgtype, ocrresult)
                    raise RuntimeError('unhandled dialog')

            logger.info('战斗未结束')
            self.__wait(BATTLE_FINISH_DETECT)

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
                drops = imgreco.end_operation.recognize(screenshot)
                logger.debug('%s', repr(drops))
                logger.info('掉落识别结果：%s', format_recoresult(drops))
                log_total = len(self.loots)
                for _, group in drops['items']:
                    for name, qty in group:
                        if name is not None and qty is not None:
                            self.loots[name] = self.loots.get(name, 0) + qty
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
                if '基建' in ocr or '停止招募' in ocr:
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

            raise RuntimeError('未知画面')
        logger.info("已回到主页")

    def module_battle(self,  # 完整的战斗模块
                      c_id,  # 选择的关卡
                      set_count=1000):  # 作战次数
        logger.debug("helper.module_battle")
        self.goto_stage(c_id)
        self.module_battle_slim(c_id,
                                set_count=set_count,
                                check_ai=True,
                                sub=True)
        return True

    def main_handler(self, task_list, clear_tasks=False, auto_close=True):

        logger.info("装载模块...")
        logger.info("战斗模块...启动")
        flag = False
        if len(task_list) == 0:
            logger.fatal("任务清单为空!")

        for c_id, count in task_list:
            if not stage_path.is_stage_supported(c_id):
                raise ValueError(c_id)
            logger.info("开始 %s", c_id)
            flag = self.module_battle(c_id, count)

        if flag:
            if self.__call_by_gui or auto_close is False:
                logger.info("所有模块执行完毕")
            else:
                if clear_tasks:
                    self.clear_daily_task()
                logger.info("所有模块执行完毕... 60s后退出")
                self.__wait(60)
                self.__del()
        else:
            if self.__call_by_gui or auto_close is False:
                logger.error("发生未知错误... 进程已结束")
            else:
                logger.error("发生未知错误... 60s后退出")
                self.__wait(60)
                self.__del()

    def clear_daily_task(self):
        logger.debug("helper.clear_daily_task")
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

        while imgreco.task.check_collectable_reward(screenshot):
            logger.info('完成任务')
            self.tap_rect(imgreco.task.get_collect_reward_button_rect(self.viewport))
            self.__wait(SMALL_WAIT)
            while True:
                screenshot = self.adb.screenshot()
                if imgreco.common.check_get_item_popup(screenshot):
                    logger.info('领取奖励')
                    self.tap_rect(imgreco.common.get_reward_popup_dismiss_rect(self.viewport))
                    self.__wait(SMALL_WAIT)
                else:
                    break
            screenshot = self.adb.screenshot()
        logger.info("奖励已领取完毕")

    def clear_weekly_task(self):
        logger.debug("helper.clear_weekly_task")
        logger.info("领取每周任务")
        self.back_to_main()
        screenshot = self.adb.screenshot()
        logger.info('进入任务界面')
        self.tap_quadrilateral(imgreco.main.get_task_corners(screenshot))
        self.__wait(SMALL_WAIT)

        screenshot = self.adb.screenshot()
        hasbeginner = imgreco.task.check_beginners_task(screenshot)
        logger.info('切换到每周任务') #默认进入见习任务或每日任务，因此无需检测，直接切换即可
        
        self.tap_rect(imgreco.task.get_weekly_task_rect(screenshot, hasbeginner))
        self.__wait(TINY_WAIT)
        screenshot = self.adb.screenshot()
        while imgreco.task.check_collectable_reward(screenshot):
            logger.info('完成任务')
            self.tap_rect(imgreco.task.get_collect_reward_button_rect(self.viewport))
            self.__wait(SMALL_WAIT)
            while True:
                screenshot = self.adb.screenshot()
                if imgreco.common.check_get_item_popup(screenshot):
                    logger.info('领取奖励')
                    self.tap_rect(imgreco.common.get_reward_popup_dismiss_rect(self.viewport))
                    self.__wait(SMALL_WAIT)
                else:
                    break
            screenshot = self.adb.screenshot()
        logger.info("奖励已领取完毕")

    def recruit(self):
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
                logger.info('目标可能在可视区域右侧，向左拖动')
                originX = self.viewport[0] // 2 + randint(-100, 100)
                originY = self.viewport[1] // 2 + randint(-100, 100)
                self.adb.touch_swipe2((originX, originY), (-self.viewport[0] * 0.2, 0), 400)
                self.__wait(2)
                self.find_and_tap_daily(partition, target, recursion=recursion+1)
            else:
                logger.error('未找到目标，是否未开放关卡？')

    def goto_stage(self, stage):
        if not stage_path.is_stage_supported(stage):
            logger.error('不支持的关卡：%s', stage)
            raise ValueError(stage)
        path = stage_path.get_stage_path(stage)
        self.back_to_main()
        logger.info('进入作战')
        self.tap_quadrilateral(imgreco.main.get_ballte_corners(self.adb.screenshot()))
        self.__wait(3)
        if path[0] == 'main':
            self.find_and_tap('episodes', path[1])
            self.find_and_tap(path[1], path[2])
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
