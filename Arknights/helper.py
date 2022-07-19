from __future__ import annotations

import os
import time
import logging
from fractions import Fraction

import app

from automator import BaseAutomator

logger = logging.getLogger('helper')

from . import all_addons
class ArknightsHelper(BaseAutomator):
    def on_device_connected(self):
        if self.viewport[1] < 720 or Fraction(self.viewport[0], self.viewport[1]) < Fraction(16, 9):
            title = '设备当前分辨率（%dx%d）不符合要求' % (self.viewport[0], self.viewport[1])
            body = '需要宽高比等于或大于 16∶9，且渲染高度不小于 720。'
            details = None
            if Fraction(self.viewport[1], self.viewport[0]) >= Fraction(16, 9):
                body = '屏幕截图可能需要旋转，请尝试在 device-config 中指定旋转角度。'
                img = self._controller.screenshot()
                imgfile = app.screenshot_path.joinpath('orientation-diagnose-%s.png' % time.strftime("%Y%m%d-%H%M%S"))
                img.save(imgfile)
                import json
                details = '参考 %s 以更正 device-config.json[%s]["screenshot_rotate"]' % (imgfile, json.dumps(self._controller.config_key))
            for msg in [title, body, details]:
                if msg is not None:
                    logger.warn(msg)
            self.frontend.alert(title, body, 'warn', details)
