import os
import json
import re
import time
import logging
from random import randint, uniform, gauss
from fractions import Fraction

import coloredlogs
import numpy as np

import config
import imgreco.imgops

from connector import auto_connect
from connector.ADBConnector import ADBConnector, ensure_adb_alive
from .frontend import DummyFrontend
from Arknights.flags import *

from Arknights import frontend

logger = logging.getLogger('helper')
coloredlogs.install(
    fmt=' Ξ %(message)s',
    #fmt=' %(asctime)s ! %(funcName)s @ %(filename)s:%(lineno)d ! %(levelname)s # %(message)s',
    datefmt='%H:%M:%S',
    level_styles={'warning': {'color': 'green'}, 'error': {'color': 'red'}},
    level='INFO')


class AddonMixin:
    def delay(self, n=10,  # 等待时间中值
               MANLIKE_FLAG=True, allow_skip=False):  # 是否在此基础上设偏移量
        if MANLIKE_FLAG:
            m = uniform(0, 0.3)
            n = uniform(n - m * 0.5 * n, n + m * n)
        self.helper.frontend.delay(n, allow_skip)

    def mouse_click(self,  # 点击一个按钮
                    XY):  # 待点击的按钮的左上和右下坐标
        assert (self.viewport == (1280, 720))
        logger.debug("helper.mouse_click")
        xx = randint(XY[0][0], XY[1][0])
        yy = randint(XY[0][1], XY[1][1])
        logger.info("接收到点击坐标并传递xx:{}和yy:{}".format(xx, yy))
        self.adb.touch_tap((xx, yy))
        self.delay(TINY_WAIT, MANLIKE_FLAG=True)

    def tap_rect(self, rc):
        hwidth = (rc[2] - rc[0]) / 2
        hheight = (rc[3] - rc[1]) / 2
        midx = rc[0] + hwidth
        midy = rc[1] + hheight
        xdiff = max(-1, min(1, gauss(0, 0.2)))
        ydiff = max(-1, min(1, gauss(0, 0.2)))
        tapx = int(midx + xdiff * hwidth)
        tapy = int(midy + ydiff * hheight)
        self.adb.touch_tap((tapx, tapy))
        self.delay(TINY_WAIT, MANLIKE_FLAG=True)

    def tap_quadrilateral(self, pts):
        pts = np.asarray(pts)
        acdiff = max(0, min(2, gauss(1, 0.2)))
        bddiff = max(0, min(2, gauss(1, 0.2)))
        halfac = (pts[2] - pts[0]) / 2
        m = pts[0] + halfac * acdiff
        pt2 = pts[1] if bddiff > 1 else pts[3]
        halfvec = (pt2 - m) / 2
        finalpt = m + halfvec * bddiff
        self.adb.touch_tap(tuple(int(x) for x in finalpt))
        self.delay(TINY_WAIT, MANLIKE_FLAG=True)

    def wait_for_still_image(self, threshold=16, crop=None, timeout=60, raise_for_timeout=True, check_delay=1):
        if crop is None:
            shooter = lambda: self.adb.screenshot(False)
        else:
            shooter = lambda: self.adb.screenshot(False).crop(crop)
        screenshot = shooter()
        t0 = time.monotonic()
        ts = t0 + timeout
        n = 0
        minerr = 65025
        message_shown = False
        while (t1 := time.monotonic()) < ts:
            if check_delay > 0:
                self.delay(check_delay, False, True)
            screenshot2 = shooter()
            mse = imgreco.imgops.compare_mse(screenshot, screenshot2)
            if mse <= threshold:
                return screenshot2
            screenshot = screenshot2
            if mse < minerr:
                minerr = mse
            if not message_shown and t1-t0 > 10:
                logger.info("等待画面静止")
        if raise_for_timeout:
            raise RuntimeError("%d 秒内画面未静止，最小误差=%d，阈值=%d" % (timeout, minerr, threshold))
        return None



    def swipe_screen(self, move, rand=100, origin_x=None, origin_y=None):
        origin_x = (origin_x or self.viewport[0] // 2) + randint(-rand, rand)
        origin_y = (origin_y or self.viewport[1] // 2) + randint(-rand, rand)
        self.adb.touch_swipe2((origin_x, origin_y), (move, max(250, move // 2)), randint(600, 900))


class AddonBase(AddonMixin):
    def __init__(self, helper):
        super().__init__()
        self.helper = helper
        self.on_attach()
    def addon(self, cls):
        return self.helper.addon(cls)
    def on_attach(self):
        """callback"""

class ArknightsHelper(AddonMixin):
    def __init__(self, adb_host=None, device_connector=None, frontend=None):  # 当前绑定到的设备
        self.adb = None
        if adb_host is not None or device_connector is not None:
            self.connect_device(device_connector, adb_serial=adb_host)
        if frontend is None:
            frontend = DummyFrontend()
            if self.adb is None:
                self.connect_device(auto_connect())
        self.frontend = frontend
        self.frontend.attach(self)
        self.operation_time = []
        self.helper = self
        self.addons = {}
        if DEBUG_LEVEL >= 1:
            self.__print_info()

        logger.debug("成功初始化模块")

    def addon(self, cls):
        if cls in self.addons:
            return self.addons[cls]
        else:
            instance = cls(self)
            self.addons[cls] = instance
            return instance

    def ensure_device_connection(self):
        if self.adb is None:
            raise RuntimeError('not connected to device')

    def connect_device(self, connector=None, *, adb_serial=None):
        if connector is not None:
            self.adb = connector
        elif adb_serial is not None:
            self.adb = ADBConnector(adb_serial)
        else:
            self.adb = None
            return
        self.viewport = self.adb.screen_size
        if self.adb.screenshot_rotate %180:
            self.viewport = (self.viewport[1], self.viewport[0])
        if self.viewport[1] < 720 or Fraction(self.viewport[0], self.viewport[1]) < Fraction(16, 9):
            title = '设备当前分辨率（%dx%d）不符合要求' % (self.viewport[0], self.viewport[1])
            body = '需要宽高比等于或大于 16∶9，且渲染高度不小于 720。'
            details = None
            if Fraction(self.viewport[1], self.viewport[0]) >= Fraction(16, 9):
                body = '屏幕截图可能需要旋转，请尝试在 device-config 中指定旋转角度。'
                img = self.adb.screenshot()
                imgfile = os.path.join(config.SCREEN_SHOOT_SAVE_PATH, 'orientation-diagnose-%s.png' % time.strftime("%Y%m%d-%H%M%S"))
                img.save(imgfile)
                import json
                details = '参考 %s 以更正 device-config.json[%s]["screenshot_rotate"]' % (imgfile, json.dumps(self.adb.config_key))
            for msg in [title, body, details]:
                if msg is not None:
                    logger.warn(msg)
            frontend.alert(title, body, 'warn', details)

    def __print_info(self):
        logger.info('当前系统信息:')
        logger.info('分辨率:\t%dx%d', *self.viewport)
        # logger.info('OCR 引擎:\t%s', ocr.engine.info)
        logger.info('截图路径:\t%s', config.SCREEN_SHOOT_SAVE_PATH)

        if config.enable_baidu_api:
            logger.info('%s',
                        """百度API配置信息:
        APP_ID\t{app_id}
        API_KEY\t{api_key}
        SECRET_KEY\t{secret_key}
                        """.format(
                            app_id=config.APP_ID, api_key=config.API_KEY, secret_key=config.SECRET_KEY
                        )
                        )

    def __del(self):
        self.adb.run_device_cmd("am force-stop {}".format(config.ArkNights_PACKAGE_NAME))

    def destroy(self):
        self.__del()

