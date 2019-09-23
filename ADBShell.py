import logging.config
import os
from random import randint
from time import sleep
from io import BytesIO

from PIL import Image

from config import ADB_ROOT, ADB_HOST, SCREEN_SHOOT_SAVE_PATH, ShellColor, CONFIG_PATH,enable_adb_host_auto_detect, ADB_SERVER
from ADBClientSession import ADBClientSession
# from numpy import average, dot, linalg


logging.config.fileConfig(os.path.join(CONFIG_PATH, 'logging.ini'))
logger = logging.getLogger('ADBShell')

def _screencap_to_image(cap):
    w, h, pixels = cap
    return Image.frombytes('RGBA', (w, h), pixels)

def _ensure_pil_image(imgorfile):
    if isinstance(imgorfile, Image.Image):
        return imgorfile
    return Image.open(imgorfile)

class ADBShell(object):
    def __init__(self, adb_host=ADB_HOST):
        # os.chdir(ADB_ROOT)
        self.ADB_ROOT = ADB_ROOT
        self.ADB_HOST = adb_host
        self.shell_log = ShellColor()
        self.host_session_factory = lambda: ADBClientSession(ADB_SERVER)
        self.DEVICE_NAME = self.__adb_device_name_detector()
        self.device_session_factory = lambda: self.host_session_factory().device(self.DEVICE_NAME)

    def __adb_device_name_detector(self):
        if not enable_adb_host_auto_detect:
            return ADB_HOST
        devices = self.host_session_factory().devices()
        if len(devices) == 1:
            device_name = devices[0][0]
        else:
            logger.info("[!] 检测到多台设备，根据 ADB_HOST 参数将自动选择设备")
            device_name = ""
            for i, device in enumerate(devices):
                print('[%d]  %s\t%s' % (i, *device))
                if self.ADB_HOST == device[0]:
                    device_name = self.ADB_HOST
            if device_name == "":
                logger.warn("自动选择设备失败，请根据上述内容自行输入数字并选择")
                input_valid_flag = False
                num = "0"
                while not input_valid_flag:
                    try:
                        num = int(input(">"))
                        if 0 <= num < len(devices):
                            input_valid_flag = True
                    except:
                        logger.error("输入不合法，请重新输入")
                device_name = devices[num][0]
        logger.info("[+] 确认设备名称\t" + device_name)
        return device_name

    def __adb_connect(self):
        try:
            host_session_factory().service('host:connect:'+self.DEVICE_NAME)
            logger.info(
                "[+] Connect to DEVICE {}  Success".format(self.DEVICE_NAME))
        except:
            logger.error(
                "[-] Connect to DEVICE {}  Failed".format(self.DEVICE_NAME))


    def run_device_cmd(self, cmd, DEBUG_LEVEL=2):
        output = self.device_session_factory().exec(cmd)
        logger.debug("command: %s", cmd)
        logger.debug("output: %s", repr(output))
        return output
        

    def get_sub_screen(self, image, screen_range):
        return image.crop(
            (
                screen_range[0][0],
                screen_range[0][1],
                screen_range[0][0] + screen_range[1][0],
                screen_range[0][1] + screen_range[1][1]
            )
        )

    def get_screen_shoot(self, screen_range=None):
        # sleep(1)
        rawcap = self.device_session_factory().screencap()
        img = _screencap_to_image(rawcap)
        if screen_range is not None:
            return self.get_sub_screen(img, screen_range)
        return img

    def touch_swipe(self, XY_mXmY=None, FLAG=None):
        # sleep(1)
        XY, mXmY = XY_mXmY
        logger.debug("滑动初始坐标:({},{}); 移动距离dX:{}, dy:{}".format(XY[0], XY[1], XY[0] + mXmY[0], XY[1] + mXmY[1]))
        command = "input swipe {X1} {Y1} {X2} {Y2}".format(
            X1=XY[0], Y1=XY[1], X2=XY[0] + mXmY[0], Y2=XY[1] + mXmY[1]
        )
        self.run_device_cmd(command)

    def touch_tap(self, XY=None, offsets=None):
        # sleep(10)
        # sleep(0.5)
        if offsets is not None:
            final_X = XY[0] + randint(-offsets[0], offsets[0])
            final_Y = XY[1] + randint(-offsets[1], offsets[1])
        else:
            final_X = XY[0] + randint(-1, 1)
            final_Y = XY[1] + randint(-1, 1)
        # 如果你遇到了问题，可以把这百年输出并把日志分享到群里。
        logger.debug("点击坐标:({},{})".format(final_X, final_Y))
        command = "input tap {} {}".format(final_X,
                                                      final_Y)
        self.run_device_cmd(command)

    @staticmethod
    def img_difference(img1, img2):
        img1 = _ensure_pil_image(img1).convert('1')
        img2 = _ensure_pil_image(img2).convert('1')
        hist1 = list(img1.getdata())
        hist2 = list(img2.getdata())
        sum1 = 0
        for i in range(len(hist1)):
            if hist1[i] == hist2[i]:
                sum1 += 1
            else:
                sum1 += 1 - \
                        float(abs(hist1[i] - hist2[i])) / max(hist1[i], hist2[i])
        return sum1 / len(hist1)

#
# if __name__ == '__main__':
#     a = ADBShell()
