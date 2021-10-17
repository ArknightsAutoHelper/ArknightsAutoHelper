import logging
logger = logging.getLogger(__name__)

class BootstrapAddon:
    def check_game_active(self):  # 启动游戏 需要手动调用
        self.logger.debug("helper.check_game_active")
        current = self.device.run_device_cmd('dumpsys window windows | grep mCurrentFocus').decode(errors='ignore')
        self.logger.debug("正在尝试启动游戏")
        self.logger.debug(current)
        if config.ArkNights_PACKAGE_NAME in current:
            self.logger.debug("游戏已启动")
        else:
            self.device.run_device_cmd(
                "am start -n {}/{}".format(config.ArkNights_PACKAGE_NAME, config.ArkNights_ACTIVITY_NAME))
            self.logger.debug("成功启动游戏")
    def module_login(self):
        self.logger.debug("helper.module_login")
        self.logger.info("发送坐标LOGIN_QUICK_LOGIN: {}".format(CLICK_LOCATION['LOGIN_QUICK_LOGIN']))
        self.mouse_click(CLICK_LOCATION['LOGIN_QUICK_LOGIN'])
        self.delay(BIG_WAIT)
        self.logger.info("发送坐标LOGIN_START_WAKEUP: {}".format(CLICK_LOCATION['LOGIN_START_WAKEUP']))
        self.mouse_click(CLICK_LOCATION['LOGIN_START_WAKEUP'])
        self.delay(BIG_WAIT)

