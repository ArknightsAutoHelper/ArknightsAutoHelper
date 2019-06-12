from ADBShell import ADBShell
from time import sleep
from Arknights.click_location import *
from collections import OrderedDict
from random import randint, uniform
from Arknights.BattleSelector import BattleSelector
from Arknights.flags import *
from Baidu_api import *
from Arknights.Binarization import binarization_image
from config import *

os.path.join(os.path.abspath('../'))


class ArknightsHelper(object):
    def __init__(self, current_strength=None, adb_host=None,
                 out_put=0, call_by_gui=False):
        '''
        :param current_strength:
        :param adb_host:
        :param out_put:  0 default with console
                          1 no out put
        '''
        if adb_host is None:
            adb_host = ADB_HOST
        self.adb = ADBShell(adb_host=adb_host)
        self.shell_color = ShellColor() if out_put == 0 else BufferColor()
        self.__is_game_active = False
        self.__call_by_gui = call_by_gui
        self.__rebase_to_null = " 1>nul 2>nul" if "win" in os.sys.platform else " 1>/dev/null 2>/dev/null &" \
            if enable_rebase_to_null else ""
        self.CURRENT_STRENGTH = 100
        self.selector = BattleSelector()
        self.ocr_active = True
        self.is_call_by_gui = call_by_gui
        # 为了让 GUI 启动快一些，这里关闭了激活ocr的选项以及确认游戏开启的设置
        if not call_by_gui:
            self.is_ocr_active(current_strength)

    def __ocr_check(self, file_path, save_path, option=None, change_image=True):
        """
        选择百度ocr识别，还是tesseract识别；以及图片二值化是否开启，
        :param file_path: ocr识别图片路径
        :param save_path: ocr结果保存路径，建议使用txt跟tesseract同一
        :param option: 对tesseract的命令传递
        :param change_image:是否进行二值化，默认使用二值化
        :return:
        """
        global enable_api
        if change_image:
            binarization_image(file_path)
        if enable_api:
            try:
                ocr(file_path, save_path + ".txt")
            except ConnectionError:
                self.shell_color.failure_text("[!] 百度API无法连接")
                enable_api = False
                self.shell_color.helper_text("继续使用tesseract")
                if option is not None:
                    option = " " + option
                os.popen(
                    "tesseract {} {}{}".format(file_path, save_path, option) + self.__rebase_to_null
                )
                self.__wait(3)
        else:
            if option is not None:
                option = " " + option
            os.popen(
                "tesseract {} {}{}".format(file_path, save_path, option) + self.__rebase_to_null
            )
            self.__wait(3)

    def is_ocr_active(self, current_strength):
        """
        启用ocr判断
        :param current_strength: 当前理智
        :return:
        """
        global enable_api
        self.__ocr_check(STORAGE_PATH + "OCR_TEST_1.png", SCREEN_SHOOT_SAVE_PATH + "ocr_test_result", "--psm 7",
                         change_image=False)
        try:
            with open(SCREEN_SHOOT_SAVE_PATH + "ocr_test_result.txt", 'r', encoding="utf8") as f:
                tmp = f.read()
                test_1 = int(tmp.split("/")[0])
                if test_1 == 51:
                    self.ocr_active = True
                else:
                    # 如果启动了api检测失误的话，关闭api
                    if enable_api:
                        enable_api = False
                    self.shell_color.failure_text("[!] OCR 模块识别错误...装载初始理智值")
                    if current_strength is not None:
                        self.CURRENT_STRENGTH = current_strength
                    else:
                        self.shell_color.failure_text("[!] 未装载初始理智值，请在初始化Ark nights助手时候赋予初值")
                        if not self.is_call_by_gui:
                            exit(0)
                        else:
                            return False
        except Exception as e:
            self.shell_color.failure_text("[!] OCR 模块未检测...装载初始理智值")
            if current_strength is not None:
                self.CURRENT_STRENGTH = current_strength
            else:
                self.shell_color.failure_text("[!] 未装载初始理智值，请在初始化Ark nights助手时候赋予初值")
                if not self.is_call_by_gui:
                    exit(0)
                else:
                    return False

    def __del(self):
        self.adb.ch_tools("shell")
        self.adb.ch_abd_command("am force-stop {}".format(ArkNights_PACKAGE_NAME))
        self.adb.run_cmd()

    def destroy(self):
        self.__del()

    def __check_apk_info_active(self):
        """
        IT IS JUST A HELPER FUNCTION
        :return:
        """
        self.adb.ch_tools("shell")
        self.adb.ch_abd_command("dumpsys window windows | findstr \"Current\" > {}"
                                .format(STORAGE_PATH + "package.txt"))
        self.adb.run_cmd(DEBUG_LEVEL=0)

    def check_game_active(self):
        '''
        该命令是启动 官服的 明日方舟的函数
        在之后的GUI里调用。启动脚本的时候不调用了。默认你已经打开了
        :return:
        '''
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
    def __wait(n=10, MANLIKE_FLAG=True):
        """
        n的+-随机值服从均匀分布
        :param n:
        :param MANLIKE_FLAG:
        :return:
        """
        if MANLIKE_FLAG:
            m = uniform(0, 0.3)
            n = uniform(n - m * 0.5 * n, n + m * n)
            sleep(n)
        else:
            sleep(n)

    def __simulate_man(self):
        """
        模仿人操作，给检测机制提供一些困扰
        :return:
        """
        action = randint(1, 4)
        if action == 1:
            pass
        elif action == 2:
            pass
        elif action == 3:
            pass
        elif action == 4:
            pass

    def module_login(self):
        # self.__wait(SECURITY_WAIT)
        self.adb.get_mouse_click(
            XY=CLICK_LOCATION['LOGIN_QUICK_LOGIN']
        )
        self.__wait(BIG_WAIT)
        self.adb.get_mouse_click(
            XY=CLICK_LOCATION['LOGIN_START_WAKEUP']
        )
        self.__wait(BIG_WAIT)

    def module_battle_slim(self, c_id, set_count=1000, set_ai=False, **kwargs):
        """
        简单的战斗模式，请参考 Arknights README.md 中的使用方法调用
        该模块 略去了选关部分，直接开始打
        :param c_id: 关卡 ID
        :param set_count: 设置总次数
        :param set_ai: 是否设置代理指挥，默认没有设置
                        True 的时候，系统不会判断 AI 是否设置
                        False 的时候，系统会判断 AI 是否设置，所以省略不写该参数事一个比较保险的选择
        扩展参数
        :param sub: 是否是子程序。（是否为module_battle所调用的)
        :param auto_close: 是否自动关闭，默认为 False
        :param self_fix: 是否自动修复，默认为 False
                            该参数如果设置为 True 会在安装OCR模块且获取理智失败的情况下进入DEBUG逻辑
                            目前只支持不小心点到素材页面导致卡死的状况
        :param MAX_TIME: 最大迭代次数，默认为config的设置
                            该次数 * 14 S  + 60 得到每次战斗的最长时间
                            建议自定义这个数值，如果出现一定失误，超出最大判断次数后有一定的自我修复能力
        :return:
            True  当且仅当所有战斗计数达到设定值的时候
            False 当且仅当理智不足的时候
        """
        if "sub" in kwargs.keys():
            sub = kwargs['sub']
        else:
            sub = False
        if "auto_close" in kwargs.keys():
            auto_close = kwargs['auto_close']
        else:
            auto_close = True
        if "self_fix" in kwargs.keys():
            self_fix = kwargs['self_fix']
        else:
            self_fix = False
        if not sub:
            self.shell_color.helper_text("[+] 战斗-选择{}...启动！".format(c_id))
        if not set_ai:
            self.set_ai_commander()

        strength_end_signal = False
        count = 0
        while not strength_end_signal:
            # 初始化 变量
            battle_end_signal = False
            if "MAX_TIME" in kwargs.keys():
                battle_end_signal_max_execute_time = kwargs["MAX_TIME"]
            else:
                battle_end_signal_max_execute_time = BATTLE_END_SIGNAL_MAX_EXECUTE_TIME
            # 查看理智剩余部分
            strength_end_signal = not self.check_current_strength(c_id, self_fix)
            if strength_end_signal:
                return True
            # 查看理智剩余部分结束

            self.shell_color.info_text("[+] 开始战斗")
            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_CLICK_START_BATTLE'], FLAG=FLAGS_START_BATTLE_BIAS
            )
            self.__wait(4, False)
            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_CLICK_ENSURE_TEAM_INFO'], FLAG=FLAGS_ENSURE_TEAM_INFO_BIAS,
            )
            t = 0

            while not battle_end_signal:
                # 先打个60S，不检测
                if t == 0:
                    self.__wait(60)
                    t += 60
                else:
                    self.__wait(BATTLE_FINISH_DETECT)
                t += BATTLE_FINISH_DETECT
                self.shell_color.helper_text("[*] 战斗进行{}S 判断是否结束".format(t))
                # 升级的情况
                self.adb.get_screen_shoot(
                    file_name="level_up_real_time.png",
                    screen_range=MAP_LOCATION['BATTLE_INFO_LEVEL_UP']
                )
                level_up_signal = False
                level_up_num = 0
                # 检测是否启动ocr检查升级情况
                if enable_ocr_check_update:
                    self.__ocr_check(SCREEN_SHOOT_SAVE_PATH + "level_up_real_time.png",
                                     SCREEN_SHOOT_SAVE_PATH + "1",
                                     "--psm 7 -l chi_sim")
                    level_up_text = "等级提升"
                    f = open(SCREEN_SHOOT_SAVE_PATH + "1.txt", 'r', encoding="utf8")
                    tmp = f.readline()
                    if level_up_text in tmp:
                        level_up_signal = True
                else:
                    level_up_num = self.adb.img_difference(img1=SCREEN_SHOOT_SAVE_PATH + "level_up_real_time.png",
                                                           img2=STORAGE_PATH + "BATTLE_INFO_BATTLE_END_LEVEL_UP.png")
                if level_up_num > .7 or level_up_signal:
                    battle_end_signal = True
                    self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
                    self.adb.shell_color.helper_text("[*] 检测到升级！")
                    self.adb.get_mouse_click(
                        XY=CLICK_LOCATION['CENTER_CLICK'], FLAG=(200, 150)
                    )
                    self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
                    self.adb.get_mouse_click(
                        XY=CLICK_LOCATION['CENTER_CLICK'], FLAG=(200, 150)
                    )
                    self.__wait(SMALL_WAIT, MANLIKE_FLAG=True)
                else:
                    # 检测游戏是否结束
                    self.adb.get_screen_shoot(
                        file_name="battle_end.png",
                        screen_range=MAP_LOCATION['BATTLE_INFO_BATTLE_END']
                    )
                    end_num = 0
                    end_signal = False

                    if enable_ocr_check_end:
                        self.__ocr_check(SCREEN_SHOOT_SAVE_PATH + "battle_end.png",
                                         SCREEN_SHOOT_SAVE_PATH + "1",
                                         "--psm 7 -l chi_sim")
                        end_text = "行动结束"
                        f = open(SCREEN_SHOOT_SAVE_PATH + "1.txt", 'r', encoding="utf8")
                        tmp = f.readline()
                        if end_text in tmp:
                            end_signal = True
                    else:
                        end_num = self.adb.img_difference(
                            img1=SCREEN_SHOOT_SAVE_PATH + "battle_end.png",
                            img2=STORAGE_PATH + "BATTLE_INFO_BATTLE_END_TRUE.png")

                    if end_num >= 0.8 or end_signal:
                        battle_end_signal = True
                        self.adb.get_mouse_click(
                            XY=CLICK_LOCATION['CENTER_CLICK'], FLAG=(200, 150)
                            # 点到了经验尝试降低从（200, 200）降低（200, 150）
                        )
                    else:
                        battle_end_signal_max_execute_time -= 1
                    if battle_end_signal_max_execute_time < 1:
                        self.shell_color.failure_text("[!] 超过最大战斗时常")  # 推测BUG发生，启动自检测模块")
                        battle_end_signal = True

            count += 1
            self.shell_color.info_text("[*] 当前战斗次数  {}".format(count))

            if count >= set_count:
                strength_end_signal = True
            self.shell_color.info_text("[-] 战斗结束 重新开始")
            self.__wait(10, MANLIKE_FLAG=True)

        if not sub:
            if auto_close:
                self.shell_color.helper_text("[+] 简略模块结束，系统准备退出".format(c_id))
                self.__wait(120, False)
                self.__del()
            else:
                self.shell_color.helper_text("[+] 简略模块结束")
                return True
        else:
            self.shell_color.helper_text("[+] 当前任务清单 {} 结束，准备执行下一任务".format(c_id))
            return True

    def __check_is_on_setting(self):
        """
        检查是否在设置页面
        :return: True 如果在设置页面
        """
        self.adb.get_screen_shoot(
            'is_setting.png', MAP_LOCATION['INDEX_INFO_IS_SETTING']
        )
        if enable_ocr_debugger:
            self.__ocr_check(SCREEN_SHOOT_SAVE_PATH + "is_setting.png",
                             SCREEN_SHOOT_SAVE_PATH + "1",
                             "--psm 7 -l chi_sim")
            end_text = "设置"
            f = open(SCREEN_SHOOT_SAVE_PATH + "1.txt", 'r', encoding="utf8")
            tmp = f.readline()
            if end_text in tmp:
                return True
            else:
                return False
        else:
            if self.adb.img_difference(
                    img1=STORAGE_PATH + "INDEX_INFO_IS_SETTING.png",
                    img2=SCREEN_SHOOT_SAVE_PATH + "is_setting.png"
            ) > .85:
                return True
            else:
                return False

    def module_battle(self, c_id, set_count=1000):
        """
            保留 first_battle_signal 尽管这样的代码有些冗余但是可能会在之后用到。
        :param c_id:
        :param set_count:
        :return:
        """
        self.__wait(3, MANLIKE_FLAG=False)
        self.selector.id = c_id
        # 初始化 返回主页面
        for i in range(3):
            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['MAIN_RETURN_INDEX'], FLAG=None
            )
        if self.__check_is_on_setting():
            self.shell_color.helper_text("[=] 不小心点到设置了，点击返回")
            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['MAIN_RETURN_INDEX'], FLAG=None
            )
        # 进入战斗选择页面
        self.adb.get_mouse_click(
            XY=CLICK_LOCATION['BATTLE_CLICK_IN']
        )

        # 选关部分
        self.battle_selector(c_id)
        # 选关结束
        self.module_battle_slim(c_id, set_count=set_count, set_ai=False, sub=True,
                                self_fix=self.ocr_active)
        return True

    def main_handler(self, battle_task_list=None):
        if battle_task_list is None:
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
            self.selector.id = c_id
            flag = self.module_battle(c_id, count)
            # flag = self.module_battle_for_test(c_id, count)

        if flag:
            if not self.__call_by_gui:
                self.shell_color.warning_text("[*] 所有模块执行完毕...无限休眠启动！")
                self.__wait(1024)
                self.shell_color.failure_text("[*] 休眠过度...启动自毁程序！")
                self.__del()
            else:
                self.shell_color.warning_text("[*] 所有模块执行完毕...！")
        else:
            if not self.__call_by_gui:
                self.shell_color.failure_text("[*] 未知模块异常...无限休眠启动！")
                self.__wait(1024)
                self.shell_color.failure_text("[*] 休眠过度...启动自毁程序！")
                self.__del()
            else:
                self.shell_color.failure_text("[*] 未知模块异常...系统体现结束")

    def restart(self):
        """
        由于重启的逻辑比较困难，暂时废弃这里的功能
        :return:
        """
        self.shell_color.failure_text("[!] 检测异常发生 重新唤醒所有模块")
        self.__del()
        self.__init__()
        self.shell_color.warning_text("[+] 正在唤醒...明日方舟...")
        self.module_login()
        self.main_handler()

    def set_ai_commander(self):
        self.adb.get_screen_shoot('is_ai.png', MAP_LOCATION['BATTLE_CLICK_AI_COMMANDER'])
        if self.adb.img_difference(
                SCREEN_SHOOT_SAVE_PATH + "is_ai.png",
                STORAGE_PATH + "BATTLE_CLICK_AI_COMMANDER_TRUE.png"
        ) <= 0.8:
            self.shell_color.helper_text("[-] 代理指挥未设置，设置代理指挥")
            self.adb.get_mouse_click(
                XY=CLICK_LOCATION['BATTLE_CLICK_AI_COMMANDER']
            )
        else:
            self.shell_color.helper_text("[+] 代理指挥已设置")

    def __check_current_strength(self):
        """
        简易的模式，在debug后重新启动
        :return:
        """
        assert self.ocr_active
        sleep(4)
        self.adb.get_screen_shoot(
            file_name="strength.png", screen_range=MAP_LOCATION["BATTLE_INFO_STRENGTH_REMAIN"]
        )
        self.__ocr_check(SCREEN_SHOOT_SAVE_PATH + "strength.png", SCREEN_SHOOT_SAVE_PATH + "1", "--psm 7")
        with open(SCREEN_SHOOT_SAVE_PATH + "1.txt", 'r', encoding="utf8") as f:
            tmp = f.read()  #
            try:
                self.CURRENT_STRENGTH = int(tmp.split("/")[0])
                self.shell_color.helper_text("[+] 理智剩余 {}".format(self.CURRENT_STRENGTH))
                return True
            except Exception as e:
                self.shell_color.failure_text("[!] {}".format(e))
                return False

    def __check_current_strength_debug(self):
        # 查看是否在素材页面
        self.shell_color.helper_text("[+] 启动自修复模块,检查是否停留在素材页面")
        self.adb.get_screen_shoot(
            file_name="debug.png",
            screen_range=MAP_LOCATION['BATTLE_DEBUG_WHEN_OCR_ERROR']
        )
        if enable_ocr_debugger:
            self.__ocr_check(SCREEN_SHOOT_SAVE_PATH + "debug.png",
                             SCREEN_SHOOT_SAVE_PATH + "debug",
                             "--psm 7 -l chi_sim")
            end_text = "首次掉落"
            f = open(SCREEN_SHOOT_SAVE_PATH + "debug.txt", 'r', encoding="utf8")
            tmp = f.readline()
            if end_text in tmp:
                self.shell_color.helper_text("[$] 检测 BUG 成功，系统停留在素材页面，请求返回...")
                self.adb.get_mouse_click(CLICK_LOCATION['MAIN_RETURN_INDEX'], FLAG=None)
                self.__check_current_strength()
            else:
                self.shell_color.failure_text("[-] 检测 BUG 失败，系统将继续执行任务")
        else:
            if self.adb.img_difference(
                    img1=SCREEN_SHOOT_SAVE_PATH + "debug.png",
                    img2=STORAGE_PATH + "BATTLE_DEBUG_CHECK_LOCATION_IN_SUCAI.png"
            ) > 0.75:
                self.shell_color.helper_text("[$] 检测 BUG 成功，系统停留在素材页面，请求返回...")
                self.adb.get_mouse_click(CLICK_LOCATION['MAIN_RETURN_INDEX'], FLAG=None)
                self.__check_current_strength()
            else:
                self.shell_color.failure_text("[-] 检测 BUG 失败，系统将继续执行任务")

    def check_current_strength(self, c_id, self_fix=False):
        if self.ocr_active:
            sleep(4)
            self.adb.get_screen_shoot(
                file_name="strength.png", screen_range=MAP_LOCATION["BATTLE_INFO_STRENGTH_REMAIN"]
            )
            self.__ocr_check(SCREEN_SHOOT_SAVE_PATH + "strength.png", SCREEN_SHOOT_SAVE_PATH + "1", "--psm 7")
            with open(SCREEN_SHOOT_SAVE_PATH + "1.txt", 'r', encoding="utf8") as f:
                tmp = f.read()  #
                try:
                    self.CURRENT_STRENGTH = int(tmp.split("/")[0])
                    self.shell_color.helper_text("[+] 理智剩余 {}".format(self.CURRENT_STRENGTH))
                except Exception as e:
                    self.shell_color.failure_text("[!] {}".format(e))
                    if self_fix:
                        self.__check_current_strength_debug()
                    else:
                        self.CURRENT_STRENGTH -= LIZHI_CONSUME[c_id]
        else:
            self.CURRENT_STRENGTH -= LIZHI_CONSUME[c_id]
            self.shell_color.warning_text("[*] OCR 模块为装载，系统将直接计算理智值")
            self.__wait(TINY_WAIT)
            self.shell_color.helper_text("[+] 理智剩余 {}".format(self.CURRENT_STRENGTH))

        if self.CURRENT_STRENGTH - LIZHI_CONSUME[c_id] < 0:
            self.shell_color.failure_text("[!] 理智不足 退出战斗")
            return False
        else:
            return True
            # 理智不够退出战斗

    def battle_selector(self, c_id, first_battle_signal=True):
        mode = self.selector.id_checker()
        if mode == 1:
            if first_battle_signal:
                self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK']
                )

                # 拖动到正确的地方
                if c_id[0] in MAIN_TASK_CHAPTER_SWIPE.keys() or c_id[1] in MAIN_TASK_CHAPTER_SWIPE.keys():
                    if c_id[0].isnumeric():
                        x = MAIN_TASK_CHAPTER_SWIPE[c_id[0]]
                    else:
                        x = MAIN_TASK_CHAPTER_SWIPE[c_id[1]]
                    self.shell_color.helper_text("[-] 拖动%{}次".format(x))
                    for x in range(0, x):
                        self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT'], FLAG=FLAGS_SWIPE_BIAS_TO_RIGHT)
                        self.__wait(MEDIUM_WAIT)

                # 章节选择
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
                # 章节选择结束
                # 拖动
                self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)
                sleep(SMALL_WAIT)
                self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)
                sleep(SMALL_WAIT)
                self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)

                # 拖动到正确的地方
                if c_id in MAIN_TASK_BATTLE_SWIPE.keys():
                    x = MAIN_TASK_BATTLE_SWIPE[c_id]
                    self.shell_color.helper_text("[-] 拖动%{}次".format(x))
                    for x in range(0, x):
                        self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT'], FLAG=FLAGS_SWIPE_BIAS_TO_RIGHT)
                        # self.__wait(MEDIUM_WAIT)
                        sleep(5)
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MAIN_TASK_{}'.format(c_id)]
                )

            else:
                sleep(5)

        elif mode == 2:
            try:
                X = DAILY_LIST[mode][self.selector.get_week()][c_id[0:2]]
            except Exception as e:
                self.shell_color.failure_text(e.__str__() + '\tclick_location 文件配置错误')
                X = None
                exit(0)
            if first_battle_signal:
                self.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'], FLAG=FLAGS_SWIPE_BIAS_TO_LEFT)
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION']
                )
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION_{}'.format(X)]
                )
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION_X-{}'.format(c_id[-1])]
                )
            else:
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_MATERIAL_COLLECTION_X-{}'.format(c_id[-1])]
                )
        elif mode == 3:
            try:
                X = DAILY_LIST[mode][self.selector.get_week()][c_id[3]]
            except Exception as e:
                self.shell_color.failure_text(e.__str__() + '\tclick_location 文件配置错误')
                X = None
                exit(0)
            if first_battle_signal:
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH']
                )
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH_PR-{}'.format(X)]
                )
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH_PR-X-{}'.format(c_id[-1])]
                )
            else:
                self.adb.get_mouse_click(
                    XY=CLICK_LOCATION['BATTLE_SELECT_CHIP_SEARCH_PR-X-{}'.format(c_id[-1])]
                )
