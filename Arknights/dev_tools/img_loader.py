from Arknights.click_location import MAP_LOCATION
from Arknights.base import ArknightsHelper
from config import *

ark = ArknightsHelper()
a = ark.adb.img_difference(
    img1=SCREEN_SHOOT_SAVE_PATH + "LEVEL_UP_TRUE.png",
    img2=STORAGE_PATH + "BATTLE_INFO_BATTLE_END_TRUE.png"
)
print(a)

#
# self.adb.img_difference(
#     img1=SCREEN_SHOOT_SAVE_PATH + "battle_end.png",
#     img2=STORAGE_PATH + "BATTLE_INFO_BATTLE_END_TRUE.png"
