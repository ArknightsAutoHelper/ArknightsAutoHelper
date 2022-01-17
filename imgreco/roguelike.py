import operator

import cv2
import numpy as np
from numpy import argmax

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
        self.CURRENT_STAGE = (0, 0, 0, 0)
        self.REFRESH_BUTTON = (1100, 13, 1262, 54)
        self.ENTER_STAGE = (1071, 401, 1220, 568)
        self.TROOP_BUTTON = (190, 145, 252, 210)
        self.TROOP_CHOOSE_MOUNTAIN = [(507, 97, 722, 186), (65, 520, 280, 609), (1088, 662, 1242, 691)]
        self.START_BATTLE_BUTTON = (956, 649, 1234, 700)
        self.SPEED_UP_BUTTON = (1068, 26, 1133, 84)
        self.SKILL_BUTTON = (0, 0, 0, 0)
        self.BATTLE_END = (28, 514, 317, 593)
        self.BATTLE_END_RUN = (0, 0, 0, 0)
        self.BATTLE_END_RUN_OK = (0, 0, 0, 0)

        self.MAP_DICT = [
            {"name": "意外", "action": [((1223, 643), (-507, -320)), ((717, 323), (-342, 6))], "operator": (642, 325)},
            {"name": "驯兽小屋", "action": [((1228, 662), (-796, -182)), ((434, 483), (422, -3))], "operator": (645, 471)},
            {"name": "礼炮小队", "action": [((1219, 642), (-716, -301)), ((512, 338), (351, -5))], "operator": (405, 317)},
            {"name": "与虫为伴", "action": [((1225, 651), (-634, -278)), ((596, 369), (5, -274))], "operator": (506, 364)},
        ]

    def get_map_name(self, num):
        return self.MAP_DICT[num - 1]["name"]

    def get_map_action(self, num):
        return self.MAP_DICT[num - 1]["action"]

    def get_operator(self, num):
        return self.MAP_DICT[num - 1]["operator"]

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

    def check_current_stage(self, img) -> int:
        """
        检测可见关卡类型
        """
        logger.logimage(img)
        if tmp := self._check_battle(img):
            self.CURRENT_STAGE = tmp
            return 1
        elif tmp := self._check_accident(img):
            self.CURRENT_STAGE = tmp
            return 2
        elif tmp := self._check_interlude(img):
            self.CURRENT_STAGE = tmp
            return 3
        else:
            return 0

    def _check_battle(self, img):
        """
        作战
        """
        tmp, score = self._get_rect_by_template(img, "battle")
        logger.logimage(img.crop(tmp))
        logger.logtext('battle score=%f' % score)
        if score > 0.9:
            return tmp
        else:
            tmp, score = self._get_rect_by_template(img, "battle2")
            logger.logimage(img.crop(tmp))
            logger.logtext('battle2 score=%f' % score)
            if score > 0.9:
                return tmp
        return None

    def _check_accident(self, img):
        """
        不期而遇
        """
        tmp, score = self._get_rect_by_template(img, "accident")
        logger.logimage(img.crop(tmp))
        logger.logtext('accident score=%f' % score)
        if score > 0.9:
            return tmp
        else:
            return None

    def _check_interlude(self, img):
        """
        不期而遇
        """
        tmp, score = self._get_rect_by_template(img, "interlude")
        logger.logimage(img.crop(tmp))
        logger.logtext('interlude score=%f' % score)
        if score > 0.9:
            return tmp
        else:
            return None

    def check_refresh_button_exist(self, img):
        """
        检测是否存在刷新按钮
        """
        icon1 = img.crop(self.REFRESH_BUTTON).convert('RGB')
        icon2 = resources.load_image_cached('roguelike/refresh.png', 'RGB')
        icon1, icon2 = imgops.uniform_size(icon1, icon2)
        mse = imgops.compare_mse(np.asarray(icon1), np.asarray(icon2))
        logger.logimage(icon1)
        logger.logtext('refresh mse=%f' % mse)
        return mse < 5000

    def check_mountain_exist_in_troop(self, img):
        """
        检测编队中是否存在干员
        """
        icon1 = img.crop(self.TROOP_BUTTON).convert('RGB')
        icon2 = resources.load_image_cached('roguelike/mountain_troop.png', 'RGB')
        icon1, icon2 = imgops.uniform_size(icon1, icon2)
        mse = imgops.compare_mse(np.asarray(icon1), np.asarray(icon2))
        logger.logimage(icon1)
        logger.logtext('refresh mse=%f' % mse)
        return mse > 800

    def check_battle_map(self, img):
        result = []
        for i in range(1, 5):
            template = resources.load_image_cached(f'roguelike/map{i}.png', 'RGB')
            feature_result = imgops.match_feature(template, img)
            score = feature_result.matched_keypoint_count
            result.append(score)
        return argmax(result) + 1

    def check_skill_available(self, img):
        tmp, score = self._get_rect_by_template(img, "skill_icon")
        logger.logimage(img.crop(tmp))
        logger.logtext('skill icon score=%f' % score)
        return score > 0.8

    def check_skill_position(self, img):
        # 干员放置位置不同时，技能图标大小会变化，所以需要使用特征点比较
        template = resources.load_image_cached(f'roguelike/skill.png', 'RGB')
        feature_result = imgops.match_feature(template, img)
        score = feature_result.matched_keypoint_count
        x, y, w, h = cv2.boundingRect(feature_result.template_corners)
        tmp = Rect.from_xywh(x, y, w, h).ltrb

        logger.logtext('skill score=%f' % score)
        if score > 45:
            logger.logimage(img.crop(tmp))
            self.SKILL_BUTTON = tmp
            return True
        else:
            return False

    def check_battle_end(self, img):
        tmp, score = self._get_rect_by_template(img, "battle_end")
        logger.logimage(img.crop(tmp))
        logger.logtext('battle_end score=%f' % score)
        return score > 0.9

    def check_battle_end_run(self, img):
        tmp, score = self._get_rect_by_template(img, "battle_end_run")
        logger.logimage(img.crop(tmp))
        logger.logtext('battle end run score=%f' % score)
        if score > 0.9:
            self.BATTLE_END_RUN = tmp
            return True
        else:
            return False

    def check_battle_end_run_ok(self, img):
        tmp, score = self._get_rect_by_template(img, "battle_end_run_ok")
        logger.logimage(img.crop(tmp))
        logger.logtext('battle end run score=%f' % score)
        if score > 0.9:
            self.BATTLE_END_RUN_OK = tmp
            return True
        else:
            return False

    @staticmethod
    def _get_rect_by_template(img, template):
        template = resources.load_image_cached(f'roguelike/{template}.png', 'RGB')
        result, score = match_template(img, template)
        tmp = Rect.from_center_wh(result[0], result[1], template.width, template.height).ltrb
        return tmp, score
