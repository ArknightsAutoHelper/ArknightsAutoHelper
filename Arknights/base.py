import os
import time
import logging
from collections import OrderedDict
from random import randint, uniform, gauss
from time import sleep, monotonic

import numpy as np

import config
import imgreco
import imgreco.imgops
import penguin_stats.loader
import penguin_stats.reporter
from ADBShell import ADBShell
from Arknights.BattleSelector import BattleSelector
from Arknights.click_location import *
from Arknights.flags import *

logger = logging.getLogger('base')

# import richlog
# from . import ocr
# def _logged_ocr(image, *args, **kwargs):
#     logger = richlog.get_logger(os.path.join(config.SCREEN_SHOOT_SAVE_PATH, 'ocrlog.html'))
#     logger.loghtml('<hr/>')
#     logger.logimage(image)
#     ocrresult = ocr.engine.recognize(image, *args, **kwargs)
#     logger.logtext(repr(ocrresult.text))
#     return ocrresult


def _penguin_init():
    if _penguin_init.ready or _penguin_init.error:
        return
    if not config.get('reporting/enabled', False):
        logger.info('未启用掉落报告')
        _penguin_init.error = True
        return
    try:
        logger.info('载入企鹅数据资源...')
        penguin_stats.loader.load_from_service()
        penguin_stats.loader.user_login()
        _penguin_init.ready = True
    except:
        logger.error('载入企鹅数据资源出错', exc_info=True)
        _penguin_init.error = True


_penguin_init.ready = False
_penguin_init.error = False


def _penguin_report(recoresult):
    _penguin_init()
    if not _penguin_init.ready:
        return False
    logger.info('向企鹅数据汇报掉落...')
    reportid = penguin_stats.reporter.report(recoresult)
    if bool(reportid):
        logger.info('企鹅数据报告 ID: %s', reportid)
    return reportid


