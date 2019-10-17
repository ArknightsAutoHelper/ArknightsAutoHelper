import logging.config
import os
from collections import OrderedDict
from random import gauss, randint, uniform
from time import monotonic, sleep

import coloredlogs
import numpy as np
from PIL import Image

# from config import *
import config
import imgreco
import penguin_stats.loader
import penguin_stats.reporter
import richlog
from ADBShell import ADBShell
from Arknights.BattleSelector import BattleSelector
from Arknights.click_location import *
from Arknights.flags import *

from . import ocr

logger = logging.getLogger('base')
coloredlogs.install(
    fmt=' Ξ %(message)s',
    #fmt=' %(asctime)s ! %(funcName)s @ %(filename)s:%(lineno)d ! %(levelname)s # %(message)s',
    datefmt='%H:%M:%S',
    level_styles={'info': {'color': 'blue'}, 'warning': {'color': 'green'}, 'error': {'color': 'red'}},
    level='INFO')

def _logged_ocr(image, *args, **kwargs):
    logger = richlog.get_logger(os.path.join(config.SCREEN_SHOOT_SAVE_PATH, 'ocrlog.html'))
    logger.loghtml('<hr/>')
    logger.logimage(image)
    ocrresult = ocr.engine.recognize(image, *args, **kwargs)
    logger.logtext(repr(ocrresult.text))
    return ocrresult


def _penguin_init():
    if _penguin_init.ready or _penguin_init.error:
        return
    if not config.get('reporting/enabled', False):
        logger.debug('[D] 未启用掉落报告')
        _penguin_init.error = True
        return
    try:
        logger.debug('[D] 载入企鹅数据资源...')
        penguin_stats.loader.load_from_service()
        penguin_stats.loader.user_login()
        _penguin_init.ready = True
    except:
        logger.error('[x] 载入企鹅数据资源出错', exc_info=True)
        _penguin_init.error = True


_penguin_init.ready = False
_penguin_init.error = False


def _penguin_report(recoresult):
    _penguin_init()
    if not _penguin_init.ready:
        return
    logger.debug('[D] 向企鹅数据汇报掉落...')
    reportid = penguin_stats.reporter.report(recoresult)
    if reportid is not None:
        logger.debug('[i] 企鹅数据报告 ID: %s', reportid)


