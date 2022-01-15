import operator

import cv2
import numpy as np

from imgreco import common, resources, imgops
from imgreco.imgops import match_template
from imgreco.resources import load_pickle
from util.cvimage import Rect
from util.richlog import get_logger

logger = get_logger(__name__)


class RoguelikeOCR:
    def __init__(self):
        self.EXPLORE_BUTTON = (1065, 515, 1263, 704)
        self.ASSAULT_BUTTON = (0, 0, 0, 0)
        self.ASSAULT_OK_BUTTON = (0, 0, 0, 0)
        self.STRENGTHS_MAKE_UP_WEAKNESS_BUTTON = (655, 566, 912, 632)
        self.INITIAL_RECRUIT_BUTTON = [(243, 522, 460, 574), (534, 521, 751, 573), (821, 521, 1038, 573)]
        self.SUPPORT_UNITS_BUTTON = (1012, 10, 1187, 57)

    def check_explore_button_exist(self, img):
        """
        检测是否在肉鸽开始界面
        """
        icon1 = img.crop(self.EXPLORE_BUTTON).convert('RGB')
        icon2 = resources.load_image_cached('roguelike/explore.png', 'RGB')
        icon1, icon2 = imgops.uniform_size(icon1, icon2)
        mse = imgops.compare_mse(np.asarray(icon1), np.asarray(icon2))
        logger.logimage(icon1)
        logger.logtext('mse=%f' % mse)
        return mse < 500

    def check_assault_detachment(self, img):
        img = img.convert('RGB')
        tmp, score = self._get_rect_by_template(img, "assault")
        logger.logimage(img.crop(tmp))
        logger.logtext('score=%f' % score)
        if score > 0.9:
            self.ASSAULT_BUTTON = tmp
            return True
        else:
            return False

    def check_assault_ok(self, img):
        subarea = (self.ASSAULT_BUTTON[0], 0, self.ASSAULT_BUTTON[2], img.height)
        cropped_img = img.convert('RGB').crop(subarea)
        tmp, score = self._get_rect_by_template(cropped_img, "assault-ok")
        tmp = (tmp[0] + self.ASSAULT_BUTTON[0], tmp[1], tmp[2] + self.ASSAULT_BUTTON[0], tmp[3])
        logger.logimage(img.crop(tmp))
        logger.logtext('score=%f' % score)
        if score > 0.9:
            self.ASSAULT_OK_BUTTON = tmp
            return True
        else:
            return False

    @staticmethod
    def _get_rect_by_template(img, template):
        template = resources.load_image_cached(f'roguelike/{template}.png', 'RGB')
        result, score = match_template(img, template)
        tmp = Rect.from_center_wh(result[0], result[1], template.width, template.height).ltrb
        return tmp, score


def main():
    ocr = RoguelikeOCR()
    from PIL import Image
    ocr.ASSAULT_BUTTON = (593, 169, 732, 347)
    img = Image.open(r"C:\Users\chunibyo\Documents\MuMu共享文件夹\MuMu20220115190005.png")
    ocr.check_assault_ok(img)


if __name__ == '__main__':
    main()
