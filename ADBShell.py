import os
from config import ADB_ROOT, ADB_HOST, SCREEN_SHOOT_SAVE_PATH, ShellColor, FLAGS_CLICK_BIAS_TINY
from PIL import Image
from time import sleep
from random import randint
from numpy import average, dot, linalg


class ADBShell(object):
    def __init__(self):
        self.SCREEN_SHOOT_SAVE_PATH = SCREEN_SHOOT_SAVE_PATH
        os.chdir(ADB_ROOT)
        self.ADB_ROOT = ADB_ROOT
        self.ADB_HOST = ADB_HOST
        self.__command = "adb {tools} {command}"
        self.__buffer = ""
        self.shell_color = ShellColor()
        self.__adb_tools = ""
        self.__adb_command = ""
        self.__adb_connect()

    def __adb_connect(self):
        self.__adb_tools = "connect"
        self.__adb_command = self.ADB_HOST
        self.run_cmd(DEBUG_LEVEL=1)
        if "device" in self.__buffer or "already connected to {}".format(self.ADB_HOST) in self.__buffer:
            self.shell_color.warning_text("[+] Connect to DEVICE {}  Success".format(self.ADB_HOST))
        else:
            self.shell_color.failure_text("[-] Connect to DEVICE {}  Failed".format(self.ADB_HOST))

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
            print(self.shell_color.H_OK_BLUE +
                  self.__command.format(
                      tools=self.__adb_tools,
                      command=self.__adb_command) + self.shell_color.E_END
                  )

            self.__buffer = os.popen(self.__command.format(
                tools=self.__adb_tools,
                command=self.__adb_command
            )).read()
            self.get_buffer()
        elif DEBUG_LEVEL == 2:
            print(self.shell_color.H_OK_BLUE +
                  self.__command.format(
                      tools=self.__adb_tools,
                      command=self.__adb_command) + self.shell_color.E_END
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
            print(self.shell_color.H_OK_BLUE + "[+] DEBUG INFO " + self.shell_color.E_END + "\n" +
                  self.__buffer[0:n])
        elif BUFFER_OUT_PUT_LEVEL == -1:
            print(self.shell_color.H_FAIL + "[+] DEBUG WARNING " + self.shell_color.E_END + "\n" +
                  self.__buffer[0:n])
        elif BUFFER_OUT_PUT_LEVEL == 0:
            print(self.shell_color.H_OK_GREEN + "[+] DEBUG HELPER " + self.shell_color.E_END + "\n" +
                  self.__buffer[0:n])

    @staticmethod
    def get_sub_screen(file_name, screen_range):
        i = Image.open(SCREEN_SHOOT_SAVE_PATH + file_name)
        i.crop(
            (
                screen_range[0][0],
                screen_range[0][1],
                screen_range[0][0] + screen_range[1][0],
                screen_range[0][1] + screen_range[1][1]
            )
        ).save(SCREEN_SHOOT_SAVE_PATH + file_name)

    def get_screen_shoot(self, file_name="1.png", screen_range=None):
        sleep(1)
        if screen_range is None:
            screen_range = []
        self.__adb_tools = "shell"
        self.__adb_command = "/system/bin/screencap -p /sdcard/screenshot.png"
        self.run_cmd(1)
        self.__adb_tools = "pull"
        self.__adb_command = "/sdcard/screenshot.png {}".format(self.SCREEN_SHOOT_SAVE_PATH + file_name)
        self.run_cmd(1)
        self.__adb_tools = "shell"
        self.__adb_command = "rm /sdcard/screen.png"
        self.run_cmd(1)
        if screen_range.__len__() == 2:
            self.get_sub_screen(file_name, screen_range)

    def get_mouse_swipe(self, XY_mXmY=None, FLAG=None):
        sleep(1)
        assert type(XY_mXmY).__name__ == "tuple"
        assert XY_mXmY.__len__() == 2
        XY, mXmY = XY_mXmY
        # XY = list(XY[0], XY[1])
        # mXmY = list(mXmY[0], mXmY[1])
        # if FLAG is not None:
        #     FLAG_XY, FLAG_mXmY = FLAG
        #     XY[0] = XY[0] + randint(-FLAG_XY[0], FLAG_XY[0])
        #     XY[1] = XY[0] + randint(-FLAG_XY[1], FLAG_XY[1])
        #     mXmY[0] = mXmY[0] + randint(-FLAG_mXmY[0], FLAG_mXmY[0])
        #     mXmY[1] = mXmY[1] + randint(-FLAG_mXmY[1], FLAG_mXmY[1])
        self.__adb_tools = "shell"
        self.__adb_command = "input swipe {X1} {Y1} {X2} {Y2}".format(
            X1=XY[0], Y1=XY[1], X2=XY[0] + mXmY[0], Y2=XY[1] + mXmY[1]
        )
        self.run_cmd(DEBUG_LEVEL=0)

    def get_mouse_click(self, XY=None, FLAG=None):
        # sleep(10)
        self.__adb_tools = "shell"
        if FLAG is not None:
            # self.shell_color.info_text(XY.__str__())
            # self.__adb_tools = "shell"
            self.__adb_command = "input tap {} {}".format(XY[0] + randint(-FLAG[0], FLAG[0]),
                                                          XY[1] + randint(-FLAG[1], FLAG[1]))
            # self.run_cmd(DEBUG_LEVEL=0)
        else:
            # self.shell_color.info_text(XY.__str__())
            # self.__adb_tools = "shell"
            self.__adb_command = "input tap {} {}".format(XY[0] + randint(-1, 1),
                                                          XY[1] + randint(-1, 1))
            # self.run_cmd(DEBUG_LEVEL=0)
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
                sum1 += 1 - float(abs(hist1[i] - hist2[i])) / max(hist1[i], hist2[i])
        return sum1 / len(hist1)

    def ch_tools(self, tools):
        self.__adb_tools = tools

    def ch_abd_command(self, command):
        self.__adb_command = command


if __name__ == '__main__':
    a = ADBShell()
    a.mv_file("shaobao.pcap", RM=True)
