import os
from collections import OrderedDict
from random import randint, uniform
from time import sleep

from ADBShell import ADBShell
from Arknights.BattleSelector import BattleSelector
from Arknights.Binarization import binarization_image
from Arknights.click_location import *
from Arknights.flags import *
from Baidu_api import *
from config import *

os.path.join(os.path.abspath("../"))


class ArknightsHelper(object):
    def __init__(self,
                 current_san=None,   # 当前理智
                 adb_host=None,   # 当前绑定到的设备
                 out_put=True,   # 是否有命令行输出
                 call_by_gui=False):  # 是否为从 GUI 程序调用
        if adb_host is None:
            adb_host = ADB_HOST
        self.adb = ADBShell(adb_host=adb_host)
        self.shell_log = ShellColor() if out_put else BufferColor()
        self.__is_game_active = False
        self.__call_by_gui = call_by_gui
        self.__rebase_to_null = " 1>nul 2>nul" \
            if "win" in os.sys.platform \
            else " 1>/dev/null 2>/dev/null &" \
                                if enable_rebase_to_null else ""
        self.CURRENT_SAN = 100
        self.selector = BattleSelector()
        self.ocr_active = True
        self.is_called_by_gui = call_by_gui
        if not call_by_gui:
            self.is_ocr_active(current_san)

    def __ocr_check(self,
                    file_path,   # 输入文件路径
                    save_path,   # 输出文件路径
                    option=None,   # 附加选项
                    change_image=True):  # 是否预处理图片
        global enable_baidu_api
        if change_image and enable_baidu_api is not True:
            binarization_image(file_path)
        if enable_baidu_api:
            try:
                ocr(file_path, save_path + ".txt")
            except ConnectionError:
                self.shell_log.failure_text("百度API无法连接")
                enable_baidu_api = False
                self.shell_log.info_text("继续使用 tesseract")
        if not enable_baidu_api:
            if option is not None:
                option = " " + option
            os.popen(
                "tesseract {} {}{}".format(file_path, save_path, option)
                + self.__rebase_to_null)
            self.__wait(3)

    def is_ocr_active(self,   # 判断 OCR 是否可用
                      current_san=None):  # 如果不可用时用于初始化的理智值
        global enable_baidu_api
        self.__ocr_check(STORAGE_PATH + "OCR_TEST_1.png",
                         SCREEN_SHOOT_SAVE_PATH + "ocr_test_result", "--psm 7",
                         change_image=False)
        try:
            with open(SCREEN_SHOOT_SAVE_PATH + "ocr_test_result.txt",
                      "r", encoding="utf8") as f:
                tmp = f.read()
                test_1 = int(tmp.split("/")[0])
                if test_1 == 51:
                    self.ocr_active = True
                    return True
                else:
                    raise Exception
        except Exception as e:
            if enable_baidu_api:
                enable_baidu_api = False
                return self.is_ocr_active(current_san)
            self.shell_log.failure_text("OCR 模块识别错误, 使用初始理智值")
            if current_san is not None:
                self.CURRENT_SAN = current_san
            else:
                self.shell_log.failure_text(
                    "未装载初始理智值, 请在初始化 Arknights 助手时赋予初值")
                if not self.is_called_by_gui:
                    exit(0)
                else:
                    return False

    def __del(self):
        self.adb.ch_tools("shell")
        self.adb.ch_abd_command(
            "am force-stop {}".format(ArkNights_PACKAGE_NAME))
        self.adb.run_cmd()

    def destroy(self):
        self.__del()

    def __check_apk_info_active(self):
        self.adb.ch_tools("shell")
        self.adb.ch_abd_command("dumpsys window windows | findstr \"Current\" > {}".format(
            STORAGE_PATH + "package.txt"))
        self.adb.run_cmd(DEBUG_LEVEL=0)

    def check_game_active(self):  # 启动游戏 需要手动调用
        self.__check_apk_info_active()
        with open(STORAGE_PATH + "current.txt", "r", encoding="utf8") as f:
            if ArkNights_PACKAGE_NAME in f.read():
                self.__is_game_active = True
            else:
                self.adb.ch_tools("shell")
                self.adb.ch_abd_command(
                    "am start -n {}/{}".format(ArkNights_PACKAGE_NAME, ArkNights_ACTIVITY_NAME))
                self.adb.run_cmd()
                self.__is_game_active = True

    @staticmethod
    def __wait(mintime=10,   # 等待时间中值
               MANLIKE_FLAG=True):  # 是否在此基础上设偏移量
        if MANLIKE_FLAG:
            m = uniform(0, 0.3)
            n = uniform(n - m * 0.5 * n, n + m * n)
        sleep(n)

    def mouse_click(self,   # 点击一个按钮
                    XY):  # 待点击的按钮的左上和右下坐标
        xx = randint(XY[0][0], XY[1][0])
        yy = randint(XY[0][1], XY[1][1])
        self.adb.get_mouse_click((xx, yy))
        self.__wait(TINY_WAIT, MANLIKE_FLAG=True)

    def module_login(self):
        self.mouse_click(CLICK_LOCATION['LOGIN_QUICK_LOGIN'])
        self.__wait(BIG_WAIT)
        self.mouse_click(CLICK_LOCATION['LOGIN_START_WAKEUP'])
        self.__wait(BIG_WAIT)

    def module_battle_slim(self,
                           c_id,   # 待战斗的关卡编号
                           set_count=1000,   # 战斗次数
                           check_ai=True,   # 是否检查代理指挥
                           ** kwargs):  # 扩展参数:
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
        sub = kwargs["sub"] \
            if "sub" in kwargs.keys() else False
        auto_close = kwargs["auto_close"] \
            if "auto_close" in kwargs.keys() else False
        self_fix = kwargs["self_fix"] \
            if "self_fix" in kwargs.keys() else False
        if not sub:
            self.shell_log.helper_text("战斗-选择{}...启动".format(c_id))
        if check_ai:
            self.set_ai_commander()
        if set_count == 0:
            return True
        san_end_signal = False
        count = 0
        while not san_end_signal:
            # 初始化变量
            battle_end_signal = False
            if "MAX_TIME" in kwargs.keys():
                battle_end_signal_max_execute_time = kwargs["MAX_TIME"]
            else:
                battle_end_signal_max_execute_time = BATTLE_END_SIGNAL_MAX_EXECUTE_TIME
            # 查看剩余理智
            san_end_signal = not self.check_current_san(c_id, self_fix)
            if san_end_signal:
                return True

            self.shell_log.helper_text("开始战斗")
            self.mouse_click(XY=CLICK_LOCATION['BATTLE_CLICK_START_BATTLE'])
            self.__wait(4, False)
            self.mouse_click(
                XY=CLICK_LOCATION['BATTLE_CLICK_ENSURE_TEAM_INFO'])
            t = 0

            while not battle_end_signal:
                # 前 60s 不进行检测
                if t == 0:
                    self.__wait(BATTLE_NONE_DETECT_TIME)
                    t += BATTLE_NONE_DETECT_TIME
                else:
                    self.__wait(BATTLE_FINISH_DETECT)
                t += BATTLE_FINISH_DETECT
                self.shell_log.helper_text("战斗进行{}s 判断是否结束".format(t))
                # 判断是否升级
                self.adb.get_screen_shoot(file_name="battle_status.png")
                self.adb.get_sub_screen(
                    file_name="battle_status.png",
                    screen_range=MAP_LOCATION['BATTLE_INFO_LEVEL_UP'],
                    save_name="level_up_real_time.png"
                )
                level_up_signal = False
                # 检查升级情况
                if enable_ocr_check_update:
                    self.__ocr_check(
                        SCREEN_SHOOT_SAVE_PATH + "level_up_real_time.png",
                        SCREEN_SHOOT_SAVE_PATH + "1",
                        "--psm 7 -l chi_sim"
                    )
                    level_up_text = "等级提升"
                    f = open(SCREEN_SHOOT_SAVE_PATH + "1.txt",
                             "r", encoding="utf8")
                    tmp = f.readline()
                    tmp.replace(' ', '')
                    level_up_signal = level_up_text in tmp
                else:
                    level_up_signal = self.adb.img_difference(
                        img1=SCREEN_SHOOT_SAVE_PATH + "level_up_real_time.png",
                        img2=STORAGE_PATH + "BATTLE_INFO_BATTLE_END_LEVEL_UP.png"
                    ) > .7
                if level_up_signal:
                    battle_end_signal = True
                    self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
                    self.adb.shell_log.helper_text("检测到升级")
                    self.mouse_click(CLICK_LOCATION['CENTER_CLICK'])
                    self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
                    self.mouse_click(CLICK_LOCATION['CENTER_CLICK'])
                    self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
                else:
                    self.adb.get_sub_screen(
                        file_name="battle_status.png",
                        screen_range=MAP_LOCATION['BATTLE_INFO_BATTLE_END'],
                        save_name="battle_end.png"
                    )
                    end_signal = False
                    if enable_ocr_check_end:
                        self.__ocr_check(
                            SCREEN_SHOOT_SAVE_PATH + "battle_end.png",
                            SCREEN_SHOOT_SAVE_PATH + "1",
                            "--psm 7 -l chi_sim"
                        )
                        end_text = "结束"
                        f = open(SCREEN_SHOOT_SAVE_PATH + "1.txt",
                                 "r", encoding="utf8")
                        tmp = f.readline()
                        tmp.replace(' ', '')
                        end_signal = end_text in tmp
                    else:
                        end_signal = self.adb.img_difference(
                            img1=SCREEN_SHOOT_SAVE_PATH + "battle_end.png",
                            img2=STORAGE_PATH + "BATTLE_INFO_BATTLE_END_TRUE.png"
                        ) > .7
                    if end_signal:
                        battle_end_signal = True
                        self.mouse_click(CLICK_LOCATION['CENTER_CLICK'])
                    else:
                        battle_end_signal_max_execute_time -= 1
                    if battle_end_signal_max_execute_time < 1:
                        self.shell_log.failure_text("超过最大战斗时长!")
                        battle_end_signal = True
            count += 1
            self.shell_log.info_text("当前战斗次数 {}".format(count))
            if count >= set_count:
                san_end_signal = True
            self.shell_log.info_text("战斗结束 重新开始")
            self.__wait(10, MANLIKE_FLAG=True)
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