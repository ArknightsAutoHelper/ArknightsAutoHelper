'''
在这里做一些测试，包括拖动后的点击位置获取操作

'''
from Arknights import ArknightsHelper
from Arknights.click_location import SWIPE_LOCATION, CLICK_LOCATION
from time import sleep

ark = ArknightsHelper()
ark.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_LEFT'])
ark.adb.get_mouse_swipe(SWIPE_LOCATION['BATTLE_TO_MAP_RIGHT'])
sleep(3)
# ark.adb.get_mouse_click(CLICK_LOCATION["BATTLE_SELECT_MAIN_TASK_4-6"])
sleep(200)
