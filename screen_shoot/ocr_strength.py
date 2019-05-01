import os
from config import *

os.system(
    "tesseract {} {}".format(
        SCREEN_SHOOT_SAVE_PATH + "strength.png", SCREEN_SHOOT_SAVE_PATH + "1"
    )
)
