from Arknights.helper import ArknightsHelper
from abc import ABC, abstractmethod


class BaseAddOn(ABC):
    def __init__(self, helper=None):
        if helper is None:
            helper = ArknightsHelper()
        self.helper = helper

    @abstractmethod
    def run(self, **kwargs):
        pass
