from random import randint

import imgreco.roguelike
from Arknights.addons.common import CommonAddon
from Arknights.flags import SMALL_WAIT, TINY_WAIT, MEDIUM_WAIT
from automator import AddonBase


# TODO: 状态机
class RoguelikeAddon(AddonBase):
    def on_attach(self):
        self.ocr = imgreco.roguelike.RoguelikeOCR()

        self.register_cli_command('roguelike', self.cli_roguelike, self.cli_roguelike.__doc__)

    def _forward_looking_investment(self):
        self.logger.info("前瞻性投资")
        screenshot = self.device.screenshot()
        if not self.ocr.check_explore_button_exist(screenshot):
            self.logger.error("不在肉鸽开始界面")
            return
        self.tap_rect(self.ocr.EXPLORE_BUTTON)
        self.delay(SMALL_WAIT)

        self.logger.info("突击战术分队")
        move = -randint(self.viewport[0] // 4, self.viewport[0] // 3)
        self.swipe_screen(move)
        self.delay(TINY_WAIT)
        screenshot = self.device.screenshot()
        if not self.ocr.check_assault_detachment(screenshot):
            self.logger.error("未找到突击战术分队")
            return
        self.tap_rect(self.ocr.ASSAULT_BUTTON)

        screenshot = self.device.screenshot()
        if not self.ocr.check_assault_ok(screenshot):
            self.logger.error("未找到突击战术分队确认按钮")
            return
        self.tap_rect(self.ocr.ASSAULT_OK_BUTTON)

        self.logger.info("取长补短")
        self.tap_rect(self.ocr.STRENGTHS_MAKE_UP_WEAKNESS_BUTTON)
        self.tap_rect(self.ocr.STRENGTHS_MAKE_UP_WEAKNESS_BUTTON)

        self.logger.info("近卫招募")
        self.tap_rect(self.ocr.INITIAL_RECRUIT_BUTTON[0])
        self.delay(TINY_WAIT)
        self.logger.info("好友助战")
        self.tap_rect(self.ocr.SUPPORT_UNITS_BUTTON)
        self.delay(TINY_WAIT)

        # TODO: refresh
        # 左半屏幕
        screenshot = self.device.screenshot().convert('RGB')
        subarea1 = (0, 0, screenshot.width * 0.8, screenshot.height)
        cropped_img = screenshot.crop(subarea1)
        if not self.ocr.check_mountain_exist(cropped_img):
            move = -randint(self.viewport[0] // 4, self.viewport[0] // 3)
            self.swipe_screen(move)
            self.delay(TINY_WAIT)
            # 右半屏幕
            screenshot = self.device.screenshot().convert('RGB')
            if not self.ocr.check_mountain_exist(screenshot):
                self.logger.error("山未找到")
                return

        self.logger.info("山")
        mountain_position = self.ocr.MOUNTAIN
        w, h = mountain_position[2] - mountain_position[0], mountain_position[3] - mountain_position[1]
        click_area = (mountain_position[0] + w * 2.0, mountain_position[1],
                      mountain_position[0] + w * 2.5, mountain_position[3])
        cropped_img = screenshot.crop(click_area)
        if not self.ocr.check_mountain_ok(cropped_img):
            return
        self.ocr.MOUNTAIN_OK = (self.ocr.MOUNTAIN_OK[0] + click_area[0],
                                self.ocr.MOUNTAIN_OK[1] + click_area[1],
                                self.ocr.MOUNTAIN_OK[2] + click_area[0],
                                self.ocr.MOUNTAIN_OK[3] + click_area[1])
        # 招募
        self.tap_rect(self.ocr.MOUNTAIN_OK)
        self.delay(TINY_WAIT)
        self.tap_rect((772, 499, 933, 544))
        self.delay(MEDIUM_WAIT)
        self.tap_rect((772, 499, 933, 544))

        self.logger.info("辅助招募")
        self.tap_rect(self.ocr.INITIAL_RECRUIT_BUTTON[1])
        self.delay(TINY_WAIT)
        self.tap_rect(self.ocr.RECRUIT_CONFIRM)
        self.tap_rect(self.ocr.RECRUIT_CONFIRM2)
        self.delay(TINY_WAIT)

        self.logger.info("医疗招募")
        self.tap_rect(self.ocr.INITIAL_RECRUIT_BUTTON[2])
        self.delay(TINY_WAIT)
        self.tap_rect(self.ocr.RECRUIT_CONFIRM)
        self.tap_rect(self.ocr.RECRUIT_CONFIRM2)
        self.delay(TINY_WAIT)

        screenshot = self.device.screenshot().convert('RGB')
        if not self.ocr.check_enter_castle_exist(screenshot):
            return
        self.tap_rect(self.ocr.ENTER_CASTLE)
        self.delay(MEDIUM_WAIT)

    def cli_roguelike(self, argv) -> int:
        """
        roguelike
        集成战略
        """
        with self.helper.frontend.context:
            self._forward_looking_investment()
        return 0
