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
                 current_san=None,  # 当前理智
                 adb_host=None,  # 当前绑定到的设备
                 out_put=True,  # 是否有命令行输出
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
                    file_path,  # 输入文件路径
                    save_path,  # 输出文件路径
                    option=None,  # 附加选项
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

    def is_ocr_active(self,  # 判断 OCR 是否可用
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
            self.shell_log.failure_text("OCR 模块识别错误，使用初始理智值")
            if current_san is not None:
                self.CURRENT_SAN = current_san
            else:
                self.shell_log.failure_text("未装载初始理智值，请在初始化 Arknights 助手时赋予初值")
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
    def __wait(mintime=10,  # 等待时间中值
               MANLIKE_FLAG=True):  # 是否在此基础上设偏移量
        if MANLIKE_FLAG:
            m = uniform(0, 0.3)
            n = uniform(n - m * 0.5 * n, n + m * n)
        sleep(n)
