import random

from Arknights.helper import ArknightsHelper
from abc import ABC, abstractmethod
import time
import cv2
from util import cvimage as Image
import numpy as np

from imgreco import common


def cv2pil(cv_img):
    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))


def pil2cv(pil_img):
    return cv2.cvtColor(np.asarray(pil_img), cv2.COLOR_BGR2RGB)


def crop_cv_by_rect(cv_img, rect):
    l, t, r, b = tuple(map(int, rect))
    return cv_img[t:b, l:r]


def show_img(img):
    cv2.imshow('test', img)
    cv2.waitKey()


class BaseAddOn(ABC):
    def __init__(self, helper=None):
        if helper is None:
            helper = ArknightsHelper()
        self.helper = helper
        self.vw, self.vh = common.get_vwvh(self.helper.viewport)

    @abstractmethod
    def run(self, **kwargs):
        pass

    def click(self, pos, sleep_time=0.5, randomness=(5, 5)):
        x, y = pos
        rx, ry = randomness
        x += random.randint(-rx, rx)
        y += random.randint(-ry, ry)
        self.helper.adb.touch_tap((x, y))
        time.sleep(sleep_time)

    def screenshot(self):
        return self.helper.adb.screenshot()
