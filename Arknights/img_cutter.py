'''
在这里做一些测试，包括图像的匹配度算法操作
'''
from config import *
from PIL import Image
import hashlib
from Arknights.click_location import *

i1 = Image.open(SCREEN_SHOOT_SAVE_PATH + "2-2_0.png")

#     "BATTLE_CLICK_AI_COMMANDER": ((1055, 582), (19, 19))

i1_c = i1.crop(
    (1055, 580, 1055 + 23, 580 + 23)
)

i1_c.save(SCREEN_SHOOT_SAVE_PATH + "2-2_0_C.png")

i2 = Image.open(SCREEN_SHOOT_SAVE_PATH + "2-2_1.png")
i2_c = i2.crop(
    (1055, 580, 1055 + 23, 580 + 23)
)
i2_c.save(SCREEN_SHOOT_SAVE_PATH + "2-2_1_C.png")
# hashlib.md5('asd'.encode()).hexdigest()
