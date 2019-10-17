import os

'''
这是一个示例文件，请不要直接运行。
'''

'''
main_handler 的启动模式
'''
from Arknights import ArknightsHelper
from collections import OrderedDict

TASK_LIST = OrderedDict()
TASK_LIST['CE-5'] = 5
TASK_LIST['4-8'] = 10
Ark = ArknightsHelper()
Ark.main_handler(task_list=TASK_LIST,clear_tasks=True)

# TASK_LIST['战斗章节'] = 战斗次数
# True代表在任务完成后清理每日任务，False不清理

'''
main_battle_slim 的启动模式
'''
from Arknights import ArknightsHelper
Ark = ArknightsHelper()
# 传递c_id可以确保页面正确
Ark.module_battle_slim(c_id='CE-5', set_count=14, set_ai=True)
# 不传递c_id可以自动检测消耗，本功能暂不支持Shell
Ark.module_battle_slim(set_count=7, self_detect=True)

# 如果没有安装OCR模块，请在初始化ArknightsHelper()类时告知系统初值，就像这样子
from Arknights import ArknightsHelper
Ark = ArknightsHelper(123)
Ark.module_battle_slim(c_id='4-8', set_count=14, set_ai=True)

# c_id 是战斗章节
# set_count 是战斗次数

'''
关于多开器的用法
请在初始化前，带入 ADB_HOST。如果你不知道你的 ADB_HOST 是多少，就带入一个空值。系统会自动检测,并让你手动选择。

    [!] 检测到多台设备，根据 ADB_HOST 参数将自动选择设备
    [*]  0    127.0.0.1:62025    device
    [*]  1    127.0.0.1:62001    device
    系统未检测到设备名称，请根据上述内容自行输入数字并选择
    >0
    127.0.0.1:62025

请不要直接带入和你另一个设备同样的ADB_HOST，这样会导致连到另一台设备上去
'''
ADB_HOST = "127.0.0.1:62025"
# OR ADB_HOST = ""
Ark = ArknightsHelper(adb_host=ADB_HOST)
Ark.module_battle_slim(c_id='CE-3', set_count=50, set_ai=True)
