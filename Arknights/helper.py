from __future__ import annotations
from collections import OrderedDict
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Annotated, Callable, ClassVar, Sequence, Tuple, TypeVar, Union, Type
    from numbers import Real
    TupleRect: Tuple[Annotated[Real, 'left'], Annotated[Real, 'top'], Annotated[Real, 'right'], Annotated[Real, 'bottom']]
    TAddon = TypeVar('TAddon')
del TYPE_CHECKING

import os
import time
import logging
from random import randint, uniform, gauss
from fractions import Fraction

import numpy as np

import config
import imgreco.imgops

from connector import auto_connect
from connector.ADBConnector import ADBConnector, ensure_adb_alive
from .frontend import Frontend, DummyFrontend
from Arknights.flags import *


logger = logging.getLogger('helper')


class AddonMixin:
    helper: 'ArknightsHelper'
    def delay(self, n: Real=10,  # 等待时间中值
               MANLIKE_FLAG=True, allow_skip=False):  # 是否在此基础上设偏移量
        if MANLIKE_FLAG:
            m = uniform(0, 0.3)
            n = uniform(n - m * 0.5 * n, n + m * n)
        self.helper.frontend.delay(n, allow_skip)

    def mouse_click(self,  # 点击一个按钮
                    XY):  # 待点击的按钮的左上和右下坐标
        assert (self.helper.viewport == (1280, 720))
        logger.debug("helper.mouse_click")
        xx = randint(XY[0][0], XY[1][0])
        yy = randint(XY[0][1], XY[1][1])
        logger.info("接收到点击坐标并传递xx:{}和yy:{}".format(xx, yy))
        self.helper.device.touch_tap((xx, yy))
        self.delay(TINY_WAIT, MANLIKE_FLAG=True)

    def tap_point(self, pos, sleep_time=0.5, randomness=(5, 5)):
        x, y = pos
        rx, ry = randomness
        x += randint(-rx, rx)
        y += randint(-ry, ry)
        self.helper.device.touch_tap((x, y))
        self.delay(sleep_time)

    def tap_rect(self, rc: TupleRect):
        hwidth = (rc[2] - rc[0]) / 2
        hheight = (rc[3] - rc[1]) / 2
        midx = rc[0] + hwidth
        midy = rc[1] + hheight
        xdiff = max(-1, min(1, gauss(0, 0.2)))
        ydiff = max(-1, min(1, gauss(0, 0.2)))
        tapx = int(midx + xdiff * hwidth)
        tapy = int(midy + ydiff * hheight)
        self.helper.device.touch_tap((tapx, tapy))
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
        self.helper.device.touch_tap(tuple(int(x) for x in finalpt))
        self.delay(TINY_WAIT, MANLIKE_FLAG=True)

    def wait_for_still_image(self, threshold=16, crop=None, timeout=60, raise_for_timeout=True, check_delay=1):
        if crop is None:
            shooter = lambda: self.helper.device.screenshot(False)
        else:
            shooter = lambda: self.helper.device.screenshot(False).crop(crop)
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
        self.helper.device.touch_swipe2((origin_x, origin_y), (move, max(250, move // 2)), randint(600, 900))


class AddonBase(AddonMixin):
    alias : ClassVar[Union[str, None]] = None

    def __init__(self, helper):
        super().__init__()
        self.helper : ArknightsHelper = helper
        self.logger = logging.getLogger(type(self).__name__)
        self.on_attach()

    def addon(self, cls: Union[str, Type[TAddon]]) -> TAddon:
        return self.helper.addon(cls)

    def on_attach(self) -> None:
        """callback"""

    @property
    def device(self):
        return self.helper.device

    @property
    def viewport(self):
        self.helper._ensure_device()
        return self.helper.viewport

    @property
    def vw(self):
        self.helper._ensure_device()
        return self.helper.vw

    @property
    def vh(self):
        self.helper._ensure_device()
        return self.helper.vh

    @property
    def frontend(self):
        return self.helper.frontend

    def register_cli_command(self, command: str, handler: Callable[[Annotated[Sequence[str], "argv"]], int], help: Union[str, None]=None):
        if help is None:
            help = command
        self.helper._cli_commands[command] = (command, handler, help)

    def register_gui_handler(self, handler):
        pass

class ArknightsHelper(AddonMixin):
    frontend: Frontend
    def __init__(self, device_connector=auto_connect, frontend=None):  # 当前绑定到的设备
        self._device = None
        if device_connector is None:
            pass
        elif device_connector is auto_connect:
            self.connect_device(auto_connect())
        else:
            self.connect_device(device_connector)
        if frontend is None:
            frontend = DummyFrontend()
        self.frontend = frontend
        self.frontend.attach(self)
        self.helper = self
        self._addons = {}
        self._cli_commands = OrderedDict()
        self.load_addons()
        logger.debug("成功初始化模块")

    def addon(self, cls: Union[str, Type[TAddon]]) -> TAddon:
        if cls in self._addons:
            return self._addons[cls]
        elif type(cls) == type:
            logger.debug("loading addon %s", cls.__qualname__)
            instance = cls(self)
            self._addons[cls] = instance
            alias = getattr(instance, 'alias', None)
            if alias is None:
                alias = cls.__name__
            self._addons[alias] = instance
            return instance
        else:
            raise TypeError("cls")

    def _ensure_device(self):
        if self._device is None:
            new_device = self.frontend.request_device_connector()
            if new_device is None:
                raise RuntimeError("no device connected")
            self.connect_device(connector=new_device)

    @property
    def device(self):
        self._ensure_device()
        return self._device

    @property
    def viewport(self):
        self._ensure_device()
        return self._viewport

    def connect_device(self, connector=None, *, adb_serial=None):
        if connector is not None:
            self._device = connector
        elif adb_serial is not None:
            self._device = ADBConnector(adb_serial)
        else:
            self._device = None
            return
        self._viewport: tuple[int, int] = self._device.screen_size
        if self._device.screenshot_rotate %180:
            self._viewport = (self._viewport[1], self._viewport[0])
        import imgreco.common
        self.vw, self.vh = imgreco.common.get_vwvh(self.viewport)
        if self._viewport[1] < 720 or Fraction(self._viewport[0], self._viewport[1]) < Fraction(16, 9):
            title = '设备当前分辨率（%dx%d）不符合要求' % (self._viewport[0], self._viewport[1])
            body = '需要宽高比等于或大于 16∶9，且渲染高度不小于 720。'
            details = None
            if Fraction(self._viewport[1], self._viewport[0]) >= Fraction(16, 9):
                body = '屏幕截图可能需要旋转，请尝试在 device-config 中指定旋转角度。'
                img = self._device.screenshot()
                imgfile = os.path.join(config.SCREEN_SHOOT_SAVE_PATH, 'orientation-diagnose-%s.png' % time.strftime("%Y%m%d-%H%M%S"))
                img.save(imgfile)
                import json
                details = '参考 %s 以更正 device-config.json[%s]["screenshot_rotate"]' % (imgfile, json.dumps(self._device.config_key))
            for msg in [title, body, details]:
                if msg is not None:
                    logger.warn(msg)
            self.frontend.alert(title, body, 'warn', details)

    def load_addons(self):
        from .addons.common import CommonAddon
        from .addons.combat import CombatAddon
        from .addons.recruit import RecruitAddon
        from .addons.stage_navigator import StageNavigator
        from .addons.quest import QuestAddon
        from .addons.record import RecordAddon
        
        self.addon(CommonAddon)
        self.addon(CombatAddon)
        self.addon(StageNavigator)
        self.addon(RecruitAddon)
        self.addon(QuestAddon)
        self.addon(RecordAddon)

        from .addons.contrib.grass_on_aog import GrassAddOn
        self.addon(GrassAddOn)

        from .addons.contrib.activity import ActivityAddOn
        self.addon(ActivityAddOn)
        
        try:
            from .addons.contrib.start_sp_stage import StartSpStageAddon
            self.addon(StartSpStageAddon)
        except Exception:
            pass

        from .addons.contrib.plan import PlannerAddOn
        self.addon(PlannerAddOn)
