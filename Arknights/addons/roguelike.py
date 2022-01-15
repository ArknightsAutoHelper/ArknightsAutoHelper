from random import randint

import imgreco.roguelike
from Arknights.addons.common import CommonAddon
from Arknights.flags import SMALL_WAIT, TINY_WAIT
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
        self.logger.info("好友助战")
        self.tap_rect(self.ocr.SUPPORT_UNITS_BUTTON)

    def cli_roguelike(self, argv) -> int:
        """
        roguelike
        集成战略
        """
        with self.helper.frontend.context:
            self._forward_looking_investment()
        return 0
