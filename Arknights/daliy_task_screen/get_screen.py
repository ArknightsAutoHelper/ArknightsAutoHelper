# coding: utf-8

import os, shutil

# a = os.path.abspath(".")
a = os.path.abspath("../development_step_by_step")
from ADBShell import ADBShell
from config import *

adb = ADBShell()
f_name = "2019_5_3.jpg"
f_name += ".png"
adb.get_screen_shoot(f_name)
shutil.move(SCREEN_SHOOT_SAVE_PATH + f_name, a + "\\" + f_name)
