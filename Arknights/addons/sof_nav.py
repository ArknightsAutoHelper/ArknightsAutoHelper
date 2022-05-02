
import random
from automator.addon import AddonBase
from util.cvimage import Rect
from .stage_navigator import navigator
from imgreco import imgops, ocr
import cv2

stage_to_section = {
    'SN-1': 1,
    'SN-2': 1,
    'SN-3': 1,
    'SN-4': 1,
    'SN-5': 1,
    'SN-6': 2,
    'SN-7': 2,
    'SN-8': 2,
    'SN-9': 3,
    'SN-10': 3,
}

linear_maps = {
    1: ['SN-1', 'SN-2', 'SN-TR-1', 'SN-3', 'SN-4', 'SN-5'],
    2: ['SN-7', 'SN-6', 'SN-8'],
    3: ['SN-9', 'SN-10']
}

class ShipOfFoolsNavigator(AddonBase):
    @navigator
    def nav(self, stage: str):
        return stage.upper() in stage_to_section

    @nav.navigate
    def run(self, stage_code: str):
        stage_code = stage_code.upper()
        if stage_code not in stage_to_section:
            raise RuntimeError(f'无效的关卡: {stage_code}')
        self.scale = self.viewport[1] / 1080

        # 进入活动
        from .common import CommonAddon
        self.addon(CommonAddon).back_to_main()

        count = 0
        while True:
            if match := self.match_roi('maps/sof/glan_faro'):
                self.logger.info('进入活动关卡')
                self.tap_rect(match.bbox, post_delay=3)
            if section_icon := self.match_roi('maps/sof/section_icon'):
                break
            if match := self.match_roi('maps/sof/banner', fixed_position=False, method='sift'):
                self.logger.info('进入活动首页')
                self.tap_rect(match.bbox, post_delay=3)
            count += 1
            if count > 10:
                raise RuntimeError('导航失败')

        while True:
            screenshot = imgops.scale_to_height(self.device.screenshot().convert('RGB'), 1080)
            scale = self.viewport[1] / 1080
            passed_icon = self.load_roi('maps/sof/passed_stage')
            current_page_stages = {}
            tm = cv2.matchTemplate(screenshot.array, passed_icon.template.array, cv2.TM_SQDIFF_NORMED, mask=passed_icon.mask.array)
            while True:
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(tm)
                if min_val > 0.2:
                    break
                self.logger.debug('found icon at %r', min_loc)
                x, y = min_loc
                stage_code_img = screenshot.crop(Rect.from_xywh(x, y + passed_icon.template.height, passed_icon.template.width, 23)).convert('L')
                stage_code_img = imgops.enhance_contrast(stage_code_img)
                stage_code_img = imgops.crop_blackedge(stage_code_img)
                stage_code_img = imgops.invert_color(stage_code_img)
                stage_code_img = imgops.pad(stage_code_img, 6, value=255)
                self.richlogger.logimage(stage_code_img)
                stage_code_ocr = ocr.acquire_engine_global_cached('zh-cn').recognize(stage_code_img, tessedit_pageseg_mode='13', tessedit_char_whitelist='SNTR-0123456789')
                self.richlogger.logtext(stage_code_ocr)
                cv2.rectangle(tm, (x-4, y-4), (x+4, y+4), max_val, -1)
                current_page_stages[stage_code_ocr.text.replace(' ', '')] = Rect.from_xywh(x, y - 80, passed_icon.template.width, 80).scale(scale)
            self.logger.info('当前画面关卡: %r', current_page_stages)
            if stage_code in current_page_stages:
                self.tap_rect(current_page_stages[stage_code], post_delay=1)
                break
            if len(current_page_stages) == 0:
                self.swipe_left()
                continue
            target_section = stage_to_section[stage_code]
            if target_section != stage_to_section[next(iter(current_page_stages))]:
                self.logger.info('跳转到第 %d 层', target_section)
                self.tap_rect(section_icon.bbox, post_delay=1)
                self.tap_rect(self.load_roi(f'maps/sof/section{target_section}').bbox, post_delay=3)
                continue
            section_map = linear_maps[target_section]
            target_index = section_map.index(stage_code)
            known_indices = [section_map.index(x) for x in current_page_stages.keys()]
            if all(x > target_index for x in known_indices):
                self.logger.info('目标在可视区域左侧，向右拖动')
                self.swipe_right()
            elif all(x < target_index for x in known_indices):
                self.logger.info('目标在可视区域右侧，向左拖动')
                self.swipe_left()
            else:
                self.logger.error('未能定位关卡地图')
                raise RuntimeError('recognition failed')


    def swipe_left(self):
        self.device.input.swipe(random.uniform(85, 95)*self.vw, random.uniform(40, 60)*self.vh, random.uniform(5, 15)*self.vw, random.uniform(40, 60)*self.vh, move_duration=0.5, hold_before_release=0.5)

    def swipe_right(self):
        self.device.input.swipe(random.uniform(5, 15)*self.vw, random.uniform(40, 60)*self.vh, random.uniform(85, 95)*self.vw, random.uniform(40, 60)*self.vh, move_duration=0.5, hold_before_release=0.5)
