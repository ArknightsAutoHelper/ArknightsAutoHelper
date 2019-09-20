import logging.config
from collections import OrderedDict
from random import randint, uniform
from time import sleep, monotonic

from PIL import Image

from ADBShell import ADBShell
from Arknights.BattleSelector import BattleSelector
from Arknights.Binarization import binarization_image
from Arknights.click_location import *
from Arknights.flags import *
from Baidu_api import *
from config import *
from . import ocr

import richlog
import imgreco

os.path.join(os.path.abspath("../"))
logging.config.fileConfig(os.path.join(CONFIG_PATH, 'logging.ini'))
logger = logging.getLogger('base')


def _logged_ocr(image, *args, **kwargs):
    logger = richlog.get_logger(os.path.join(SCREEN_SHOOT_SAVE_PATH, 'ocrlog.html'))
    logger.loghtml('<hr/>')
    logger.logimage(image)
    ocrresult = ocr.engine.recognize(image, *args, **kwargs)
    logger.logtext(repr(ocrresult.text))
    return ocrresult


class ArknightsHelper(object):
    def __init__(self,
                 current_strength=None,  # 当前理智
                 adb_host=None,  # 当前绑定到的设备
                 out_put=True,  # 是否有命令行输出
                 call_by_gui=False):  # 是否为从 GUI 程序调用
        if adb_host is None:
            adb_host = ADB_HOST
        self.adb = ADBShell(adb_host=adb_host)
        self.shell_log = ShellColor() if out_put else BufferColor(debug_level=DEBUG_LEVEL)
        self.__is_game_active = False
        self.__call_by_gui = call_by_gui
        self.CURRENT_STRENGTH = 100
        self.selector = BattleSelector()
        self.ocr_active = True
        self.is_called_by_gui = call_by_gui
        if DEBUG_LEVEL >= 1:
            self.__print_info()
        if not call_by_gui:
            self.is_ocr_active(current_strength)
        self.shell_log.debug_text("成功初始化模块")

    def __print_info(self):
        self.shell_log.info_text(
            """当前系统信息:
ADB 路径\t{adb_path}
ADB 端口\t{adb_host}
截图路径\t{screen_shoot_path}
存储路径\t{storage_path}
OCR 引擎\t{ocr_engine}
            """.format(
                adb_path=ADB_ROOT, adb_host=ADB_HOST,
                screen_shoot_path=SCREEN_SHOOT_SAVE_PATH, storage_path=STORAGE_PATH,
                ocr_engine=ocr.engine.info
            )
        )
        if enable_baidu_api:
            self.shell_log.info_text(
                """百度API配置信息:
APP_ID\t{app_id}
API_KEY\t{api_key}
SECRET_KEY\t{secret_key}
                """.format(
                    app_id=APP_ID, api_key=API_KEY, secret_key=SECRET_KEY
                )
            )

    def is_ocr_active(self,  # 判断 OCR 是否可用
                      current_strength=None):  # 如果不可用时用于初始化的理智值
        self.shell_log.debug_text("base.is_ocr_active")
        if not ocr.engine.check_supported():
            self.ocr_active = False
            return False
        if ocr.engine.is_online:
            # 不检查在线 OCR 服务可用性
            self.ocr_active = True
            return True
        testimg = Image.open(os.path.join(STORAGE_PATH, "OCR_TEST_1.png"))
        result = _logged_ocr(testimg, 'en', hints=[ocr.OcrHint.SINGLE_LINE])
        if '51/120' in result:
            self.ocr_active = True
            self.shell_log.debug_text("OCR 模块工作正常")
        else:
            self.ocr_active = False
        return self.ocr_active

    def __del(self):
        self.adb.run_device_cmd("am force-stop {}".format(ArkNights_PACKAGE_NAME))

    def destroy(self):
        self.__del()

    def check_game_active(self):  # 启动游戏 需要手动调用
        self.shell_log.debug_text("base.check_game_active")
        current = self.adb.run_device_cmd('dumpsys window windows | grep mCurrentFocus')
        self.shell_log.debug_text("正在尝试启动游戏")
        self.shell_log.debug_text(current)
        if ArkNights_PACKAGE_NAME in current:
            self.__is_game_active = True
            self.shell_log.debug_text("游戏已启动")
        else:
            self.adb.run_device_cmd("am start -n {}/{}".format(ArkNights_PACKAGE_NAME, ArkNights_ACTIVITY_NAME))
            self.shell_log.debug_text("成功启动游戏")
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
        self.shell_log.debug_text("base.mouse_click")
        xx = randint(XY[0][0], XY[1][0])
        yy = randint(XY[0][1], XY[1][1])
        logger.info("接收到点击坐标并传递xx:{}和yy:{}".format(xx, yy))
        self.adb.touch_tap((xx, yy))
        self.__wait(TINY_WAIT, MANLIKE_FLAG=True)

    def module_login(self):
        self.shell_log.debug_text("base.module_login")
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
        self.shell_log.debug_text("base.module_battle_slim")
        sub = kwargs["sub"] \
            if "sub" in kwargs else False
        auto_close = kwargs["auto_close"] \
            if "auto_close" in kwargs else False
        self_fix = kwargs["self_fix"] \
            if "self_fix" in kwargs else False
        self_detect = kwargs["self_detect"] \
            if "self_detect" in kwargs else False
        if not sub:
            self.shell_log.helper_text("战斗-选择{}...启动".format(c_id))
        if set_count == 0:
            return True
        # 如果当前不在进入战斗前的界面就重启
        try:
            for count in range(set_count):
                self.operation_once_statemachine(c_id)
                logger.info("第 %d 次战斗完成", count+1)
                self.__wait(10, MANLIKE_FLAG=True)
        except StopIteration:
            logger.error('已忽略 %d 次战斗', set_count - count)
        if not sub:
            if auto_close:
                self.shell_log.helper_text("简略模块{}结束，系统准备退出".format(c_id))
                self.__wait(120, False)
                self.__del()
            else:
                self.shell_log.helper_text("简略模块{}结束".format(c_id))
                return True
        else:
            self.shell_log.helper_text("当前任务{}结束，准备进行下一项任务".format(c_id))
            return True

    class operation_once_state:
        state = None
        stop = None
        operation_start = None

    def operation_once_statemachine(self, c_id):
        smobj = ArknightsHelper.operation_once_state()
        
        def on_prepare(smobj):
            screenshot = self.adb.get_screen_shoot()
            recoresult = imgreco.before_operation.recognize(screenshot)
            not_in_scene = False
            if not recoresult['AP']:
                # ASSUMPTION: 只有在战斗前界面才能识别到右上角体力
                not_in_scene = True

            if (not not_in_scene) and c_id is not None:
                # 如果传入了关卡 ID，检查识别结果
                logger.info('当前画面关卡：%s', recoresult['operation'])
                if recoresult['operation'] != c_id:
                    not_in_scene = True
            
            if not_in_scene:
                logger.error('不在关卡界面，退出……')
                smobj.stop = True
            
            self.CURRENT_STRENGTH = int(recoresult['AP'].split('/')[0])
            logger.info('当前理智 %d, 关卡消耗 %d', self.CURRENT_STRENGTH, recoresult['consume'])
            if self.CURRENT_STRENGTH < int(recoresult['consume']):
                logger.error('理智不足')
                smobj.stop = True
                return
                raise StopIteration()

            logger.info("开始战斗")
            # logger.info("发送坐标BATTLE_CLICK_START_BATTLE: {}".format(CLICK_LOCATION['BATTLE_CLICK_START_BATTLE']))
            self.mouse_click(CLICK_LOCATION['BATTLE_CLICK_START_BATTLE'])
            self.__wait(4, False)
            smobj.state = on_troop
        def on_troop(smobj):
            logger.info("发送坐标BATTLE_CLICK_ENSURE_TEAM_INFO: {}".format(CLICK_LOCATION['BATTLE_CLICK_ENSURE_TEAM_INFO']))
            self.mouse_click(CLICK_LOCATION['BATTLE_CLICK_ENSURE_TEAM_INFO'])
            smobj.operation_start = monotonic()
            smobj.state = on_operation
        def on_operation(smobj):
            t = monotonic() - smobj.operation_start
            if t < BATTLE_NONE_DETECT_TIME:
                self.__wait(BATTLE_NONE_DETECT_TIME - t)
                return
            self.__wait(BATTLE_FINISH_DETECT)
            logger.info('已进行 %.0f s，判断是否结束', t)
            
            battle_status = self.adb.get_screen_shoot()
            level_up_real_time = self.adb.get_sub_screen(
                battle_status,
                screen_range=MAP_LOCATION['BATTLE_INFO_LEVEL_UP']
            )
            # 检查升级情况
            if enable_ocr_check_update:
                level_up_text = "提升"
                level_up_signal = level_up_text in _logged_ocr(level_up_real_time, 'zh-cn',
                                                                hints=[ocr.OcrHint.SINGLE_LINE])
            else:
                level_up_signal = self.adb.img_difference(
                    img1=level_up_real_time,
                    img2=os.path.join(STORAGE_PATH, "BATTLE_INFO_BATTLE_END_LEVEL_UP.png")
                ) > .7
            if level_up_signal:
                smobj.state = on_level_up_popup
                return
            battle_end = self.adb.get_sub_screen(
                battle_status,
                screen_range=MAP_LOCATION['BATTLE_INFO_BATTLE_END']
            )
            if enable_ocr_check_end:
                end_signal = "结束" in _logged_ocr(battle_end, 'zh-cn', hints=[ocr.OcrHint.SINGLE_LINE])
            else:
                end_signal = self.adb.img_difference(
                    img1=battle_end,
                    img2=os.path.join(STORAGE_PATH, "BATTLE_INFO_BATTLE_END_TRUE.png")
                ) > .7
            if end_signal:
                self.__wait(SMALL_WAIT)
                smobj.state = on_end_operation
        def on_level_up_popup(smobj):
            self.shell_log.helper_text("检测到升级")
            self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
            logger.info("发送坐标CENTER_CLICK: {}".format(CLICK_LOCATION['CENTER_CLICK']))
            self.mouse_click(CLICK_LOCATION['CENTER_CLICK'])
            self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
            smobj.state = on_end_operation
        def on_end_operation(smobj):
            screenshot = self.adb.get_screen_shoot()
            try:
                # 掉落识别
                drops = imgreco.end_operation.recognize(screenshot)
                logger.info('掉落识别结果：%s', repr(drops))
            except Exception as e:
                print(e)
            logger.info("发送坐标CENTER_CLICK: {}".format(CLICK_LOCATION['CENTER_CLICK']))
            self.mouse_click(CLICK_LOCATION['CENTER_CLICK'])
            smobj.stop = True

        smobj.state = on_prepare
        smobj.stop = False
        smobj.operation_start = 0

        while not smobj.stop:
            smobj.state(smobj)


    def __check_is_on_setting(self):  # 检查是否在设置页面，True 为是
        self.shell_log.debug_text("base.__check_is_on_setting")
        is_setting = self.adb.get_screen_shoot(
            screen_range=MAP_LOCATION['INDEX_INFO_IS_SETTING']
        )
        if enable_ocr_debugger:
            ocrresult = _logged_ocr(is_setting, 'zh-cn', hints=[ocr.OcrHint.SINGLE_LINE])
            result = ocrresult.text.replace(' ', '')
            end_text = "设置"
            self.shell_log.debug_text("OCR 识别结果: {}".format(result))
            logger.info("OCR 识别设置结果: {}".format(result))
            return end_text in result
        else:
            return self.adb.img_difference(
                img1=os.path.join(STORAGE_PATH, "INDEX_INFO_IS_SETTING.png"),
                img2=is_setting
            ) > .85

    def __check_is_on_notice(self):  # 检查是否有公告，True为是
        self.shell_log.debug_text("base.__check_is_on_notice")
        is_notice = self.adb.get_screen_shoot(
            screen_range=MAP_LOCATION['INDEX_INFO_IS_NOTICE']
        )
        if enable_ocr_debugger:
            ocrresult = _logged_ocr(is_notice, 'zh-cn', hints=[ocr.OcrHint.SINGLE_LINE])
            return "活动公告" in ocrresult
        else:
            return self.adb.img_difference(
                img1=os.path.join(STORAGE_PATH, "INDEX_INFO_IS_NOTICE.png"),
                img2=is_notice
            ) > .85

    def back_to_main(self):  # 回到主页
        self.shell_log.debug_text("base.back_to_main")
        self.shell_log.helper_text("返回主页ing...")
        # 检测是否有公告，如果有就点掉，点掉公告就是在主页
        if self.__check_is_on_notice():
            self.shell_log.helper_text("触发公告，点掉公告")
            logger.info("发送坐标CLOSE_NOTICE: {}".format(CLICK_LOCATION['CLOSE_NOTICE']))
            self.mouse_click(CLICK_LOCATION['CLOSE_NOTICE'])
            self.shell_log.helper_text("已回到主页")
            self.__wait(SMALL_WAIT, True)
            return
        # 检测左上角是否有返回标志，有就返回，没有就结束
        for i in range(5):
            is_return = self.adb.get_screen_shoot(
                screen_range=MAP_LOCATION['INDEX_INFO_IS_RETURN']
            )
            if self.adb.img_difference(
                    img1=os.path.join(STORAGE_PATH, "INDEX_INFO_IS_RETURN.png"),
                    img2=is_return
            ) > .75:
                self.shell_log.helper_text("未回到主页，点击返回")
                logger.info("发送坐标MAIN_RETURN_INDEX: {}".format(CLICK_LOCATION['MAIN_RETURN_INDEX']))
                self.mouse_click(CLICK_LOCATION['MAIN_RETURN_INDEX'])
                self.__wait(TINY_WAIT, True)
                if self.__check_is_on_notice():
                    self.shell_log.helper_text("触发公告，点掉公告")
                    logger.info("发送坐标CLOSE_NOTICE: {}".format(CLICK_LOCATION['CLOSE_NOTICE']))
                    self.mouse_click(CLICK_LOCATION['CLOSE_NOTICE'])
                    break
            else:
                break
        if self.__check_is_on_setting():
            self.shell_log.helper_text("触发设置，返回")
            logger.info("发送坐标MAIN_RETURN_INDEX: {}".format(CLICK_LOCATION['MAIN_RETURN_INDEX']))
            self.mouse_click(CLICK_LOCATION['MAIN_RETURN_INDEX'])
        self.shell_log.helper_text("已回到主页")
        self.__wait(SMALL_WAIT, True)

    def module_battle(self,  # 完整的战斗模块
                      c_id,  # 选择的关卡
                      set_count=1000):  # 作战次数
        self.shell_log.debug_text("base.module_battle")
        self.back_to_main()
        self.__wait(3, MANLIKE_FLAG=False)
        self.selector.id = c_id
        logger.info("发送坐标BATTLE_CLICK_IN: {}".format(CLICK_LOCATION['BATTLE_CLICK_IN']))
        self.mouse_click(CLICK_LOCATION['BATTLE_CLICK_IN'])
        self.battle_selector(c_id)  # 选关
        self.module_battle_slim(c_id,
                                set_count=set_count,
                                check_ai=True,
                                sub=True,
                                self_fix=self.ocr_active)
        return True

    def main_handler(self, task_list=None, clear_tasks=False):
        self.shell_log.debug_text("base.main_handler")
        if task_list is None:
            task_list = OrderedDict()

        self.shell_log.warning_text("装载模块...")
        self.shell_log.warning_text("战斗模块...启动")
        flag = False
        if task_list.__len__() == 0:
            self.shell_log.failure_text("任务清单为空!")

        for c_id, count in task_list.items():
            if c_id not in MAIN_TASK_SUPPORT.keys():
                raise IndexError("无此关卡!")
            self.shell_log.helper_text("战斗{} 启动".format(c_id))
            self.selector.id = c_id
            flag = self.module_battle(c_id, count)

        if flag:
            if not self.__call_by_gui:
                if clear_tasks:
                    self.clear_daily_task()
                self.shell_log.warning_text("所有模块执行完毕... 60s后退出")
                self.__wait(60)
                self.__del()
            else:
                self.shell_log.warning_text("所有模块执行完毕")
        else:
            if not self.__call_by_gui:
                self.shell_log.warning_text("发生未知错误... 60s后退出")
                self.__wait(60)
                self.__del()
            else:
                self.shell_log.warning_text("发生未知错误... 进程已结束")

    def task_check(self, enable_ocr_check, c_id):
        # 检测是否在关卡页面
        if enable_ocr_check:
            is_on_task = self.adb.get_screen_shoot(screen_range=MAP_LOCATION['ENSURE_ON_TASK_PAGE_OCR'])
            thimg = binarization_image(is_on_task, invert_image=True)
            continue_run = c_id in _logged_ocr(thimg, 'en', hints=[ocr.OcrHint.SINGLE_LINE])
        else:
            is_on_task = self.adb.get_screen_shoot(screen_range=MAP_LOCATION['ENSURE_ON_TASK_PAGE'])
            if self.adb.img_difference(
                    is_on_task,
                    os.path.join(STORAGE_PATH, "ENSURE_ON_TASK_PAGE.png")
            ) <= 0.8:
                self.shell_log.debug_text("相似度对比失败")
                continue_run = False
            else:
                self.shell_log.debug_text("相似度对比成功")
                continue_run = True
        if continue_run:
            self.shell_log.info_text("确认处于关卡页面")
            return False
        else:
            self.shell_log.failure_text("当前未处在关卡页面")
            return True

    def set_ai_commander(self):
        logger.info("发送坐标BATTLE_CLICK_AI_COMMANDER: {}".format(CLICK_LOCATION['BATTLE_CLICK_AI_COMMANDER']))
        self.mouse_click(CLICK_LOCATION['BATTLE_CLICK_AI_COMMANDER'])

    def __check_current_strength(self):  # 检查当前理智是否足够
        self.shell_log.debug_text("base.__check_current_strength")
        assert self.ocr_active
        self.__wait(SMALL_WAIT, False)
        strength = self.adb.get_screen_shoot(
            screen_range=MAP_LOCATION["BATTLE_INFO_STRENGTH_REMAIN"]
        )

        ocrresult = _logged_ocr(binarization_image(strength), 'en', hints=[ocr.OcrHint.SINGLE_LINE])
        tmp = ocrresult.text.replace(' ', '')
        try:
            self.CURRENT_STRENGTH = int(tmp.split("/")[0])
            self.shell_log.helper_text(
                "理智剩余 {}".format(self.CURRENT_STRENGTH))
            logger.info("理智剩余 {}".format(self.CURRENT_STRENGTH))
            return True
        except Exception as e:
            self.shell_log.failure_text("{}".format(e))
            return False

    def __check_current_strength_debug(self, c_id):
        # 查看是否在素材页面
        self.shell_log.debug_text("base.__check_current_strength_debug")
        self.shell_log.helper_text("启动自修复模块,检查是否停留在素材页面")
        debug = self.adb.get_screen_shoot(screen_range=MAP_LOCATION['BATTLE_DEBUG_WHEN_OCR_ERROR'])
        if enable_ocr_debugger:
            end_text = "掉落"
            if end_text in _logged_ocr(binarization_image(debug), 'zh-cn', hints=[ocr.OcrHint.SINGLE_LINE]):
                self.shell_log.helper_text("检测 BUG 成功，系统停留在素材页面，请求返回...")
                logger.info("传递点击坐标MAIN_RETURN_INDEX: {}".format(CLICK_LOCATION['MAIN_RETURN_INDEX']))
                self.adb.touch_tap(
                    CLICK_LOCATION['MAIN_RETURN_INDEX'], offsets=None)
                self.__check_current_strength()
            else:
                self.shell_log.failure_text("检测 BUG 失败，系统将返回主页重新开始")
                self.CURRENT_STRENGTH = -1  # CURRENT_STRENGTH = -1 代表需要需要回到主页重来
        else:
            if self.adb.img_difference(
                    img1=debug,
                    img2=os.path.join(STORAGE_PATH, "BATTLE_DEBUG_CHECK_LOCATION_IN_SUCAI.png")
            ) > 0.75:
                self.shell_log.helper_text("检测 BUG 成功，系统停留在素材页面，请求返回...")
                logger.info("传递点击坐标MAIN_RETURN_INDEX: {}".format(CLICK_LOCATION['MAIN_RETURN_INDEX']))
                self.adb.touch_tap(
                    CLICK_LOCATION['MAIN_RETURN_INDEX'], offsets=None)
                self.__check_current_strength()
            else:
                self.shell_log.failure_text("检测 BUG 失败，系统将返回主页重新开始")
                self.CURRENT_STRENGTH = -1  # CURRENT_STRENGTH = -1 代表需要需要回到主页重来

    def check_current_strength(self, c_id=None, self_fix=False, self_detect=None):
        self.shell_log.debug_text("base.check_current_strength")
        if self.ocr_active:
            self.__wait(SMALL_WAIT, False)
            strength = self.adb.get_screen_shoot(screen_range=MAP_LOCATION["BATTLE_INFO_STRENGTH_REMAIN"])
            ocrresult = _logged_ocr(binarization_image(strength), 'en', hints=[ocr.OcrHint.SINGLE_LINE])
            tmp = ocrresult.text.replace(' ', '')
            try:
                self.CURRENT_STRENGTH = int(tmp.split("/")[0])
                self.shell_log.helper_text(
                    "理智剩余 {}".format(self.CURRENT_STRENGTH))
                logger.info("理智剩余 {}".format(self.CURRENT_STRENGTH))
            except Exception as e:
                self.shell_log.failure_text("{}".format(e))
                if self_fix:
                    self.__check_current_strength_debug(c_id)
                    if self.CURRENT_STRENGTH == -1:
                        return False
                else:
                    self.CURRENT_STRENGTH -= LIZHI_CONSUME[c_id]
        else:
            self.CURRENT_STRENGTH -= LIZHI_CONSUME[c_id]
            self.shell_log.warning_text("OCR 模块未装载，系统将直接计算理智值")
            self.__wait(TINY_WAIT)
            self.shell_log.helper_text(
                "理智剩余 {}".format(self.CURRENT_STRENGTH))

        if self_detect:
            consume_image = self.adb.get_screen_shoot(screen_range=MAP_LOCATION["CONSUME_STRENGTH"])
            ocrresult = _logged_ocr(binarization_image(consume_image), 'en', hints=[ocr.OcrHint.SINGLE_LINE])
            try:
                consume = int(ocrresult.text.replace(' ', '').replace('-', ''))
            except TypeError:
                logger.warning("无法自动识别理智，模块终止，请输入关卡id")
                return False
        else:
            consume = LIZHI_CONSUME[c_id]

        if self.CURRENT_STRENGTH - consume < 0:
            self.shell_log.failure_text("理智不足 退出战斗")
            return False
        else:
            return True

    def battle_selector(self, c_id, first_battle_signal=True):  # 选关
        self.shell_log.debug_text("base.battle_selector")
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
                    self.shell_log.helper_text("拖动 {} 次".format(x))
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
                sleep(SMALL_WAIT)
                logger.info("发送滑动坐标BATTLE_TO_MAP_LEFT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_LEFT".format(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT']
                ))
                self.adb.touch_swipe(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)
                sleep(SMALL_WAIT)
                logger.info("发送滑动坐标BATTLE_TO_MAP_LEFT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_LEFT".format(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT']
                ))
                self.adb.touch_swipe(
                    SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)

                # 拖动到正确的地方
                if c_id in MAIN_TASK_BATTLE_SWIPE.keys():
                    x = MAIN_TASK_BATTLE_SWIPE[c_id]
                    self.shell_log.helper_text("拖动 {} 次".format(x))
                    for x in range(0, x):
                        logger.info(
                            "发送滑动坐标BATTLE_TO_MAP_RIGHT: {}; FLAG=FLAGS_SWIPE_BIAS_TO_RIGHT".format(
                                SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT']
                            ))
                        self.adb.touch_swipe(
                            SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT'], FLAG=FLAGS_SWIPE_BIAS_TO_RIGHT)
                        sleep(5)
                logger.info("发送坐标BATTLE_SELECT_MAIN_TASK_{}: {}".format(c_id, CLICK_LOCATION[
                    'BATTLE_SELECT_MAIN_TASK_{}'.format(c_id)]))
                self.mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK_{}'.format(c_id)])

            else:
                sleep(5)

        elif mode == 2:
            try:
                X = DAILY_LIST[str(mode)][self.selector.get_week()][c_id[0:2]]
            except Exception as e:
                self.shell_log.failure_text(
                    e.__str__() + '\tclick_location 文件配置错误')
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
                self.shell_log.failure_text(
                    e.__str__() + '\tclick_location 文件配置错误')
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
            self.shell_log.helper_text(
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
                    self.shell_log.failure_text('click_location 文件配置错误')
                    exit(0)
            except Exception as e:
                self.shell_log.failure_text(
                    e.__str__() + 'click_location 文件配置错误')
                exit(0)

    def clear_daily_task(self):
        self.shell_log.debug_text("base.clear_daily_task")
        self.shell_log.helper_text("领取每日任务")
        self.back_to_main()
        logger.info("发送坐标TASK_CLICK_IN: {}".format(CLICK_LOCATION['TASK_CLICK_IN']))
        self.mouse_click(CLICK_LOCATION['TASK_CLICK_IN'])
        self.__wait(TINY_WAIT, True)
        logger.info("发送坐标TASK_DAILY_TASK: {}".format(CLICK_LOCATION['TASK_DAILY_TASK']))
        self.mouse_click(CLICK_LOCATION['TASK_DAILY_TASK'])
        self.__wait(TINY_WAIT, True)
        task_ok_signal = True
        while task_ok_signal:
            task_status = self.adb.get_screen_shoot()
            self.shell_log.helper_text("正在检查任务状况")
            task_status_1 = self.adb.get_sub_screen(task_status, screen_range=MAP_LOCATION['TASK_INFO'])
            if enable_ocr_check_task:
                task_ok_text = "领取"
                task_ok_signal = task_ok_text in _logged_ocr(binarization_image(task_status_1), 'zh-cn',
                                                             hints=[ocr.OcrHint.SINGLE_LINE])
            else:
                task_ok_signal = self.adb.img_difference(
                    img1=task_status_1,
                    img2=os.path.join(STORAGE_PATH, "TASK_COMPLETE.png")
                ) > .7
            if not task_ok_signal:  # 检查当前是否在获得物资页面
                self.shell_log.debug_text("未检测到可领取奖励，检查是否在获得物资页面")
                task_status_2 = self.adb.get_sub_screen(
                    task_status,
                    screen_range=MAP_LOCATION['REWARD_GET']
                )
                if enable_ocr_check_task:
                    reward_text = "物资"
                    task_ok_signal = reward_text in _logged_ocr(binarization_image(task_status_2), 'zh-cn',
                                                                hints=[ocr.OcrHint.SINGLE_LINE])
                else:
                    task_ok_signal = self.adb.img_difference(
                        img1=task_status_2,
                        img2=os.path.join(STORAGE_PATH, "REWARD_GET.png")
                    ) > .7
            if task_ok_signal:
                self.shell_log.debug_text("当前有可领取奖励")
                logger.info("发送坐标TASK_DAILY_TASK_CHECK: {}".format(CLICK_LOCATION['TASK_DAILY_TASK_CHECK']))
                self.mouse_click(CLICK_LOCATION['TASK_DAILY_TASK_CHECK'])
                self.__wait(2, False)
        self.shell_log.helper_text("奖励已领取完毕")
