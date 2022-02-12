from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Annotated, Callable, ClassVar, Sequence, Tuple, TypeVar, Union, Type, ForwardRef, Optional
    from .helper import BaseAutomator
    TAddon = TypeVar('TAddon')
del TYPE_CHECKING

import logging
from util import richlog
from .mixin import AddonMixin

logger = logging.getLogger('addon')

@dataclass
class _cli_command_record:
    owner: Type[AddonBase]
    attr: str
    help: Optional[str] = None
    help_func: Optional[Callable] = None
    def get_help(self, helper: BaseAutomator):
        if self.help_func is None:
            return self.help
        else:
            return self.help_func(helper.addon(self.owner))

_addon_registry: OrderedDict[str, Type[AddonBase]] = OrderedDict()
_cli_registry: OrderedDict[str, _cli_command_record] = OrderedDict()

class RichLogSyncHandler(logging.Handler):
    def __init__(self, richlog: richlog.RichLogger):
        super().__init__()
        self.richlog = richlog

    def emit(self, record: logging.LogRecord):
        self.richlog.logtext(f'[{record.levelname}] {record.getMessage()}')

class cli_command:
    def __init__(self, command: Union[Callable[[Sequence[str]], int], str] = None, help: Optional[str] = None):
        if callable(command):
            self.command = None
            self.fn = command
        else:
            self.command = command
        self.help = help
        self.help_func = None

    def __set_name__(self, owner: Type[AddonBase], name: str):
        if self.command is None:
            self.command = name
        if self.help is None:
            self.help = self.fn.__doc__
        _cli_registry[self.command] = _cli_command_record(owner, name, self.help, self.help_func)
        logger.debug('registering cli command: %s from %s', self.command, owner.__qualname__)
        setattr(owner, name, self.fn)

    def dynamic_help(self, func):
        self.help_func = func
        return func

    def __call__(self, fn: Callable[[Sequence[str]], int]):
        self.fn = fn
        return self

class AddonBase(AddonMixin):
    alias : ClassVar[Union[str, None]] = None

    def __init__(self, helper):
        super().__init__()
        self.helper : BaseAutomator = helper
        self.logger = logging.getLogger(type(self).__name__)
        self.richlogger = richlog.get_logger(type(self).__name__)
        self._sync_handler = None
        self.on_attach()

    def __init_subclass__(sub: Type[AddonBase]) -> None:
        super().__init_subclass__()
        _addon_registry[sub.__name__] = sub
        _addon_registry[sub] = sub
        if sub.alias is not None:
            _addon_registry[sub.alias] = sub

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

    def register_gui_handler(self, handler):
        pass

    def sync_richlog(self):
        if self._sync_handler is None:
            self._sync_handler = RichLogSyncHandler(self.richlogger)
            self.logger.addHandler(self._sync_handler)
