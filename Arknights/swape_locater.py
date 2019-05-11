'''
在这里做一些测试，包括拖动后的点击位置获取操作

'''
from Arknights.click_location import *
from time import sleep
from ADBShell import ADBShell

adb = ADBShell()
adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'])
adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT'])
sleep(3)
# ark.adb.get_mouse_click(CLICK_LOCATION["BATTLE_SELECT_MAIN_TASK_4-6"])
sleep(200)
