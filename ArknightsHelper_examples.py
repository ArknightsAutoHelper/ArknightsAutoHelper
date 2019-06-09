import os

'''
在启动之前，请修改config/config.py下的一些参数

    [⚠] 这个路径很重要 ADB_ROOT 
            这个路径为你 安卓模拟器adb工具的路径 （一般安卓电脑模拟器都有，所以设置成模拟器路径即可）
    [⚠] 这个路径很重要 STORAGE_PATH 
            也就是目录底下的 storage 文件夹，请确保是绝对路径
    [⚠] 这个路径重要 SCREEN_SHOOT_SAVE_PATH
            也就是目录底下的 screen_shoot 文件夹，用来存放一些截图

    为啥这些路径我都要写绝对路径呢...因为之后会有 os.chdir()的操作，所以建议全部写成绝对路径，就像如下所示：
'''
# ADB_ROOT = r"D:\Program Files\Nox\bin"
# SCREEN_SHOOT_SAVE_PATH = "D:\\python_box\\shaobao_adb\\screen_shoot\\"
# STORAGE_PATH = "D:\\python_box\\shaobao_adb\\storage\\"
'''
在config.config 下还有一个参数，为ADB_HOST 夜深模拟器第一个模拟器的HOST 是 127.0.0.1:62001
如果是其他模拟器，则需要修改

由于该脚本没有做适配，仅仅测试了夜神模拟器，其他模拟器请自行测试。
另外，请确定夜神模拟器的分辨率是否调整为1280*720
在运行过程中，请不要对模拟器进行缩放，以免造成不必要的麻烦

'''
# ADB_HOST = "127.0.0.1:62001"

from Arknights import ArknightsHelper
from collections import OrderedDict

'''
main_handler 的启动模式
'''

TASK_LIST = OrderedDict()
TASK_LIST['CE-5'] = 5
TASK_LIST['4-8'] = 10
Ark = ArknightsHelper()
Ark.main_handler(TASK_LIST)

'''
main_battle_slim 的启动模式
'''
Ark = ArknightsHelper()
Ark.module_battle_slim(c_id='CE-5', set_count=14, set_ai=True)
'''
如果没有安装OCR模块，请在初始化ArknightsHelper()类时告知系统初值，就像这样子
'''
Ark = ArknightsHelper(123)
Ark.module_battle_slim(c_id='4-8', set_count=14, set_ai=True)

'''
关于多开器的用法
请在初始化前，带入 ADB_HOST。如果你不知道你的 ADB_HOST 是多少，就带入一个空值。系统会自动检测,并让你手动选择。

    [!] 检测到多台设备，根据 ADB_HOST 参数将自动选择设备
    [*]  0	127.0.0.1:62025	device
    [*]  1	127.0.0.1:62001	device
    系统未检测到设备名称，请根据上述内容自行输入数字并选择
    >0
    127.0.0.1:62025

请不要直接带入和你另一个设备同样的ADB_HOST，这样会导致连到另一台设备上去
'''
ADB_HOST = "127.0.0.1:62025"
# OR ADB_HOST = ""
Ark = ArknightsHelper(adb_host=ADB_HOST)
Ark.module_battle_slim(c_id='CE-3', set_count=50, set_ai=True)
