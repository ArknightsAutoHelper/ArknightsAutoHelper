
from Arknights.helper import ArknightsHelper
import cv2
from util import cvimage as Image
import numpy as np


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
