import os, shutil

a = os.path.abspath(".")
from ADBShell import ADBShell
from config import *

adb = ADBShell()
f_name = "Friday_collection"
f_name += ".png"
adb.get_screen_shoot(f_name)
shutil.move(SCREEN_SHOOT_SAVE_PATH + f_name, a + "\\" + f_name)
