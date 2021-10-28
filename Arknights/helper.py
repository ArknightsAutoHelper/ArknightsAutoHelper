from __future__ import annotations
from collections import OrderedDict
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Annotated, Callable, ClassVar, Sequence, Tuple, TypeVar, Union, Type, ForwardRef
    from numbers import Real
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
from .mixin import AddonMixin

logger = logging.getLogger('helper')

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
        self.addons: dict[Union[str, Type[TAddon]], TAddon] = {}
        self._cli_commands = OrderedDict()
        self.load_addons()
        logger.debug("成功初始化模块")

    def addon(self, cls: Union[ForwardRef[Type[TAddon]], Type[TAddon]]) -> TAddon:
        if cls in self.addons:
            return self.addons[cls]
        elif type(cls) == type:
            logger.debug("loading addon %s", cls.__qualname__)
            instance = cls(self)
            self.addons[cls] = instance
            alias = getattr(instance, 'alias', None)
            if alias is None:
                alias = cls.__name__
            self.addons[alias] = instance
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
