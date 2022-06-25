from __future__ import annotations
import time
from contextlib import AbstractContextManager, nullcontext
from abc import ABC, abstractmethod

from automator.control.types import Controller

class Frontend(ABC):
    @abstractmethod
    def attach(self, helper):
        pass

    @abstractmethod
    def alert(self, title, text, level='info', details=None):
        """user-targeted message"""

    @abstractmethod
    def notify(self, name, value):
        """program-targeted message"""

    @abstractmethod
    def delay(self, secs, skippable):
        time.sleep(secs)

    @abstractmethod
    def request_device_connector(self) -> Controller:
        """request a device connector (interactively) from frontend"""
        return None

    @property
    @abstractmethod
    def context(self) -> AbstractContextManager[None]:
        return nullcontext()

class DummyFrontend(Frontend):
    pass
