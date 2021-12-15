from __future__ import annotations
from collections import OrderedDict
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Annotated, Callable, ClassVar, Sequence, Tuple, TypeVar, Union, Type, ForwardRef
    TAddon = TypeVar('TAddon')
del TYPE_CHECKING

import logging



from connector import auto_connect
from connector.ADBConnector import ADBConnector
from .frontend import Frontend, DummyFrontend
from .mixin import AddonMixin

logger = logging.getLogger('helper')

class AddonBase(AddonMixin):
    alias : ClassVar[Union[str, None]] = None

    def __init__(self, helper):
        super().__init__()
        self.helper : BaseAutomator = helper
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

class BaseAutomator(AddonMixin):
    frontend: Frontend
    def __init__(self, device_connector=None, frontend=None):  # 当前绑定到的设备
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
        self.vw = self._viewport[0] / 100
        self.vh = self._viewport[1] / 100
        self.on_device_connected()
        self.frontend.notify('current-device', str(self._device))
    
    def on_device_connected(self):
        pass

    def load_addons(self):
        pass
