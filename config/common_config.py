import os
if "win32" in os.sys.platform:
    SCREEN_SHOOT_SAVE_PATH = os.getcwd() + "\\screen_shoot\\"
    STORAGE_PATH = os.getcwd() + "\\storage\\"
else:
    SCREEN_SHOOT_SAVE_PATH = os.getcwd() + "/screen_shoot/"
    STORAGE_PATH = os.getcwd() + "/storage/"
