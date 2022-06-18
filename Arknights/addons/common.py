from automator import AddonBase
from Arknights.flags import *

class CommonAddon(AddonBase):
    alias = "common"
    def back_to_main(self, extra_predicate=None):  # 回到主页
        import imgreco.common
        import imgreco.main
        if extra_predicate is None:
            self.logger.info("正在返回主页")
            from Arknights.addons.record import RecordAddon
            self.addon(RecordAddon).try_replay_record('back_to_main', quiet=True)
        else:
            self.logger.info("返回上层")
        retry_count = 0
        max_retry = 3
        while True:
            screenshot = self.control.screenshot()

            if extra_predicate is not None and extra_predicate(screenshot):
                self.logger.info('满足停止条件，停止导航')
                return

            if imgreco.main.check_main(screenshot):
                break

            # 检查是否有返回按钮
            if imgreco.common.check_nav_button(screenshot):
                self.logger.info('发现返回按钮，点击返回')
                self.tap_rect(imgreco.common.get_nav_button_back_rect(self.viewport), post_delay=2)
                # 点击返回按钮之后重新检查
                continue

            if imgreco.common.check_get_item_popup(screenshot):
                self.logger.info('当前为获得物资画面，关闭')
                self.tap_rect(imgreco.common.get_reward_popup_dismiss_rect(self.viewport), post_delay=2)
                continue

            # 检查是否在设置画面
            if imgreco.common.check_setting_scene(screenshot):
                self.logger.info("当前为设置/邮件画面，返回")
                self.tap_rect(imgreco.common.get_setting_back_rect(self.viewport), post_delay=2)
                continue

            # 检测是否有关闭按钮
            rect, confidence = imgreco.common.find_close_button(screenshot)
            if confidence > 0.9:
                self.logger.info("发现关闭按钮")
                self.tap_rect(rect, post_delay=2)
                continue

            dlgtype, ocr = imgreco.common.recognize_dialog(screenshot)
            self.logger.debug(f"检查对话框：{dlgtype}, {ocr}")
            if dlgtype == 'yesno':
                if '基建' in ocr or '停止招募' in ocr or '好友列表' in ocr:
                    self.tap_rect(imgreco.common.get_dialog_right_button_rect(screenshot), post_delay=5)
                    continue
                elif '招募干员' in ocr or '加急' in ocr or '退出游戏' in ocr:
                    self.tap_rect(imgreco.common.get_dialog_left_button_rect(screenshot), post_delay=2)
                    continue
                else:
                    raise RuntimeError('未适配的对话框')
            elif dlgtype == 'ok':
                self.tap_rect(imgreco.common.get_dialog_ok_button_rect(screenshot), post_delay=2)
                self.delay(1)
                continue
            retry_count += 1
            if retry_count > max_retry:
                raise RuntimeError('未知画面')
            self.logger.info('未知画面，尝试返回按钮 {}/{} 次'.format(retry_count, max_retry))
            self.control.input.send_key(4)  # KEYCODE_BACK
            self.delay(3)
        self.logger.info("已回到主页")
