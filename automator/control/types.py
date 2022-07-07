from __future__ import annotations
from typing import Protocol, TYPE_CHECKING
import enum

if TYPE_CHECKING:
    from util import cvimage

class EventAction(enum.IntEnum):
    DOWN = 0
    UP = 1
    MOVE = 2

class EventFlag(enum.IntFlag):
    ASYNC = 0x1
    MERGE_MULTITOUCH_MOVE = 0x2

class InputProtocol(Protocol):
    def get_input_capabilities(self) -> ControllerCapabilities:
        return ControllerCapabilities(0)
    def touch_tap(self, x: int, y: int, hold_time: float = 0) -> None:
        raise NotImplementedError
    def touch_swipe(self, x0, y0, x1, y1, move_duration=1, hold_before_release=0, interpolation='linear'):
        raise NotImplementedError
    def touch_event(self, action: EventAction, x: int, y: int, pointer_id = 0) -> None:
        raise NotImplementedError
    def key_event(self, action: EventAction, keycode: int, metastate: int = 0) -> None:
        raise NotImplementedError
    def send_key(self, keycode: int, metastate: int = 0) -> None:
        raise NotImplementedError
    def send_text(self, text: str) -> None:
        raise NotImplementedError
    def close(self) -> None:
        pass

class ScreenshotProtocol(Protocol):
    def get_screenshot_capabilities(self) -> ControllerCapabilities:
        return ControllerCapabilities(0)
    def screenshot(self) -> cvimage.Image:
        raise NotImplementedError
    def close(self) -> None:
        pass

class ControllerCapabilities(enum.Flag):
    SCREENSHOT_TIMESTAMP = enum.auto()
    """screenshots include a render timestamp"""

    LOW_LATENCY_INPUT = enum.auto()
    """input is processed immediately, on contrast to the legacy `input` command that spawns an `app_process`"""

    TOUCH_EVENTS = enum.auto()
    """touch events (pointer down/move/up) are supported"""

    KEYBOARD_EVENTS = enum.auto()
    """keyboard events (key down/up) are supported"""

    MULTITOUCH_EVENTS = enum.auto()
    """multitouch events (more than one pointer down/move/up) are supported"""

class Controller(Protocol):
    input: InputProtocol
    def get_controller_capabilities(self) -> ControllerCapabilities:
        raise NotImplementedError
    def screenshot(self) -> cvimage.Image:
        raise NotImplementedError
    def close(self) -> None:
        pass

class ControllerTarget(Protocol):
    auto_connect_priority: int
    def describe(self) -> tuple[str, str]:
        """returns identifier, description"""
        raise NotImplementedError
    def create_controller(self) -> Controller:
        raise NotImplementedError
