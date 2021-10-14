import logging

logger = logging.getLogger(__name__)

class CommonAddon:
    def back_to_main(self):  # 回到主页
        import imgreco.common
        import imgreco.main
        logger.info("正在返回主页")
        retry_count = 0
        max_retry = 3
        while True:
            screenshot = self.adb.screenshot()

            if imgreco.main.check_main(screenshot):
                break

            # 检查是否有返回按钮
            if imgreco.common.check_nav_button(screenshot):
                logger.info('发现返回按钮，点击返回')
                self.tap_rect(imgreco.common.get_nav_button_back_rect(self.viewport))
                self.__wait(SMALL_WAIT)
                # 点击返回按钮之后重新检查
                continue

            if imgreco.common.check_get_item_popup(screenshot):
                logger.info('当前为获得物资画面，关闭')
                self.tap_rect(imgreco.common.get_reward_popup_dismiss_rect(self.viewport))
                self.__wait(SMALL_WAIT)
                continue

            # 检查是否在设置画面
            if imgreco.common.check_setting_scene(screenshot):
                logger.info("当前为设置/邮件画面，返回")
                self.tap_rect(imgreco.common.get_setting_back_rect(self.viewport))
                self.__wait(SMALL_WAIT)
                continue

            # 检测是否有关闭按钮
            rect, confidence = imgreco.common.find_close_button(screenshot)
            if confidence > 0.9:
                logger.info("发现关闭按钮")
                self.tap_rect(rect)
                self.__wait(SMALL_WAIT)
                continue

            dlgtype, ocr = imgreco.common.recognize_dialog(screenshot)
            if dlgtype == 'yesno':
                if '基建' in ocr or '停止招募' in ocr or '好友列表' in ocr:
                    self.tap_rect(imgreco.common.get_dialog_right_button_rect(screenshot))
                    self.__wait(3)
                    continue
                elif '招募干员' in ocr or '加急' in ocr:
                    self.tap_rect(imgreco.common.get_dialog_left_button_rect(screenshot))
                    self.__wait(3)
                    continue
                else:
                    raise RuntimeError('未适配的对话框')
            elif dlgtype == 'ok':
                self.tap_rect(imgreco.common.get_dialog_ok_button_rect(screenshot))
                self.__wait(1)
                continue
            retry_count += 1
            if retry_count > max_retry:
                raise RuntimeError('未知画面')
            logger.info('未知画面，尝试重新识别 {}/{} 次'.format(retry_count, max_retry))
            self.__wait(3)
        logger.info("已回到主页")
