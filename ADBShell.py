import logging.config
import os
from random import randint
from time import sleep

from PIL import Image

from config import ADB_ROOT, ADB_HOST, SCREEN_SHOOT_SAVE_PATH, ShellColor, CONFIG_PATH

# from numpy import average, dot, linalg


logging.config.fileConfig(CONFIG_PATH + 'logging.ini')
logger = logging.getLogger('ADBSHell')


class ADBShell(object):
    def __init__(self, adb_host=ADB_HOST):
        # os.chdir(ADB_ROOT)
        self.ADB_ROOT = ADB_ROOT
        self.ADB_HOST = adb_host
        self.__buffer = ""
        self.shell_log = ShellColor()
        self.__adb_tools = ""
        self.__adb_command = ""
        self.DEVICE_NAME = self.__adb_device_name_detector()
        if "win32" in os.sys.platform:
            self.__command = "\"" + self.ADB_ROOT + "\\adb.exe\" -s " + self.DEVICE_NAME + " {tools} {command} "
            self.SCREEN_SHOOT_SAVE_PATH = os.path.abspath(SCREEN_SHOOT_SAVE_PATH) + "\\"
        else:
            self.__command = self.ADB_ROOT + "/adb -s " + self.DEVICE_NAME + " {tools} {command} "
            self.SCREEN_SHOOT_SAVE_PATH = os.path.abspath(SCREEN_SHOOT_SAVE_PATH) + "/"

    def __adb_device_name_detector(self):
        if "win32" in os.sys.platform:
            self.__command = "\"" + self.ADB_ROOT + \
                             "\\adb.exe\" {tools} {command}"

        else:
            self.__command = self.ADB_ROOT + "/adb {tools} {command}"
        self.__adb_tools = "devices"
        content = self.run_cmd(DEBUG_LEVEL=1).strip().split("\n")
        content.pop(0)
        if content.__len__() == 1:
            device_name = content[0].split("\t")[0]
        else:
            self.shell_log.helper_text("[!] 检测到多台设备，根据 ADB_HOST 参数将自动选择设备")
            device_name = ""
            for c in range(content.__len__()):
                print("[*]  " + c.__str__() + "\t" + content[c])
                if self.ADB_HOST == content[c].split("\t")[0]:
                    device_name = self.ADB_HOST
            if device_name == "":
                print("自动选择设备失败，请根据上述内容自行输入数字并选择")
                input_valid_flag = False
                num = "0"
                while not input_valid_flag:
                    num = input(">")
                    if num.isnumeric() and int(num) <= content.__len__():
                        input_valid_flag = True
                    else:
                        print("输入不合法，请重新输入")
                device_name = content[int(num)].split("\t")[0]
        self.shell_log.helper_text("[+] 确认设备名称\t" + device_name)
        return device_name

    def __adb_connect(self):
        self.__adb_tools = "connect"
        self.__adb_command = self.DEVICE_NAME
        self.run_cmd(DEBUG_LEVEL=1)
        if "device" in self.__buffer or "already connected to {}".format(self.DEVICE_NAME) in self.__buffer:
            self.shell_log.warning_text(
                "[+] Connect to DEVICE {}  Success".format(self.DEVICE_NAME))
        else:
            self.shell_log.failure_text(
                "[-] Connect to DEVICE {}  Failed".format(self.DEVICE_NAME))

    def run_cmd(self, DEBUG_LEVEL=2):
        """
        :param DEBUG_LEVEL:
            0 : cannot get any info
            1 : use get_buffer() to get info
            2 : print command and can use get_buffer() to get info
            3 : print command and print the return content
        :return:
        """
        if DEBUG_LEVEL == 3:
            print(self.shell_log.H_OK_BLUE +
                  self.__command.format(
                      tools=self.__adb_tools,
                      command=self.__adb_command) + self.shell_log.E_END
                  )

            self.__buffer = os.popen(self.__command.format(
                tools=self.__adb_tools,
                command=self.__adb_command
            )).read()
            self.get_buffer()
        elif DEBUG_LEVEL == 2:
            print(self.shell_log.H_OK_BLUE +
                  self.__command.format(
                      tools=self.__adb_tools,
                      command=self.__adb_command) + self.shell_log.E_END
                  )
            self.__buffer = os.popen(self.__command.format(
                tools=self.__adb_tools,
                command=self.__adb_command
            )).read()
        elif DEBUG_LEVEL == 1:
            self.__buffer = os.popen(self.__command.format(
                tools=self.__adb_tools,
                command=self.__adb_command
            )).read()
            return self.__buffer
        else:
            os.system(self.__command.format(
                tools=self.__adb_tools,
                command=self.__adb_command
            ))

    def get_buffer(self, n=1024, BUFFER_OUT_PUT_LEVEL=1):
        """
        :param n: buffer size default 1024 chars
        :param BUFFER_OUT_PUT_LEVEL:
            1 INFO - color blue
            0 HELPER - color green
            -1 WEARING - color red
        :return:
        """
        if BUFFER_OUT_PUT_LEVEL == 1:
            print(self.shell_log.H_OK_BLUE + "[+] DEBUG INFO " + self.shell_log.E_END + "\n" +
                  self.__buffer[0:n])
        elif BUFFER_OUT_PUT_LEVEL == -1:
            print(self.shell_log.H_FAIL + "[+] DEBUG WARNING " + self.shell_log.E_END + "\n" +
                  self.__buffer[0:n])
        elif BUFFER_OUT_PUT_LEVEL == 0:
            print(self.shell_log.H_OK_GREEN + "[+] DEBUG HELPER " + self.shell_log.E_END + "\n" +
                  self.__buffer[0:n])
        return self.__buffer[0:n]

    def get_sub_screen(self, file_name, screen_range, save_name=None):
        if save_name is None:
            save_name = file_name
        i = Image.open(self.SCREEN_SHOOT_SAVE_PATH + file_name)
        i.crop(
            (
                screen_range[0][0],
                screen_range[0][1],
                screen_range[0][0] + screen_range[1][0],
                screen_range[0][1] + screen_range[1][1]
            )
        ).save(self.SCREEN_SHOOT_SAVE_PATH + save_name)

    def get_screen_shoot(self, file_name="1.png", screen_range=None):
        sleep(1)
        if screen_range is None:
            screen_range = []
        self.__adb_tools = "shell"
        self.__adb_command = "/system/bin/screencap -p /sdcard/screenshot.png"
        self.run_cmd(1)
        self.__adb_tools = "pull"
        self.__adb_command = "/sdcard/screenshot.png \"{}\"".format(
            self.SCREEN_SHOOT_SAVE_PATH + file_name)
        self.run_cmd(1)
        self.__adb_tools = "shell"
        self.__adb_command = "rm /sdcard/screenshot.png"
        self.run_cmd(1)
        # print(self.SCREEN_SHOOT_SAVE_PATH + file_name)
        if screen_range.__len__() == 2:
            self.get_sub_screen(file_name, screen_range)

    def get_mouse_swipe(self, XY_mXmY=None, FLAG=None):
        sleep(1)
        XY, mXmY = XY_mXmY
        self.__adb_tools = "shell"
        logger.debug("滑动初始坐标:({},{}); 移动距离dX:{}, dy:{}".format(XY[0], XY[1], XY[0] + mXmY[0], XY[1] + mXmY[1]))
        self.__adb_command = "input swipe {X1} {Y1} {X2} {Y2}".format(
            X1=XY[0], Y1=XY[1], X2=XY[0] + mXmY[0], Y2=XY[1] + mXmY[1]
        )
        self.run_cmd(DEBUG_LEVEL=0)

    def get_mouse_click(self, XY=None, FLAG=None):
        # sleep(10)
        sleep(0.5)
        self.__adb_tools = "shell"
        if FLAG is not None:
            # self.shell_log.info_text(XY.__str__())
            # self.__adb_tools = "shell"
            fianal_XY_0 = XY[0] + randint(-FLAG[0], FLAG[0])
            fianal_XY_1 = XY[1] + randint(-FLAG[1], FLAG[1])
            # self.run_cmd(DEBUG_LEVEL=0)
        else:
            # self.shell_log.info_text(XY.__str__())
            # self.__adb_tools = "shell"
            fianal_XY_0 = XY[0] + randint(-1, 1)
            fianal_XY_1 = XY[1] + randint(-1, 1)
            # self.run_cmd(DEBUG_LEVEL=0)
        # print(self.__adb_command)
        # 如果你遇到了问题，可以把这百年输出并把日志分享到群里。
        logger.debug("点击坐标:({},{})".format(fianal_XY_0, fianal_XY_1))
        self.__adb_command = "input tap {} {}".format(fianal_XY_0,
                                                      fianal_XY_1)
        self.run_cmd(DEBUG_LEVEL=0)

    def mv_file(self, file_name, file_path="/sdcard/", RM=False):
        self.__adb_tools = "pull"
        self.__adb_command = "{} {}".format(
            file_path + file_name,
            SCREEN_SHOOT_SAVE_PATH + file_name
        )
        self.run_cmd(DEBUG_LEVEL=0)
        if RM:
            self.__adb_tools = "shell"
            self.__adb_command = "rm {}".format(file_path + file_name)

    @staticmethod
    def img_difference(img1, img2):
        img1 = Image.open(img1).convert('1')
        img2 = Image.open(img2).convert('1')
        hist1 = list(img1.getdata())
        hist2 = list(img2.getdata())
        sum1 = 0
        for i in range(len(hist1)):
            if hist1[i] == hist2[i]:
                sum1 += 1
            else:
                sum1 += 1 - \
                        float(abs(hist1[i] - hist2[i])) / max(hist1[i], hist2[i])
        return sum1 / len(hist1)

    def ch_tools(self, tools):
        self.__adb_tools = tools

    def ch_abd_command(self, command):
        self.__adb_command = command

#
# if __name__ == '__main__':
#     a = ADBShell()
