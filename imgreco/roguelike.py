import operator

import cv2
import numpy as np

from imgreco import common, resources, imgops
from imgreco.imgops import match_template
from imgreco.resources import load_pickle
from util.cvimage import Rect
from util.richlog import get_logger

logger = get_logger(__name__)


# TODO: add unit tests
class RoguelikeOCR:
    def __init__(self):
        self.EXPLORE_BUTTON = (1065, 515, 1263, 704)
        self.ASSAULT_BUTTON = (0, 0, 0, 0)
        self.ASSAULT_OK_BUTTON = (0, 0, 0, 0)
        self.STRENGTHS_MAKE_UP_WEAKNESS_BUTTON = (655, 566, 912, 632)
        self.INITIAL_RECRUIT_BUTTON = [(243, 522, 460, 574), (534, 521, 751, 573), (821, 521, 1038, 573)]
        self.SUPPORT_UNITS_BUTTON = (1012, 10, 1187, 57)
        self.MOUNTAIN = (0, 0, 0, 0)
        self.MOUNTAIN_OK = (0, 0, 0, 0)
        self.RECRUIT_CONFIRM = (1069, 654, 1251, 699)
        self.RECRUIT_CONFIRM2 = (732, 457, 936, 529)
        self.ENTER_CASTLE = (0, 0, 0, 0)

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
        """
        选择突击战术分队
        """
        img = img.convert('RGB')
        tmp, score = self._get_rect_by_template(img, "assault")
        logger.logimage(img.crop(tmp))
        logger.logtext('assault score=%f' % score)
        if score > 0.9:
            self.ASSAULT_BUTTON = tmp
            return True
        else:
            return False

    def check_assault_ok(self, img):
        # 突击战术分队确认按钮
        subarea = (self.ASSAULT_BUTTON[0], 0, self.ASSAULT_BUTTON[2], img.height)
        cropped_img = img.convert('RGB').crop(subarea)
        tmp, score = self._get_rect_by_template(cropped_img, "assault-ok")
        tmp = (tmp[0] + self.ASSAULT_BUTTON[0], tmp[1], tmp[2] + self.ASSAULT_BUTTON[0], tmp[3])
        logger.logimage(img.crop(tmp))
        logger.logtext('assault ok score=%f' % score)
        if score > 0.9:
            self.ASSAULT_OK_BUTTON = tmp
            return True
        else:
            return False

    def check_mountain_exist(self, img):
        tmp, score = self._get_rect_by_template(img, "mountain")
        logger.logimage(img.crop(tmp))
        logger.logtext('mountain score=%f' % score)
        if score > 0.9:
            self.MOUNTAIN = tmp
            return True
        else:
            tmp, score = self._get_rect_by_template(img, "mountain2")
            logger.logimage(img.crop(tmp))
            logger.logtext('mountain2 score=%f' % score)
            if score > 0.9:
                self.MOUNTAIN = tmp
                return True
        return False

    def check_mountain_ok(self, img):
        tmp, score = self._get_rect_by_template(img, "mountain-ok")
        logger.logimage(img.crop(tmp))
        logger.logtext('mountain-ok score=%f' % score)
        if score > 0.9:
            self.MOUNTAIN_OK = tmp
            return True
        else:
            tmp, score = self._get_rect_by_template(img, "mountain-ok2")
            logger.logimage(img.crop(tmp))
            logger.logtext('mountain-ok2 score=%f' % score)
            if score > 0.9:
                self.MOUNTAIN_OK = tmp
                return True
        return False

    def check_enter_castle_exist(self, img):
        """
        进入古堡按钮
        """
        tmp, score = self._get_rect_by_template(img, "enter-castle")
        logger.logimage(img.crop(tmp))
        logger.logtext('enter-castle score=%f' % score)
        if score > 0.9:
            self.ENTER_CASTLE = tmp
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
    screenshot = Image.open(r"C:\Users\chunibyo\Documents\MuMu共享文件夹\MuMu20220115215238.png").convert('RGB')
    subarea1 = (928.0, 506.0, 1018.0, 686.0)
    screenshot = screenshot.convert('RGB').crop(subarea1)
    ocr.check_mountain_ok(screenshot)
    # mountain_position = ocr.MOUNTAIN
    # w, h = mountain_position[2] - mountain_position[0], mountain_position[3] - mountain_position[1]
    # click_area = (mountain_position[0] + w * 2.0, mountain_position[1],
    #               mountain_position[0] + w * 2.5, mountain_position[3])
    # print(click_area)


if __name__ == '__main__':
    main()
