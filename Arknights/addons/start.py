import re
from .common import CommonAddon
from automator.addon import AddonBase, cli_command

focus_re = re.compile(r'Window\{[0-9a-f]+ u\d+ ([a-zA-Z0-9\.]+)/([a-zA-Z0-9\.]+)\}')

class StartAddon(AddonBase):
    @cli_command('start')
    def start(self):
        focus = self.device.run_device_cmd('dumpsys window | grep mCurrentFocus').decode('utf-8', errors='ignore')
        match = focus_re.search(focus)
        focus_package_name = match.group(1)
        if focus_package_name != 'com.hypergryph.arknights':
            # FIXME: bilibili server
            self.logger.info('启动游戏')
            self.device.run_device_cmd('am start com.hypergryph.arknights/com.u8.sdk.U8UnityContext')
        else:
            self.logger.info('游戏已启动')
            self.addon(CommonAddon).back_to_main()
            return
            
        while True:
            # FIXME: 未覆盖所有情况（如客户端更新）
            if match := self.match_roi('start/start1'):
                self.logger.info('START 图标')
                self.tap_rect(match.bbox)
                continue
            if match := self.match_roi('start/networking_wait'):
                self.logger.info('等待网络')
                self.delay(3)
                continue
            if match := self.match_roi('start/saved_login'):
                self.logger.info('开始唤醒')
                self.tap_rect(match.bbox)
                continue
            if match := self.match_roi('start/new_login'):
                self.logger.info('账号登录')
                self.tap_rect(match.bbox)
                raise NotImplementedError('username/password')
            from imgreco.common import recognize_dialog, get_dialog_ok_button_rect, get_dialog_right_button_rect, get_dialog_left_button_rect
            screenshot = self.device.screenshot().convert('RGB')
            dlgtype, dlgocr = recognize_dialog(screenshot)
            if dlgtype == 'ok':
                self.logger.info('对话框：%s', dlgocr.text)
                self.tap_rect(get_dialog_ok_button_rect(screenshot))
                continue
            elif dlgtype == 'yesno':
                self.logger.info('对话框：%s', dlgocr.text)
                if 'MB' in dlgocr:
                    self.tap_rect(get_dialog_right_button_rect(screenshot))
                else:
                    self.tap_rect(get_dialog_left_button_rect(screenshot))
                continue
            self.addon(CommonAddon).back_to_main()
