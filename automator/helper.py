from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TypeVar, Union, Type, ForwardRef
    from .addon import AddonBase
    TAddon = TypeVar('TAddon')
del TYPE_CHECKING

import logging

logger = logging.getLogger('helper')


from .connector.ADBConnector import ADBConnector
from .frontend import Frontend, DummyFrontend
from .mixin import AddonMixin

class BaseAutomator(AddonMixin):
    frontend: Frontend
    def __init__(self, device_connector=None, frontend=None):  # 当前绑定到的设备
        self.logger = logging.getLogger(type(self).__name__)
        self.frontend = frontend
        self.frontend.attach(self)
        self.helper = self
        self.addons: dict[Union[str, Type[TAddon]], TAddon] = {}
        self._cli_commands = OrderedDict()
        self.load_addons()

        self._device = None
        if device_connector is not None:
            self.connect_device(device_connector)
        if frontend is None:
            frontend = DummyFrontend()

        logger.debug("成功初始化模块")


    def addon(self, cls: Union[ForwardRef[Type[TAddon]], Type[TAddon]]) -> TAddon:
        from .addon import _addon_registry
        dealias = _addon_registry[cls]
        if dealias in self.addons:
            return self.addons[dealias]
        elif type(dealias) == type:
            logger.debug("loading addon %s", dealias.__qualname__)
            instance = dealias(self)
            self.addons[dealias] = instance
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
        self.vw = self._viewport[0] / 100
        self.vh = self._viewport[1] / 100
        self.on_device_connected()
        self.frontend.notify('current-device', str(self._device))
    
    def on_device_connected(self):
        pass

    def load_addons(self):
        pass