class ArknightsHelper(object):
    def __init__(self,
                 current_strength=None,  # 当前理智
                 adb_host=None,  # 当前绑定到的设备
                 out_put=True,  # 是否有命令行输出
                 call_by_gui=False):  # 是否为从 GUI 程序调用
        if adb_host is None:
            adb_host = config.ADB_HOST
        self.adb = ADBShell(adb_host=adb_host)
        self.__is_game_active = False
        self.__call_by_gui = call_by_gui
        self.CURRENT_STRENGTH = 100
        self.selector = BattleSelector()
        self.ocr_active = True
        self.is_called_by_gui = call_by_gui
        self.viewport = self.adb.get_screen_shoot().size
        self.last_operation_time = 0
        if DEBUG_LEVEL >= 1:
            self.__print_info()
        if not call_by_gui:
            self.is_ocr_active()
        logger.debug("[D] 成功初始化模块")

    def __print_info(self):
        logger.info('[i] 当前系统信息:')
        logger.info('[i] ADB 服务器:\t%s:%d', *config.ADB_SERVER)
        logger.info('[i] 分辨率:\t%dx%d', *self.viewport)
        logger.info('[i] OCR 引擎:\t%s', ocr.engine.info)
        logger.info('[i] 截图路径 (legacy):\t%s', config.SCREEN_SHOOT_SAVE_PATH)
        logger.info('[i] 存储路径 (legacy):\t%s', config.STORAGE_PATH)

    def is_ocr_active(self):  # 如果不可用时用于初始化的理智值
        logger.debug("[D] base.is_ocr_active")
        if not ocr.engine.check_supported():
            self.ocr_active = False
            return False
        if ocr.engine.is_online:
            # 不检查在线 OCR 服务可用性
            self.ocr_active = True
            return True
        testimg = Image.open(os.path.join(config.STORAGE_PATH, "OCR_TEST_1.png"))
        result = _logged_ocr(testimg, 'en', hints=[ocr.OcrHint.SINGLE_LINE])
        if '51/120' in result:
            self.ocr_active = True
            logger.debug("[D] OCR 模块工作正常")
        else:
            self.ocr_active = False
        return self.ocr_active

    def __del(self):
        self.adb.run_device_cmd("am force-stop {}".format(config.ArkNights_PACKAGE_NAME))

    def destroy(self):
        self.__del()

    def check_game_active(self):  # 启动游戏 需要手动调用
        logger.debug("[D] base.check_game_active")
        current = self.adb.run_device_cmd('dumpsys window windows | grep mCurrentFocus').decode(errors='ignore')
        logger.debug("[D] 正在尝试启动游戏")
        logger.debug(current)
        if config.ArkNights_PACKAGE_NAME in current:
            self.__is_game_active = True
            logger.debug("[D] 游戏已启动")
        else:
            self.adb.run_device_cmd("am start -n {}/{}".format(config.ArkNights_PACKAGE_NAME, config.ArkNights_ACTIVITY_NAME))
            logger.debug("[D] 成功启动游戏")
            self.__is_game_active = True

    @staticmethod
    def __wait(n=10,  # 等待时间中值
               MANLIKE_FLAG=True):  # 是否在此基础上设偏移量
        if MANLIKE_FLAG:
            m = uniform(0, 0.3)
            n = uniform(n - m * 0.5 * n, n + m * n)
        sleep(n)

    def mouse_click(self,  # 点击一个按钮
                    XY):  # 待点击的按钮的左上和右下坐标
        assert (self.viewport == (1280, 720))
        logger.debug("[D] base.mouse_click")
        xx = randint(XY[0][0], XY[1][0])
        yy = randint(XY[0][1], XY[1][1])
        logger.debug("[D] 接收到点击坐标并传递xx:{}和yy:{}".format(xx, yy))
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

    def module_login(self):
        logger.debug("[D] base.module_login")
        logger.debug("[D] 发送坐标LOGIN_QUICK_LOGIN: {}".format(CLICK_LOCATION['LOGIN_QUICK_LOGIN']))
        self.mouse_click(CLICK_LOCATION['LOGIN_QUICK_LOGIN'])
        self.__wait(BIG_WAIT)
        logger.debug("[D] 发送坐标LOGIN_START_WAKEUP: {}".format(CLICK_LOCATION['LOGIN_START_WAKEUP']))
        self.mouse_click(CLICK_LOCATION['LOGIN_START_WAKEUP'])
        self.__wait(BIG_WAIT)

    def module_battle_slim(self,
                           c_id=None,  # 待作战的关卡编号
                           set_count=1000,  # 作战次数
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
        logger.debug("[D] base.module_battle_slim")
        sub = kwargs["sub"] \
            if "sub" in kwargs else False
        auto_close = kwargs["auto_close"] \
            if "auto_close" in kwargs else False
        if not sub:
            logger.warning("[!] 护肝助手启动")
        if set_count == 0:
            return True
        self.last_operation_time = 0
        try:
            for count in range(set_count):
                self.operation_once_statemachine(c_id, )
                logger.info("[i] 第 %d 次作战完成", count + 1)
                if count != set_count - 1:
                    self.__wait(10, MANLIKE_FLAG=True)
        except StopIteration:
            logger.error('[x] 未能进行第 %d 次作战', count + 1)
        self.__wait(SMALL_WAIT, True)
        
        if not sub:
            if auto_close:
                logger.warning("[!] 护肝助手结束，系统准备退出")
                self.__wait(120, False)
                self.__del()
            else:
                logger.warning("[!] 护肝助手退出")
                return True
        else:
            logger.warning("[!] 当前任务结束，准备进行下一项任务")
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
            screenshot = self.adb.get_screen_shoot()
            recoresult = imgreco.before_operation.recognize(screenshot)
            not_in_scene = False
            if not recoresult['AP']:
                # ASSUMPTION: 只有在作战前界面才能识别到右上角体力
                not_in_scene = True
            if recoresult['consume'] is None:
                # ASSUMPTION: 所有关卡都显示并能识别体力消耗
                not_in_scene = True

            logger.debug('[D] 当前画面关卡：%s', recoresult['operation'])

            if (not not_in_scene) and c_id is not None:
                # 如果传入了关卡 ID，检查识别结果
                if recoresult['operation'] != c_id:
                    not_in_scene = True

            if not_in_scene:
                logger.error('[x] 不在关卡界面')
                raise StopIteration()

            self.CURRENT_STRENGTH = int(recoresult['AP'].split('/')[0])
            logger.info('[i] 当前理智 %d, 关卡消耗 %d', self.CURRENT_STRENGTH, recoresult['consume'])
            if self.CURRENT_STRENGTH < int(recoresult['consume']):
                logger.error('[x] 理智不足 无法继续')
                raise StopIteration()
            if not recoresult['delegated']:
                logger.debug('[D] 代理指挥')
                self.tap_rect(imgreco.before_operation.get_delegate_rect(self.viewport))
            logger.info("[i] 理智充足 开始行动")
            self.tap_rect(imgreco.before_operation.get_start_operation_rect(self.viewport))
            smobj.state = on_troop

        def on_troop(smobj):
            self.__wait(SMALL_WAIT, False)
            logger.debug('[D] 确认编队')
            self.tap_rect(imgreco.before_operation.get_confirm_troop_rect(self.viewport))
            smobj.operation_start = monotonic()
            smobj.state = on_operation

        def on_operation(smobj):
            if smobj.first_wait:
                if self.last_operation_time == 0:
                    wait_time = BATTLE_NONE_DETECT_TIME
                else:
                    wait_time = self.last_operation_time
                logger.debug('[D] 等待 %d s' % wait_time)
                self.__wait(wait_time)
                smobj.first_wait = False
            t = monotonic() - smobj.operation_start

            logger.debug('[D] 已进行 %.1f s，判断是否结束', t)

            screenshot = self.adb.get_screen_shoot()
            if imgreco.end_operation.check_level_up_popup(screenshot):
                logger.info("[i] 等级提升")
                smobj.state = on_level_up_popup
                once_task_time = t*0.95
                return
            if imgreco.end_operation.check_end_operation(screenshot):
                logger.debug('[D] 战斗结束')
                self.__wait(SMALL_WAIT)
                smobj.state = on_end_operation
                once_task_time = t*0.95
                return
            logger.debug('[D] 战斗未结束')
            self.__wait(BATTLE_FINISH_DETECT)

        def on_level_up_popup(smobj):
            self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
            logger.debug('[D] 关闭升级提示')
            self.tap_rect(imgreco.end_operation.get_dismiss_level_up_popup_rect(self.viewport))
            self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
            smobj.state = on_end_operation

        def on_end_operation(smobj):
            screenshot = self.adb.get_screen_shoot()
            try:
                # 掉落识别
                drops, dropsitem = imgreco.end_operation.recognize(screenshot)
                logger.info('[i] 掉落识别结果：')
                logger.info('[i] %s', repr(dropsitem))
                logger.debug('[i] %s', repr(drops))
                _penguin_report(drops)
            except Exception as e:
                logger.error('[x] 掉落识别失败', exc_info=True)
            logger.debug('[D] 离开结算画面')
            self.tap_rect(imgreco.end_operation.get_dismiss_end_operation_rect(self.viewport))
            smobj.stop = True

        smobj.state = on_prepare
        smobj.stop = False
        smobj.operation_start = 0

        while not smobj.stop:
            oldstate = smobj.state
            smobj.state(smobj)
            if smobj.state != oldstate:
                logger.debug('[D] state changed to %s', smobj.state.__name__)

    def back_to_main(self):  # 回到主页
        logger.debug("[D] base.back_to_main")
        logger.info("[i] 正在返回主页")
        while True:
            screenshot = self.adb.get_screen_shoot()
            if imgreco.main.check_main(screenshot):
                break
            # 检查是否有返回按钮
            if imgreco.common.check_nav_button(screenshot):
                logger.debug('[D] 发现返回按钮，点击返回')
                self.tap_rect(imgreco.common.get_nav_button_back_rect(self.viewport))
                # FIXME: 检查基建退出提示
                self.__wait(SMALL_WAIT)
                # 点击返回按钮之后重新检查
                continue

            if imgreco.common.check_get_item_popup(screenshot):
                logger.debug('[D] 当前为获得物资画面，关闭')
                self.tap_rect(imgreco.common.get_reward_popup_dismiss_rect(self.viewport))
                self.__wait(SMALL_WAIT)
                continue

            # 检查是否在设置画面
            if imgreco.common.check_setting_scene(screenshot):
                logger.debug("[D] 当前为设置/邮件画面，返回")
                self.tap_rect(imgreco.common.get_setting_back_rect(self.viewport))
                self.__wait(SMALL_WAIT)
                continue

            # 检测是否有关闭按钮
            rect, confidence = imgreco.common.find_close_button(screenshot)
            if confidence > 0.9:
                logger.info("[i] 发现关闭按钮")
                self.tap_rect(rect)
                self.__wait(SMALL_WAIT)
                continue

            raise RuntimeError('未知画面')
        logger.info("[i] 已回到主页")

    def module_battle(self,  # 完整的战斗模块
                      c_id,  # 选择的关卡
                      set_count=1000):  # 作战次数
        logger.debug("[D] base.module_battle")
        assert (self.viewport == (1280, 720))
        self.back_to_main()
        self.__wait(3, MANLIKE_FLAG=False)
        self.selector.id = c_id
        logger.info("[i] 发送坐标BATTLE_CLICK_IN: {}".format(CLICK_LOCATION['BATTLE_CLICK_IN']))
        self.mouse_click(CLICK_LOCATION['BATTLE_CLICK_IN'])
        self.battle_selector(c_id)  # 选关
        self.module_battle_slim(c_id,
                                set_count=set_count,
                                check_ai=True,
                                sub=True,
                                self_fix=self.ocr_active)
        return True

    def main_handler(self, task_list=None, clear_tasks=False, auto_close=True):
        logger.debug("[D] base.main_handler")
        if task_list is None:
            task_list = OrderedDict()

        logger.info("[i] 装载模块...")
        logger.info("[i] 战斗模块...启动")
        flag = False
        if task_list.__len__() == 0:
            logger.fatal("[x] 任务清单为空!")

        for c_id, count in task_list.items():
            if c_id not in MAIN_TASK_SUPPORT.keys():
                raise IndexError("无此关卡!")
            logger.info("[i] 战斗{} 启动".format(c_id))
            self.selector.id = c_id
            flag = self.module_battle(c_id, count)

        if flag:
            if self.__call_by_gui or auto_close is False:
                logger.info("[i] 所有模块执行完毕")
            else:
                if clear_tasks:
                    self.clear_daily_task()
                logger.info("[i] 所有模块执行完毕... 60s后退出")
                self.__wait(60)
                self.__del()
        else:
            if self.__call_by_gui or auto_close is False:
                logger.error("[x] 发生未知错误... 进程已结束")
            else:
                logger.error("[x] 发生未知错误... 60s后退出")
                self.__wait(60)
                self.__del()


    def battle_selector(self, c_id, first_battle_signal=True):  # 选关
        logger.debug("[D] base.battle_selector")
        assert (self.viewport == (1280, 720))
        mode = self.selector.id_checker(c_id)  # 获取当前关卡所属章节
        if mode == 1:
            if first_battle_signal:
                logger.info("[i] 发送坐标BATTLE_SELECT_MAIN_TASK: {}".format(CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK']))
                self.mouse_click(XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK'])
                logger.info("[i] 发送滑动坐标BATTLE_TO_MAP_LEFT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_LEFT".format(
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
                    logger.info("[i] 拖动 {} 次".format(x))
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
                    logger.info("[i] 发送坐标BATTLE_SELECT_MAIN_TASK_{}: {}".format(c_id[0], CLICK_LOCATION[
                        'BATTLE_SELECT_MAIN_TASK_{}'.format(c_id[0])]))
                    self.mouse_click(
                        XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK_{}'.format(c_id[0])])
                elif c_id[0] == "S":
                    logger.info("[i] 发送坐标BATTLE_SELECT_MAIN_TASK_{}: {}".format(c_id[1], CLICK_LOCATION[
                        'BATTLE_SELECT_MAIN_TASK_{}'.format(c_id[1])]))
                    self.mouse_click(
                        XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK_{}'.format(c_id[1])])
                else:
                    raise IndexError("C_ID Error")
                self.__wait(3)
                # 章节选择结束
                # 拖动
                logger.info("[i] 发送滑动坐标BATTLE_TO_MAP_LEFT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_LEFT".format(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT']
                ))
                self.adb.touch_swipe(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)
                self.__wait(SMALL_WAIT)
                logger.info("[i] 发送滑动坐标BATTLE_TO_MAP_LEFT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_LEFT".format(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT']
                ))
                self.adb.touch_swipe(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)
                self.__wait(SMALL_WAIT)
                logger.info("[i] 发送滑动坐标BATTLE_TO_MAP_LEFT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_LEFT".format(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT']
                ))
                self.adb.touch_swipe(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)

                # 拖动到正确的地方
                if c_id in MAIN_TASK_BATTLE_SWIPE.keys():
                    x = MAIN_TASK_BATTLE_SWIPE[c_id]
                    logger.info("[i] 拖动 {} 次".format(x))
                    for x in range(0, x):
                        logger.info(
                            "发送滑动坐标BATTLE_TO_MAP_RIGHT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_RIGHT".format(
                                SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT']
                            ))
                        self.adb.touch_swipe(
                            SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT'], FLAG=FLAGS_SWIPE_BIAS_TO_RIGHT)
                        self.__wait(MEDIUM_WAIT)
                logger.info("[i] 发送坐标BATTLE_SELECT_MAIN_TASK_{}: {}".format(c_id, CLICK_LOCATION[
                    'BATTLE_SELECT_MAIN_TASK_{}'.format(c_id)]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK_{}'.format(c_id)])

            else:
                self.__wait(MEDIUM_WAIT)

        elif mode == 2:
            try:
                X = DAILY_LIST[str(mode)][self.selector.get_week()][c_id[0:2]]
            except Exception as e:
                logger.error('[x] \tclick_location 文件配置错误', exc_info=True)
                X = None
                exit(0)
            if first_battle_signal:
                logger.info("[i] 发送滑动坐标BATTLE_TO_MAP_LEFT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_LEFT".format(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT']))
                self.adb.touch_swipe(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)
                logger.info("[i] 发送坐标BATTLE_SELECT_MATERIAL_COLLECTION: {}".format(
                    CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION']))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION'])
                logger.info("[i] 发送坐标BATTLE_SELECT_MATERIAL_COLLECTION_{}: {}".format(X, CLICK_LOCATION[
                    'BATTLE_SELECT_MATERIAL_COLLECTION_{}'.format(X)]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION_{}'.format(X)])
                logger.info("[i] 发送坐标BATTLE_SELECT_MATERIAL_COLLECTION_X-{}: {}".format(c_id[-1], CLICK_LOCATION[
                    'BATTLE_SELECT_MATERIAL_COLLECTION_X-{}'.format(c_id[-1])]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION_X-{}'.format(c_id[-1])])
            else:
                logger.info("[i] 发送坐标BATTLE_SELECT_MATERIAL_COLLECTION_X-{}: {}".format(c_id[-1], CLICK_LOCATION[
                    'BATTLE_SELECT_MATERIAL_COLLECTION_X-{}'.format(c_id[-1])]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION_X-{}'.format(c_id[-1])])
        elif mode == 3:
            try:
                X = DAILY_LIST[str(mode)][self.selector.get_week()][c_id[3]]
            except Exception as e:
                logger.error('[x] \tclick_location 文件配置错误', exc_info=True)
                X = None
                exit(0)
            if first_battle_signal:
                logger.info("[i] 发送坐标BATTLE_SELECT_CHIP_SEARCH: {}".format(CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH']))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH'])
                logger.info("[i] 发送坐标BATTLE_SELECT_CHIP_SEARCH_PR-{}: {}".format(X, CLICK_LOCATION[
                    'BATTLE_SELECT_CHIP_SEARCH_PR-{}'.format(X)]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH_PR-{}'.format(X)])
                logger.info("[i] 发送坐标BATTLE_SELECT_CHIP_SEARCH_PR-X-{}: {}".format(c_id[-1], CLICK_LOCATION[
                    'BATTLE_SELECT_CHIP_SEARCH_PR-X-{}'.format(c_id[-1])]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH_PR-X-{}'.format(c_id[-1])])
            else:
                logger.info("[i] 发送坐标BATTLE_SELECT_CHIP_SEARCH_PR-X-{}: {}".format(c_id[-1], CLICK_LOCATION[
                    'BATTLE_SELECT_CHIP_SEARCH_PR-X-{}'.format(c_id[-1])]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH_PR-X-{}'.format(c_id[-1])])
        elif mode == 5:
            logger.info("[i] 发送坐标BATTLE_SELECT_HEART_OF_SURGING_FLAME: {}".format(
                CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME"]))
            self.mouse_click(
                XY=CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME"])
            logger.info(
                "欢迎来到火蓝之心副本\n祝你在黑曜石音乐节上玩的愉快\n目前主舞台只支持OF-7,OF-8")
            try:
                if c_id[-2] == "F":
                    logger.info("[i] 发送坐标BATTLE_SELECT_HEART_OF_SURGING_FLAME_OF-F: {}".format(
                        CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME_OF-F"]))
                    self.mouse_click(
                        XY=CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME_OF-F"])
                    logger.info("[i] 发送坐标BATTLE_SELECT_HEART_OF_SURGING_FLAME_{}: {}".format(c_id, CLICK_LOCATION[
                        "BATTLE_SELECT_HEART_OF_SURGING_FLAME_{}".format(c_id)]))
                    self.mouse_click(
                        XY=CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME_{}".format(c_id)])
                elif c_id[-2] == "-":
                    logger.info("[i] 发送坐标BATTLE_SELECT_HEART_OF_SURGING_FLAME_OF-: {}".format(
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
                    logger.info("[i] 发送坐标BATTLE_SELECT_HEART_OF_SURGING_FLAME_{}: {}".format(c_id, CLICK_LOCATION[
                        "BATTLE_SELECT_HEART_OF_SURGING_FLAME_{}".format(c_id)]))
                    self.mouse_click(
                        XY=CLICK_LOCATION["BATTLE_SELECT_HEART_OF_SURGING_FLAME_{}".format(c_id)])
                else:
                    logger.error('[x] click_location 文件配置错误')
                    exit(0)
            except Exception as e:
                logger.error('[x] click_location 文件配置错误', exc_info=True)
                exit(0)

    def clear_daily_task(self):
        logger.debug("[D] base.clear_daily_task")
        logger.info("[i] 领取每日任务")
        self.back_to_main()
        screenshot = self.adb.get_screen_shoot()
        logger.info('[i] 进入任务界面')
        self.tap_quadrilateral(imgreco.main.get_task_corners(screenshot))
        self.__wait(SMALL_WAIT)
        screenshot = self.adb.get_screen_shoot()
        hasbeginner = imgreco.task.check_beginners_task(screenshot)
        if hasbeginner:
            logger.info('[i] 发现见习任务，切换到每日任务')
            self.tap_rect(imgreco.task.get_daily_task_rect(screenshot, hasbeginner))
            self.__wait(TINY_WAIT)
        while imgreco.task.check_collectable_reward(screenshot):
            logger.debug('[D] 完成任务')
            self.tap_rect(imgreco.task.get_collect_reward_button_rect(self.viewport))
            self.__wait(SMALL_WAIT)
            while True:
                screenshot = self.adb.get_screen_shoot()
                if imgreco.common.check_get_item_popup(screenshot):
                    logger.info('[i] 领取奖励')
                    self.tap_rect(imgreco.common.get_reward_popup_dismiss_rect(self.viewport))
                    self.__wait(SMALL_WAIT)
                else:
                    break
            screenshot = self.adb.get_screen_shoot()
        logger.info("[i] 奖励已领取完毕")
        
    def get_credit(self):
        logger.debug("[D] base.get_credit")
        logger.info("[i] 领取信赖")
        self.back_to_main()
        screenshot = self.adb.get_screen_shoot()
        logger.info('[i] 进入好友列表')
        self.tap_quadrilateral(imgreco.main.get_friend_corners(screenshot))
        self.__wait(SMALL_WAIT)
        self.tap_quadrilateral(imgreco.main.get_friend_list(screenshot))
        self.__wait(SMALL_WAIT)
        logger.info('[i] 访问好友基建')
        self.tap_quadrilateral(imgreco.main.get_friend_build(screenshot))
        self.__wait(MEDIUM_WAIT)
        building_count = 0
        while building_count <= 11:
            screenshot = self.adb.get_screen_shoot()
            self.tap_quadrilateral(imgreco.main.get_next_friend_build(screenshot))
            self.__wait(MEDIUM_WAIT)
            building_count = building_count + 1
            logger.info('[i] 访问第 %s 位好友', building_count)
        logger.info('[i] 信赖领取完毕')
    
    def get_building(self):
        logger.debug("[D] base.get_building")
        logger.info("[i] 清空基建")
        self.back_to_main()
        screenshot = self.adb.get_screen_shoot()
        logger.info('[i] 进入我的基建')
        self.tap_quadrilateral(imgreco.main.get_back_my_build(screenshot))
        self.__wait(MEDIUM_WAIT + 3)
        self.tap_quadrilateral(imgreco.main.get_my_build_task(screenshot))
        self.__wait(SMALL_WAIT)
        logger.info('[i] 收取制造产物')
        self.tap_quadrilateral(imgreco.main.get_my_build_task_clear(screenshot))
        self.__wait(SMALL_WAIT)
        logger.info('[i] 清理贸易订单')
        self.tap_quadrilateral(imgreco.main.get_my_sell_task_1(screenshot))
        self.__wait(SMALL_WAIT + 1)
        self.tap_quadrilateral(imgreco.main.get_my_sell_tasklist(screenshot))
        self.__wait(SMALL_WAIT -1 )
        sell_count = 0
        while sell_count <= 6:
            screenshot = self.adb.get_screen_shoot()
            self.tap_quadrilateral(imgreco.main.get_my_sell_task_main(screenshot))
            self.__wait(TINY_WAIT)
            sell_count = sell_count + 1
        self.tap_quadrilateral(imgreco.main.get_my_sell_task_2(screenshot))
        self.__wait(SMALL_WAIT - 1)
        sell_count = 0
        while sell_count <= 6:
            screenshot = self.adb.get_screen_shoot()
            self.tap_quadrilateral(imgreco.main.get_my_sell_task_main(screenshot))
            self.__wait(TINY_WAIT)
            sell_count = sell_count + 1
        self.back_to_main()
        logger.info("[i] 基建领取完毕")