class ArknightsHelper(object):
    def __init__(self,
                 current_strength=None,  # 当前理智
                 adb_host=None,  # 当前绑定到的设备
                 out_put=True,  # 是否有命令行输出
                 call_by_gui=False):  # 是否为从 GUI 程序调用
        if adb_host is None:
            adb_host = config.ADB_HOST
        try:
            self.adb = ADBShell(adb_host=adb_host)
        except ConnectionRefusedError as e:
            logger.error("错误: {}".format(e))
            logger.info("尝试启动本地adb")
            try:
                os.system(config.ADB_ROOT + "\\adb kill-server")
                os.system(config.ADB_ROOT + "\\adb start-server")
                self.adb = ADBShell(adb_host=adb_host)
            except Exception as e:
                logger.error("尝试解决失败，错误: {}".format(e))
                logger.info("建议检查adb版本夜神模拟器正确的版本为: 1.0.36")
        self.__is_game_active = False
        self.__call_by_gui = call_by_gui
        self.CURRENT_STRENGTH = 100
        self.selector = BattleSelector()
        self.is_called_by_gui = call_by_gui
        self.viewport = self.adb.get_screen_shoot().size
        self.operation_time = []
        self.delay_impl = sleep
        if DEBUG_LEVEL >= 1:
            self.__print_info()
        self.refill_with_item = config.get('behavior/refill_ap_with_item', False)
        self.refill_with_originium = config.get('behavior/refill_ap_with_oiriginium', False)
        self.use_refill = self.refill_with_item or self.refill_with_originium
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
        logger.debug("base.check_game_active")
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
        logger.debug("base.mouse_click")
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

    def wait_for_still_image(self, screen_range=None):
        screenshot = self.adb.get_screen_shoot(screen_range)
        for n in range(60):
            self.__wait(1)
            screenshot2 = self.adb.get_screen_shoot(screen_range)
            mse = imgreco.imgops.compare_mse(screenshot, screenshot2)
            if mse <= 1:
                return screenshot
            screenshot = screenshot2
            n += 1
            if n == 9:
                logger.info("等待画面静止")
        raise RuntimeError("60秒内画面未静止")

    def module_login(self):
        logger.debug("base.module_login")
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
            每隔一段时间进行一轮检查判断战斗是否结束
            建议自定义该数值以便在出现一定失误,
            超出最大判断次数后有一定的自我修复能力
        :return:
            True 完成指定次数的战斗
            False 理智不足, 退出战斗
        '''
        logger.debug("base.module_battle_slim")
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
                logger.info("开始第 %d 次战斗", count + 1)
                self.operation_once_statemachine(c_id, )
                logger.info("第 %d 次战斗完成", count + 1)
                if count != set_count - 1:
                    # 2019.10.06 更新逻辑后，提前点击后等待时间包括企鹅物流
                    if config.reporter:
                        self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
                    else:
                        self.__wait(BIG_WAIT, MANLIKE_FLAG=True)
        except StopIteration:
            logger.error('未能进行第 %d 次战斗', count + 1)
            remain = set_count - count - 1
            if remain > 0:
                logger.error('已忽略余下的 %d 次战斗', remain)
        logger.info("等待返回{}关卡界面".format(c_id))
        self.__wait(SMALL_WAIT, True)

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

    class operation_once_state:
        def __init__(self):
            self.state = None
            self.stop = False
            self.operation_start = None
            self.first_wait = True

    def operation_once_statemachine(self, c_id):
        smobj = ArknightsHelper.operation_once_state()
        def on_prepare(smobj):
            count_times = 0
            while True:
                screenshot = self.adb.get_screen_shoot()
                recoresult = imgreco.before_operation.recognize(screenshot)
                not_in_scene = False
                if not recoresult['AP']:
                    # ASSUMPTION: 只有在战斗前界面才能识别到右上角体力
                    not_in_scene = True
                if recoresult['consume'] is None:
                    # ASSUMPTION: 所有关卡都显示并能识别体力消耗
                    not_in_scene = True

                logger.info('当前画面关卡：%s', recoresult['operation'])

                if (not not_in_scene) and c_id is not None:
                    # 如果传入了关卡 ID，检查识别结果
                    if recoresult['operation'] != c_id:
                        not_in_scene = True

                if not_in_scene:
                    count_times += 1
                    if count_times <= 7:
                        logger.warning('不在关卡界面，继续等待……')
                        self.__wait(TINY_WAIT, False)
                        continue
                    else:
                        logger.error('{}次检测后都不再关卡界面，退出进程'.format(count_times))
                        raise StopIteration()
                else:
                    break

            self.CURRENT_STRENGTH = int(recoresult['AP'].split('/')[0])
            ap_text = '理智' if recoresult['consume_ap'] else '门票'
            logger.info('当前%s %d, 关卡消耗 %d', ap_text, self.CURRENT_STRENGTH, recoresult['consume'])
            if self.CURRENT_STRENGTH < int(recoresult['consume']):
                logger.error(ap_text + '不足')
                if recoresult['consume_ap'] and self.use_refill:
                    logger.info('尝试回复理智')
                    self.tap_rect(imgreco.before_operation.get_start_operation_rect(self.viewport))
                    self.__wait(SMALL_WAIT)
                    screenshot = self.adb.get_screen_shoot()
                    refill_type = imgreco.before_operation.check_ap_refill_type(screenshot)
                    confirm_refill = False
                    if refill_type == 'item' and self.refill_with_item:
                        logger.info('使用道具回复理智')
                        confirm_refill = True
                    if refill_type == 'originium' and self.refill_with_originium:
                        logger.info('碎石回复理智')
                        confirm_refill = True
                    # FIXME: 1. 道具回复量不足时也会尝试使用
                    # FIXME: 2. 缺少没有道具和源石时的情况
                    if confirm_refill:
                        self.tap_rect(imgreco.before_operation.get_ap_refill_confirm_rect(self.viewport))
                        self.__wait(MEDIUM_WAIT)
                        return  # to on_prepare state
                    logger.error('未能回复理智')
                raise StopIteration()

            if not recoresult['delegated']:
                logger.info('设置代理指挥')
                self.tap_rect(imgreco.before_operation.get_delegate_rect(self.viewport))

            logger.info("开始行动")
            self.tap_rect(imgreco.before_operation.get_start_operation_rect(self.viewport))
            smobj.state = on_troop

        def on_troop(smobj):
            count_times = 0
            while True:
                self.__wait(TINY_WAIT, False)
                screenshot = self.adb.get_screen_shoot()
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
                        logger.error('{}次检测后不再确认编队界面'.format(count_times))
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

            screenshot = self.adb.get_screen_shoot()
            if imgreco.end_operation.check_level_up_popup(screenshot):
                logger.info("检测到升级")
                self.operation_time.append(t)
                smobj.state = on_level_up_popup
                return
            if imgreco.end_operation.check_end_operation(screenshot):
                logger.info('战斗结束')
                self.operation_time.append(t)
                self.wait_for_still_image()
                smobj.state = on_end_operation
                return
            logger.info('战斗未结束')
            self.__wait(BATTLE_FINISH_DETECT)

        def on_level_up_popup(smobj):
            self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
            logger.info('关闭升级提示')
            self.tap_rect(imgreco.end_operation.get_dismiss_level_up_popup_rect(self.viewport))
            self.wait_for_still_image()
            smobj.state = on_end_operation

        def on_end_operation(smobj):
            screenshot = self.adb.get_screen_shoot()
            logger.info('离开结算画面')
            self.tap_rect(imgreco.end_operation.get_dismiss_end_operation_rect(self.viewport))
            reportid = None
            try:
                # 掉落识别
                drops = imgreco.end_operation.recognize(screenshot)
                logger.info('掉落识别结果：%s', repr(drops))
                reportid = _penguin_report(drops)
            except Exception as e:
                logger.error('', exc_info=True)
            if reportid is None:
                filename = os.path.join(config.SCREEN_SHOOT_SAVE_PATH, '未上报掉落-%d.png' % time.time())
                with open(filename, 'wb') as f:
                    screenshot.save(f, format='PNG')
                logger.error('截图已保存到 %s', filename)
            smobj.stop = True

        smobj.state = on_prepare
        smobj.stop = False
        smobj.operation_start = 0

        while not smobj.stop:
            oldstate = smobj.state
            smobj.state(smobj)
            if smobj.state != oldstate:
                logger.debug('state changed to %s', smobj.state.__name__)

    def back_to_main(self):  # 回到主页
        logger.debug("base.back_to_main")
        logger.info("返回主页...")
        while True:
            screenshot = self.adb.get_screen_shoot()

            if imgreco.main.check_main(screenshot):
                break

            # 检查是否有返回按钮
            if imgreco.common.check_nav_button(screenshot):
                logger.info('发现返回按钮，点击返回')
                self.tap_rect(imgreco.common.get_nav_button_back_rect(self.viewport))
                # FIXME: 检查基建退出提示
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

            raise RuntimeError('未知画面')
        logger.info("已回到主页")

    def module_battle(self,  # 完整的战斗模块
                      c_id,  # 选择的关卡
                      set_count=1000):  # 作战次数
        logger.debug("base.module_battle")
        assert (self.viewport == (1280, 720))
        self.back_to_main()
        self.__wait(3, MANLIKE_FLAG=False)
        self.selector.id = c_id
        logger.info("发送坐标BATTLE_CLICK_IN: {}".format(CLICK_LOCATION['BATTLE_CLICK_IN']))
        self.mouse_click(CLICK_LOCATION['BATTLE_CLICK_IN'])
        self.battle_selector(c_id)  # 选关
        self.module_battle_slim(c_id,
                                set_count=set_count,
                                check_ai=True,
                                sub=True)
        return True

    def main_handler(self, task_list=None, clear_tasks=False, auto_close=True):
        logger.debug("base.main_handler")
        if task_list is None:
            task_list = OrderedDict()

        logger.info("装载模块...")
        logger.info("战斗模块...启动")
        flag = False
        if task_list.__len__() == 0:
            logger.fatal("任务清单为空!")

        for c_id, count in task_list.items():
            if c_id not in MAIN_TASK_SUPPORT.keys():
                raise IndexError("无此关卡!")
            logger.info("战斗{} 启动".format(c_id))
            self.selector.id = c_id
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

    def battle_selector(self, c_id, first_battle_signal=True):  # 选关
        logger.debug("base.battle_selector")
        assert (self.viewport == (1280, 720))
        mode = self.selector.id_checker(c_id)  # 获取当前关卡所属章节
        if mode == 1:
            if first_battle_signal:
                logger.info("发送坐标BATTLE_SELECT_MAIN_TASK: {}".format(CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK']))
                self.mouse_click(XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK'])
                logger.info("发送滑动坐标BATTLE_TO_MAP_LEFT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_LEFT".format(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT']))
                self.adb.touch_swipe(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'],
                    FLAG=FLAGS_SWIPE_BIAS_TO_LEFT
                )

                # 拖动到正确的地方
                if c_id[0] in MAIN_TASK_CHAPTER_SWIPE.keys() or c_id[1] in MAIN_TASK_CHAPTER_SWIPE.keys():
                    if c_id[0].isnumeric():
                        x = MAIN_TASK_CHAPTER_SWIPE[c_id[0]]
                    else:
                        x = MAIN_TASK_CHAPTER_SWIPE[c_id[1]]
                    logger.info("拖动 {} 次".format(x))
                    for x in range(0, x):
                        logger.info(
                            "发送滑动坐标BATTLE_TO_MAP_RIGHT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_RIGHT".format(
                                SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT']
                            ))
                        self.adb.touch_swipe(
                            SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT'], FLAG=FLAGS_SWIPE_BIAS_TO_RIGHT)
                        self.__wait(MEDIUM_WAIT)

                # 章节选择
                if c_id[0].isnumeric():
                    logger.info("发送坐标BATTLE_SELECT_MAIN_TASK_{}: {}".format(c_id[0], CLICK_LOCATION[
                        'BATTLE_SELECT_MAIN_TASK_{}'.format(c_id[0])]))
                    self.mouse_click(
                        XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK_{}'.format(c_id[0])])
                elif c_id[0] == "S":
                    logger.info("发送坐标BATTLE_SELECT_MAIN_TASK_{}: {}".format(c_id[1], CLICK_LOCATION[
                        'BATTLE_SELECT_MAIN_TASK_{}'.format(c_id[1])]))
                    self.mouse_click(
                        XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK_{}'.format(c_id[1])])
                else:
                    raise IndexError("C_ID Error")
                self.__wait(3)
                # 章节选择结束
                # 拖动
                logger.info("发送滑动坐标BATTLE_TO_MAP_LEFT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_LEFT".format(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT']
                ))
                self.adb.touch_swipe(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)
                self.__wait(SMALL_WAIT)
                logger.info("发送滑动坐标BATTLE_TO_MAP_LEFT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_LEFT".format(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT']
                ))
                self.adb.touch_swipe(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)
                self.__wait(SMALL_WAIT)
                logger.info("发送滑动坐标BATTLE_TO_MAP_LEFT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_LEFT".format(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT']
                ))
                self.adb.touch_swipe(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)

                # 拖动到正确的地方
                if c_id in MAIN_TASK_BATTLE_SWIPE.keys():
                    x = MAIN_TASK_BATTLE_SWIPE[c_id]
                    logger.info("拖动 {} 次".format(x))
                    for x in range(0, x):
                        logger.info(
                            "发送滑动坐标BATTLE_TO_MAP_RIGHT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_RIGHT".format(
                                SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT']
                            ))
                        self.adb.touch_swipe(
                            SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT'], FLAG=FLAGS_SWIPE_BIAS_TO_RIGHT)
                        self.__wait(MEDIUM_WAIT)
                logger.info("发送坐标BATTLE_SELECT_MAIN_TASK_{}: {}".format(c_id, CLICK_LOCATION[
                    'BATTLE_SELECT_MAIN_TASK_{}'.format(c_id)]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK_{}'.format(c_id)])

            else:
                self.__wait(MEDIUM_WAIT)

        elif mode == 2:
            try:
                X = DAILY_LIST[str(mode)][self.selector.get_week()][c_id[0:2]]
            except Exception as e:
                logger.error('\tclick_location 文件配置错误', exc_info=True)
                X = None
                exit(0)
            if first_battle_signal:
                logger.info("发送滑动坐标BATTLE_TO_MAP_LEFT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_LEFT".format(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT']))
                self.adb.touch_swipe(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)
                logger.info("发送坐标BATTLE_SELECT_MATERIAL_COLLECTION: {}".format(
                    CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION']))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION'])
                logger.info("发送坐标BATTLE_SELECT_MATERIAL_COLLECTION_{}: {}".format(X, CLICK_LOCATION[
                    'BATTLE_SELECT_MATERIAL_COLLECTION_{}'.format(X)]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION_{}'.format(X)])
                logger.info("发送坐标BATTLE_SELECT_MATERIAL_COLLECTION_X-{}: {}".format(c_id[-1], CLICK_LOCATION[
                    'BATTLE_SELECT_MATERIAL_COLLECTION_X-{}'.format(c_id[-1])]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION_X-{}'.format(c_id[-1])])
            else:
                logger.info("发送坐标BATTLE_SELECT_MATERIAL_COLLECTION_X-{}: {}".format(c_id[-1], CLICK_LOCATION[
                    'BATTLE_SELECT_MATERIAL_COLLECTION_X-{}'.format(c_id[-1])]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION_X-{}'.format(c_id[-1])])
        elif mode == 3:
            try:
                X = DAILY_LIST[str(mode)][self.selector.get_week()][c_id[3]]
            except Exception as e:
                logger.error('\tclick_location 文件配置错误', exc_info=True)
                X = None
                exit(0)
            if first_battle_signal:
                logger.info("发送坐标BATTLE_SELECT_CHIP_SEARCH: {}".format(CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH']))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH'])
                logger.info("发送坐标BATTLE_SELECT_CHIP_SEARCH_PR-{}: {}".format(X, CLICK_LOCATION[
                    'BATTLE_SELECT_CHIP_SEARCH_PR-{}'.format(X)]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH_PR-{}'.format(X)])
                logger.info("发送坐标BATTLE_SELECT_CHIP_SEARCH_PR-X-{}: {}".format(c_id[-1], CLICK_LOCATION[
                    'BATTLE_SELECT_CHIP_SEARCH_PR-X-{}'.format(c_id[-1])]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH_PR-X-{}'.format(c_id[-1])])
            else:
                logger.info("发送坐标BATTLE_SELECT_CHIP_SEARCH_PR-X-{}: {}".format(c_id[-1], CLICK_LOCATION[
                    'BATTLE_SELECT_CHIP_SEARCH_PR-X-{}'.format(c_id[-1])]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH_PR-X-{}'.format(c_id[-1])])
        elif mode == 5:
            logger.info("发送坐标BATTLE_SELECT_HEART_OF_SURGING_FLAME: {}".format(
                CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME"]))
            self.mouse_click(
                XY=CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME"])
            logger.info(
                "欢迎来到火蓝之心副本\n祝你在黑曜石音乐节上玩的愉快\n目前主舞台只支持OF-7,OF-8")
            try:
                if c_id[-2] == "F":
                    logger.info("发送坐标BATTLE_SELECT_HEART_OF_SURGING_FLAME_OF-F: {}".format(
                        CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME_OF-F"]))
                    self.mouse_click(
                        XY=CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME_OF-F"])
                    logger.info("发送坐标BATTLE_SELECT_HEART_OF_SURGING_FLAME_{}: {}".format(c_id, CLICK_LOCATION[
                        "BATTLE_SELECT_HEART_OF_SURGING_FLAME_{}".format(c_id)]))
                    self.mouse_click(
                        XY=CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME_{}".format(c_id)])
                elif c_id[-2] == "-":
                    logger.info("发送坐标BATTLE_SELECT_HEART_OF_SURGING_FLAME_OF-: {}".format(
                        CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME_OF-"]))
                    self.mouse_click(
                        XY=CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME_OF-"])

                    for x in range(0, 3):
                        logger.info(
                            "发送滑动坐标BATTLE_TO_MAP_RIGHT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_RIGHT".format(
                                SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT']))
                        self.adb.touch_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT'],
                                             FLAG=FLAGS_SWIPE_BIAS_TO_RIGHT)
                        self.__wait(MEDIUM_WAIT)
                    logger.info("发送坐标BATTLE_SELECT_HEART_OF_SURGING_FLAME_{}: {}".format(c_id, CLICK_LOCATION[
                        "BATTLE_SELECT_HEART_OF_SURGING_FLAME_{}".format(c_id)]))
                    self.mouse_click(
                        XY=CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME_{}".format(c_id)])
                else:
                    logger.error('click_location 文件配置错误')
                    exit(0)
            except Exception as e:
                logger.error('click_location 文件配置错误', exc_info=True)
                exit(0)

    def clear_daily_task(self):
        logger.debug("base.clear_daily_task")
        logger.info("领取每日任务")
        self.back_to_main()
        screenshot = self.adb.get_screen_shoot()
        logger.info('进入任务界面')
        self.tap_quadrilateral(imgreco.main.get_task_corners(screenshot))
        self.__wait(SMALL_WAIT)
        screenshot = self.adb.get_screen_shoot()

        hasbeginner = imgreco.task.check_beginners_task(screenshot)
        if hasbeginner:
            logger.info('发现见习任务，切换到每日任务')
            self.tap_rect(imgreco.task.get_daily_task_rect(screenshot, hasbeginner))
            self.__wait(TINY_WAIT)

        while imgreco.task.check_collectable_reward(screenshot):
            logger.info('完成任务')
            self.tap_rect(imgreco.task.get_collect_reward_button_rect(self.viewport))
            self.__wait(SMALL_WAIT)
            while True:
                screenshot = self.adb.get_screen_shoot()
                if imgreco.common.check_get_item_popup(screenshot):
                    logger.info('领取奖励')
                    self.tap_rect(imgreco.common.get_reward_popup_dismiss_rect(self.viewport))
                    self.__wait(SMALL_WAIT)
                else:
                    break
            screenshot = self.adb.get_screen_shoot()
        logger.info("奖励已领取完毕")
