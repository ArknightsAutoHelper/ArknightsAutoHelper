import os
'''
如果需要二次开发，请修改 
    
    [⚠] 这个路径很重要 ADB_ROOT 
            这个路径为你 安卓模拟器adb工具的路径 （一般安卓电脑模拟器都有，所以设置成模拟器路径即可）
    [⚠] 这个路径很重要 STORAGE_PATH 
            也就是目录底下的 storage 文件夹，请确保是绝对路径
    [⚠] 这个路径重要 SCREEN_SHOOT_SAVE_PATH
            也就是目录底下的 screen_shoot 文件夹，用来存放一些截图
    
    为啥这些路径我都要写绝对路径呢...因为之后会有 os.chdir()的操作，所以建议全部写成绝对路径，就像如下所示：
'''
ADB_ROOT = r"D:\Program Files\Nox\bin"
SCREEN_SHOOT_SAVE_PATH = "D:\\python_box\\shaobao_adb\\screen_shoot\\"
STORAGE_PATH = "D:\\python_box\\shaobao_adb\\storage\\"

ADB_HOST = "127.0.0.1:62001"

# arknights INFO
ArkNights_PACKAGE_NAME = "com.hypergryph.arknights"
ArkNights_ACTIVITY_NAME = "com.u8.sdk.U8UnityContext"

# manlike action
FLAGS_CLICK_BIAS_TINY = (3, 3)


class ShellColor(object):
    def __init__(self):
        self.H_HEADER = '\033[95m'
        self.H_OK_BLUE = '\033[94m'
        self.H_OK_GREEN = '\033[96m'
        self.H_WARNING = '\033[93m'
        self.H_FAIL = '\033[31m'
        self.E_END = '\033[0m'
        self.E_BOLD = '\033[1m'
        self.E_UNDERLINE = '\033[4m'

    def warning_text(self, string):
        print(self.H_WARNING + string + self.E_END)

    def info_text(self, string):
        print(self.H_OK_BLUE + string + self.E_END)

    def failure_text(self, string):
        print(self.H_FAIL + string + self.E_END)

    def helper_text(self, string):
        print(self.H_OK_GREEN + string + self.E_END)

    def run_test(self, string="[*] DEBUG COLOR"):
        self.warning_text(string)
        self.info_text(string)
        self.failure_text(string)
        self.helper_text(string)

# if __name__ == '__main__':
#     ShellColor().run_test()
