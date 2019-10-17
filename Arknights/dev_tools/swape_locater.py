'''
在这里做一些测试，包括拖动后的点击位置获取操作

'''
from time import sleep

from Arknights import ArknightsHelper
from Arknights.click_location import *

ark = ArknightsHelper()
ark.adb.touch_tap(
    XY=CLICK_LOCATION['BATTLE_CLICK_START_BATTLE'], offsets=FLAGS_START_BATTLE_BIAS
)

# ark.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'])
# ark.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'])
#
# ark.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT'])
#
# ark.adb.get_mouse_click(CLICK_LOCATION["BATTLE_SELECT_MAIN_TASK_4-6"])
ark.adb.touch_tap((91, 159))
# ark.adb.get_mouse_click(MAIN_TASK_RELOCATE["4-7"])
sleep(3)

# ark.adb.get_mouse_click(CLICK_LOCATION["BATTLE_SELECT_MAIN_TASK_4-6"])
