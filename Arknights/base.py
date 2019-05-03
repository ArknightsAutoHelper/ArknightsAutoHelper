import os

os.path.join(os.path.abspath('../'))

from ADBShell import ADBShell
from config import *
from time import sleep
from Arknights.click_location import *
from collections import OrderedDict


class BattleChapter(object):
    def __init__(self):
        self.battle_selectors = {
            1: 'MAIN_TASK',  # 主线任务
            2: 'MATERIAL_COLLECTION',  # 物资筹备
            3: 'CHIP_SEARCH',  # 芯片收集
            4: 'EXTERMINATE_BATTLE'
        }

    @staticmethod
    def id_checker(id):
        if id[0].isnumeric() or id[0:2] == "S-":
            return 1
        elif id[0:2].upper() == "CE" or id[0:2].upper() == "SK":
            return 2
        elif id[0:2].upper() == "PR":
            return 3
        # elif id[0].upper() == "E":
        #     return 4
        else:
            return False


class ArknightsHelper(object):
    def __init__(self):
        self.adb = ADBShell()
        self.shell_color = ShellColor()
        self.__is_game_active = False
        self.__check_game_active()
        self.MAX_STRENGTH = 80
        self.CURRENT_STRENGTH = 80
        self.ch_id = BattleChapter()

    def __del(self):
        self.adb.ch_tools("shell")
        self.adb.ch_abd_command("am force-stop {}".format(ArkNights_PACKAGE_NAME))
        self.adb.run_cmd()

    def __check_apk_info_active(self):
        """
        IT IS JUST A HELPER FUNCTION
        :return:
        """
        self.adb.ch_tools("shell")
        self.adb.ch_abd_command("dumpsys window windows | findstr \"Current\" > {}"
                                .format(STORAGE_PATH + "package.txt"))
        self.adb.run_cmd(DEBUG_LEVEL=0)

    def __check_game_active(self):
        self.__check_apk_info_active()

        with open(STORAGE_PATH + "current.txt", 'r', encoding='utf8') as f:
            if ArkNights_PACKAGE_NAME in f.read():
                self.__is_game_active = True
            else:
                self.adb.ch_tools("shell")
                self.adb.ch_abd_command("am start -n {}/{}".format(ArkNights_PACKAGE_NAME, ArkNights_ACTIVITY_NAME))
                self.adb.run_cmd()
                self.__is_game_active = True

    @staticmethod
    def __wait(n=10):
        sleep(n)

    def module_login(self):
        self.__wait(SECURITY_WAIT)
        self.adb.get_mouse_click(
            XY=CLICK_LOCATION['LOGIN_QUICK_LOGIN']
        )
        self.__wait(SECURITY_WAIT)
        self.adb.get_mouse_click(
            XY=CLICK_LOCATION['LOGIN_START_WAKEUP']
        )
        self.__wait(SECURITY_WAIT)
        self.adb.get_screen_shoot("login.png")

    def battle_selector(self, c_id, first_battle_signal=False):
        if self.ch_id.id_checker(c_id) == 1:
            self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'])
            # 拖到关卡最左边;为了保证没有问题，第一次拖动3次
            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK']
            )
            if c_id[0].isnumeric():
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK_{}'.format(c_id[0])]
                )
            elif c_id[0] == "S":
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK_{}'.format(c_id[1])]
                )
            else:
                raise IndexError("C_ID Error")
            self.__wait(3)

            self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'])
            if first_battle_signal:
                self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'])
                sleep(SMALL_WAIT)
                self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'])
                sleep(SMALL_WAIT)
                self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'])
            else:
                self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'])

            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK_{}'.format(c_id)]
            )

        elif self.ch_id.id_checker(c_id) == 2:
            self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'])
            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION']
            )

            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION_{}'.format(c_id[0:2])]
            )

            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION_{}'.format(c_id)]
            )
        elif self.ch_id.id_checker(c_id) == 3:
            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH']
            )
            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH_{}'.format(c_id[0:4])]
            )

            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH_{}'.format(c_id)]
            )

    def module_battle(self, c_id, set_count=1000):
        strength_end_signal = False
        first_battle_signal = True
        count = 0
        while not strength_end_signal:
            # 初始化 变量
            battle_end_signal = False
            battle_end_signal_max_execute_time = 10
            # TODO 战斗状态存活检测
            # 初始化 返回主页面
            for i in range(4):
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['MAIN_RETURN_INDEX']
                )
            # 进入战斗选择页面
            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_CLICK_IN']
            )

            # 选关部分
            self.battle_selector(c_id, first_battle_signal)
            # 选关结束

            self.adb.get_screen_shoot('{}.png'.format(c_id), MAP_LOCATION['BATTLE_CLICK_AI_COMMANDER'])
            if self.adb.img_difference(
                    SCREEN_SHOOT_SAVE_PATH + "{}.png".format(c_id), STORAGE_PATH + "BATTLE_CLICK_AI_COMMANDER_TRUE.png"
            ) <= 0.8:
                self.shell_color.helper_text("[-] 代理指挥未设置，设置代理指挥")
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['BATTLE_CLICK_AI_COMMANDER']
                )
            else:
                self.shell_color.helper_text("[+] 代理指挥已设置")

            # 查看理智剩余
            self.adb.get_screen_shoot(
                file_name="strength.png", screen_range=MAP_LOCATION["BATTLE_INFO_STRENGTH_REMAIN"]
            )
            os.popen(
                "tesseract {} {}".format(
                    SCREEN_SHOOT_SAVE_PATH + "strength.png", SCREEN_SHOOT_SAVE_PATH + "1"
                )
            )
            self.__wait(3)
            with open(SCREEN_SHOOT_SAVE_PATH + "1.txt", 'r', encoding="utf8") as f:
                tmp = f.read()  #
                try:
                    self.CURRENT_STRENGTH = int(tmp.split("/")[0])
                    self.shell_color.helper_text("[+] 理智剩余 {}".format(self.CURRENT_STRENGTH))
                except Exception as e:
                    self.shell_color.failure_text("[!] {}".format(e))
                    self.CURRENT_STRENGTH -= 20

            if self.CURRENT_STRENGTH - LIZHI_CONSUME[c_id] < 0:
                strength_end_signal = True
                self.shell_color.failure_text("[!] 理智不足 退出战斗")
                continue
                # 理智不够退出战斗

            self.shell_color.info_text("[+] 开始战斗")
            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_CLICK_START_BATTLE']
            )
            self.__wait(3)
            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_CLICK_ENSURE_TEAM_INFO']
            )

            t = 0

            while not battle_end_signal:
                self.__wait(BATTLE_FINISH_DETECT)
                t += BATTLE_FINISH_DETECT
                self.shell_color.helper_text("[*] 战斗进行{}S 判断是否结束".format(t))
                self.adb.get_screen_shoot(
                    file_name="battle_end.png",
                    screen_range=MAP_LOCATION['BATTLE_INFO_BATTLE_END']
                )
                if self.adb.img_difference(
                        img1=SCREEN_SHOOT_SAVE_PATH + "battle_end.png",
                        img2=STORAGE_PATH + "BATTLE_INFO_BATTLE_END_TRUE.png"
                ) >= 0.8:
                    battle_end_signal = True
                battle_end_signal_max_execute_time -= 1
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['MAIN_RETURN_INDEX']
                )
                if battle_end_signal_max_execute_time < 1:
                    self.shell_color.failure_text("[!] 超过最大战斗时常，默认战斗结束")
                    self.restart()
                    battle_end_signal = True

            count += 1
            self.shell_color.info_text("[*] 当前战斗次数  {}".format(count))

            if count >= set_count:
                strength_end_signal = True

            if first_battle_signal:
                first_battle_signal = False

            self.shell_color.info_text("[-] 战斗结束 重新开始")

        return True

    def main_handler(self, battle_task_list=None):
        if battle_task_list == None:
            battle_task_list = OrderedDict()

        self.shell_color.warning_text("[*] 装在模块....")
        self.shell_color.warning_text("[+] 战斗模块...启动！")
        flag = False
        if battle_task_list.__len__() == 0:
            self.shell_color.failure_text("[!] ⚠ 任务清单为空")

        for c_id, count in battle_task_list.items():
            if c_id not in LIZHI_CONSUME.keys():
                raise IndexError("无此关卡")
            self.shell_color.helper_text("[+] 战斗-选择{}...启动！".format(c_id))
            flag = self.module_battle(c_id, count)

        if flag:
            self.shell_color.warning_text("[*] 所有模块执行完毕...无限休眠启动！")
            self.__wait(1024)
            self.shell_color.failure_text("[*] 休眠过度...启动自毁程序！")
            self.__del()
        else:
            self.shell_color.failure_text("[*] 未知模块异常...无限休眠启动！")
            self.__wait(1024)
            self.shell_color.failure_text("[*] 休眠过度...启动自毁程序！")
            self.__del()

    def restart(self):
        self.shell_color.failure_text("[!] 检测异常发生 重新唤醒所有模块")
        self.__del()
        self.__init__()
        self.shell_color.warning_text("[+] 正在唤醒...明日方舟...")
        self.module_login()
        self.main_handler()


if __name__ == '__main__':
    TASK_LIST = OrderedDict()
    # TASK_LIST["S2-1"] = 6
    # TASK_LIST["PR-A-1"] = 100
    TASK_LIST["SK-3"] = 5
    h = ArknightsHelper()
    h.main_handler(TASK_LIST)
