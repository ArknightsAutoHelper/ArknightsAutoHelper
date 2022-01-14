import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np
import textdistance

import config

from Arknights.addons.common import CommonAddon
from automator import AddonBase
from imgreco import imgops, resources, ocr
import imgreco.ocr.tesseract as tesseract
import util.cvimage as Image
from util.cvimage import Rect
from . import database

operator_set = set(database.operators)
operator_alphabet = ''.join(set(c for s in database.operators for c in s))

@dataclass
class OperatorBox:
    box: Rect
    name: str
    mood: float
    status: str
    room: Optional[str]
    skill_icons: list[str]

def transform_rect(rc, M):
    l, t, r, b = rc
    pts = np.asarray([l,t, r,t, r,b, l,b], dtype=np.float32).reshape(-1, 1, 2)
    tpts: np.ndarray = cv2.transform(pts, M).reshape(-1, 2)
    left = int(round(tpts[:, 0].min()))
    top = int(round(tpts[:, 1].min()))
    right = int(round(tpts[:, 0].max()))
    bottom = int(round(tpts[:, 1].max()))
    return left, top, right, bottom

class RIICAddon(AddonBase):
    def on_attach(self) -> None:
        self.ocr = tesseract.Engine(lang=None, model_name='chi_sim')
        self.register_cli_command('riic', self.cli_riic, self.cli_riic.__doc__)
        self.tag = time.time()
        self.seq = 0
    
    def check_in_riic(self, screenshot=None):
        if self.match_roi('riic/overview', screenshot=screenshot):
            return True
        if roi := self.match_roi('riic/pending', screenshot=screenshot):
            self.logger.info('取消待办事项')
            self.tap_rect(roi.bbox)
            return True
        return False

    def enter_riic(self):
        self.addon(CommonAddon).back_to_main(extra_predicate=self.check_in_riic)
        if self.check_in_riic():
            return
        result = self.match_roi('riic/riic_entry', fixed_position=False, method='sift', mode='L')
        if result:
            self.logger.info('进入基建')
            self.tap_quadrilateral(result.context.template_corners, post_delay=6)
        else:
            raise RuntimeError('failed to find riic entry')
        while not self.check_in_riic():
            self.delay(1)
        self.logger.info('已进入基建')
        
    def collect_all(self):
        self.enter_riic()
        count = 0
        while count < 2:
            if roi := self.match_roi('riic/notification', fixed_position=False, method='template_matching'):
                while True:
                    self.logger.info('发现蓝色通知')
                    self.tap_rect(roi.bbox)
                    if self.match_roi('riic/pending'):
                        break
                    self.logger.info('重试点击蓝色通知')
                while roi := self.wait_for_roi('riic/collect_all', timeout=2, fixed_position=False, method='template_matching'):
                    self.logger.info('发现全部收取按钮')
                    rc = roi.bbox
                    rc.y = 93.704 * self.vh
                    rc.height = 5.833 * self.vh
                    rc.x -= 7.407 * self.vh
                    self.tap_rect(roi.bbox)
                break
            else:
                self.logger.info('未发现蓝色通知，等待 3 s')
                self.delay(3)
                count += 1
        self.logger.info('一键收取完成')

    def recognize_layout(self):
        self.enter_riic()
        self.logger.info('正在识别基建布局')
        screenshot = self.device.screenshot()
        
        t0 = time.monotonic()
        # screen_mask = None
        templ_mask = resources.load_image_cached('riic/layout.mask.png', 'L').array
        left_mask = imgops.scale_to_height(resources.load_image_cached('riic/layout.screen_mask.left.png', 'L'), screenshot.height, Image.NEAREST)
        right_mask = imgops.scale_to_height(resources.load_image_cached('riic/layout.screen_mask.right.png', 'L'), screenshot.height, Image.NEAREST)
        screen_mask = np.concatenate([left_mask.array, np.full((screenshot.height, screenshot.width - left_mask.width - right_mask.width), 255, dtype=np.uint8), right_mask.array], axis=1)
        match = imgops.match_feature_orb(resources.load_image_cached('riic/layout.png', 'L'), screenshot.convert('L'), templ_mask=templ_mask, haystack_mask=screen_mask, limited_transform=True)
        # roi = self.match_roi('riic/layout', fixed_position=False, method='sift', mode='L')
        self.logger.debug('%r', match)
        if match.M is None:
            raise RuntimeError('未能识别基建布局')
        # discard rotation
        M = match.M
        scalex = np.sqrt(M[0,0] ** 2 + M[0,1] ** 2)
        scaley = np.sqrt(M[1,0] ** 2 + M[1,1] ** 2)
        translatex = M[0,2]
        translatey = M[1,2]
        scale = (scalex+scaley)/2
        M = np.array([[scale, 0, translatex],[0, scale, translatey]])
        print('M=', M)
        layout = {
            name: transform_rect(rect, M)
            for name, rect in database.layout_template.items()
        }
        t1 = time.monotonic()
        print('time elapsed:', t1-t0)
        image = screenshot.convert('native')

        for name, rect in layout.items():
            cv2.rectangle(image.array, Rect.from_ltrb(*rect).xywh, [0, 0, 255], 1)
            cv2.putText(image.array, name, [rect[0]+2, rect[3]-2], cv2.FONT_HERSHEY_PLAIN, 2, [0,0,255], 2)

        image.show()
        print(layout)

    def recognize_operator_select(self, recognize_skill=False, skill_facility_hint=None):
        screenshot = self.device.screenshot().convert('RGB')
        if not (roi := self.match_roi('riic/clear_selection', screenshot=screenshot)):
            raise RuntimeError('not here')
        # self.tap_rect(roi.bbox, post_delay=0)
        t0 = time.monotonic()
        screenshot = imgops.scale_to_height(screenshot, 1080)

        highlighted_check = screenshot.subview((605, 530, screenshot.width, 538))
        self.richlogger.logimage(highlighted_check)

        if (highlighted_check.array == (0, 152, 220)).all(axis=-1).any():
            self.logger.info('取消选中干员')
            self.tap_rect(roi.bbox, post_delay=0.2)  # transition animation
            screenshot = imgops.scale_to_height(self.device.screenshot(cached=False).convert('RGB'), 1080)
        dbg_screen = screenshot.copy()
        xs = []
        operators = []
        cropim = screenshot.array[485:485+37]
        cropim = cv2.cvtColor(cropim, cv2.COLOR_RGB2GRAY)
        thim = cv2.threshold(cropim, 55, 1, cv2.THRESH_BINARY)[1]
        ysum = np.sum(thim, axis=0).astype(np.int16)
        ysumdiff=np.diff(ysum)
        row1xs = np.where(ysumdiff<=ysumdiff.min()+3)[0] + 1

        for x in row1xs:
            if x < 605 or x + 184 > screenshot.width:
                continue
            rc = Rect.from_xywh(x, 113, 184, 411)
            operators.append((screenshot.subview(rc), rc))

        cropim = screenshot.array[909:909+36]
        cropim = cv2.cvtColor(cropim, cv2.COLOR_RGB2GRAY)
        thim = cv2.threshold(cropim, 55, 1, cv2.THRESH_BINARY)[1]
        ysum = np.sum(thim, axis=0).astype(np.int16)
        ysumdiff=np.diff(ysum)
        row2xs = np.where(ysumdiff<=ysumdiff.min()+3)[0] + 1

        for x in row2xs:
            if x < 605 or x + 184 > screenshot.width:
                continue
            rc = Rect.from_xywh(x, 534, 184, 411)
            operators.append((screenshot.subview(rc), rc))

        # for color in ('green', 'yellow', 'red'):
        #     face = resources.load_image_cached(f'riic/{color}_face.png', 'RGB')
        #     w, h = face.size
        #     res = cv2.matchTemplate(screenshot.array, face.array, cv2.TM_CCOEFF_NORMED)
        #     while True:
        #         min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        #         if max_val > 0.9:
        #             xs.append(max_loc[0] - 14)
        #             res[max_loc[1]-h//2:max_loc[1]+h//2+1, max_loc[0]-w//2:max_loc[0]+w//2+1] = 0
        #             operators.append(screenshot.subview((max_loc[0] - 14, max_loc[1] - 345, max_loc[0] + 170, max_loc[1] + 66)))
        #         else:
        #             break
        for o, rc in operators:
            cv2.rectangle(dbg_screen.array, rc.xywh, [255,0,0, 1])
        self.richlogger.logimage(dbg_screen)
        result = []
        for o, rc in operators:
            self.richlogger.logimage(o)
            box = self.recognize_operator_box(o, recognize_skill, skill_facility_hint)
            box.box = rc
            result.append(box)
        # xs = np.array(xs)
        # xs.sort()
        # diffs = np.diff(xs)

        # dedup_xs = xs[np.concatenate(([183], diffs)) > 5]
        # for x in dedup_xs:
        #     cv2.line(dbg_screen.array, (x,0), (x,screenshot.height), [255,0,0], 1)
        # dbg_screen.show()
        t = time.monotonic() - t0
        print("time elapsed:", t)
        return result

    def recognize_operator_box(self, img: Image.Image, recognize_skill=False, skill_facility_hint=None):
        name_img = img.subview((0, 375, img.width, img.height - 2)).convert('L')
        # name_img = imgops.enhance_contrast(name_img, 90, 220)
        name_img = Image.fromarray(cv2.threshold(name_img.array, 127, 255, cv2.THRESH_BINARY_INV)[1])
        # name_img = Image.fromarray(255 - name_img.array)
        # save image for training ocr
        # name_img.save(os.path.join(config.SCREEN_SHOOT_SAVE_PATH, '%d-%04d.png' % (self.tag, self.seq)))
        self.seq += 1
        # OcrHint.SINGLE_LINE (PSM 7) will ignore some operator names, use raw line for LSTM (PSM 13) here
        # the effect of user-words is questionable, it seldom produce improved output (maybe we need LSTM word-dawg instead)
        ocrresult = self.ocr.recognize(name_img, ppi=240, tessedit_pageseg_mode='13', user_words_suffix='operators-user-words', tessedit_char_whitelist=operator_alphabet)
        name = ocrresult.text.replace(' ', '')
        if name not in operator_set:
            comparisions = [(n, textdistance.levenshtein(name, n)) for n in operator_set]
            comparisions.sort(key=lambda x: x[1])
            self.logger.debug('%s not in operator set, closest match: %s', name, comparisions[0][0])
            if comparisions[0][1] == comparisions[1][1]:
                self.logger.warning('multiple fixes availiable for %r', ocrresult)
            name = comparisions[0][0]
        mood_img = img.subview(Rect.from_xywh(44, 358, 127, 3)).convert('L').array
        mood_img = np.max(mood_img, axis=0)
        mask = (mood_img >= 200).astype(np.uint8)
        mood = np.count_nonzero(mask) / mask.shape[0] * 24

        tagimg = img.subview((35, 209, 155, 262))
        on_shift = resources.load_image_cached('riic/on_shift.png', 'RGB')
        distracted = resources.load_image_cached('riic/distracted.png', 'RGB')
        rest = resources.load_image_cached('riic/rest.png', 'RGB')
        tag = None
        if imgops.compare_mse(tagimg, on_shift) < 3251:
            tag = 'on_shift'
        elif imgops.compare_mse(tagimg, distracted) < 3251:
            tag = 'distracted'
        elif imgops.compare_mse(tagimg, rest) < 3251:
            tag = 'rest'
        
        has_room_check = img.subview(Rect.from_xywh(45,2,62,6)).convert('L')
        mse = np.mean(np.power(has_room_check.array.astype(np.float32) - 50, 2))
        self.richlogger.logtext(f'has_room_check mse={mse}')
        if mse < 200:
            room_img = img.subview(Rect.from_xywh(42, 6, 74, 30)).array
            room_img = imgops.enhance_contrast(Image.fromarray(np.max(room_img, axis=2)), 64, 220)
            room_img = Image.fromarray(255 - room_img.array)
            self.richlogger.logimage(room_img)
            room = self.ocr.recognize(room_img, ppi=240, hints=[ocr.OcrHint.SINGLE_LINE], char_whitelist='0123456789FB').text.replace(' ', '')
        else:
            room = None

        if recognize_skill:
            skill1_icon = img.subview(Rect.from_xywh(4,285,54,54))
            skill2_icon = img.subview(Rect.from_xywh(67,285,54,54))
            skill1, score1 = self.recognize_skill(skill1_icon, skill_facility_hint)
            skill2, score2 = self.recognize_skill(skill2_icon, skill_facility_hint)
        else:
            skill1 = None
            skill2 = None

        skill_icons = []
        if skill1 is not None:
            skill_icons.append(skill1)
        if skill2 is not None:
            skill_icons.append(skill2)
        self.richlogger.logimage(name_img)
        result = OperatorBox(None, name, mood, tag, room, skill_icons=skill_icons)
        self.richlogger.logtext(repr(result))
        return result

    def recognize_skill(self, icon, facility_hint=None) -> tuple[str, float]:
        self.richlogger.logimage(icon)
        if np.max(icon.array) < 120:
            self.richlogger.logtext('no skill')
            return None, 114514
        from . import bskill_cache
        icon = icon.resize(bskill_cache.icon_size)

        if facility_hint is not None:
            normal_filter = lambda name: name.startswith('Bskill_'+facility_hint)
            dark_filter = lambda name: not normal_filter(name)
        else:
            normal_filter = lambda x: True
            dark_filter = lambda x: True
        
        normal_comparisons = [(name, imgops.compare_ccoeff(icon, template)) for name, template in bskill_cache.normal_icons.items() if normal_filter(name)]
        normal_comparisons.sort(key=lambda x: -x[1])

        if not normal_comparisons:
            result = None, 0
        else:
            result = normal_comparisons[0]
            self.richlogger.logtext('normal icons set: ' + repr(normal_comparisons[:3]))
        if result[1] < 0.8:
            dark_comparisons = [(name, imgops.compare_ccoeff(icon, template)) for name, template in bskill_cache.dark_icons.items() if dark_filter(name)]
            dark_comparisons.sort(key=lambda x: -x[1])
            self.richlogger.logtext('dark icons set: ' + repr(dark_comparisons[:3]))
            if dark_comparisons and dark_comparisons[0][1] < result[1]:
                result = dark_comparisons[0]

        if result[1] < 0.8:
            self.richlogger.logtext('no match')
            return None, 0

        self.richlogger.logtext(f'matched {result[0]} with ccoeff {result[1]}')

        return result

    def cli_riic(self, argv):
        """
        riic <subcommand>
        基建功能（开发中）
        riic collect
        收取制造站及贸易站
        """
        if len(argv) == 1:
            print("usage: riic <subcommand>")
            return 1
        cmd = argv[1]
        if cmd == 'collect':
            self.collect_all()
            return 0
        elif cmd == 'debug_list':
            from pprint import pprint
            def warmup():
                return self.recognize_operator_select(recognize_skill=True)
            def bench():
                return self.recognize_operator_select(recognize_skill=True)
            # for i in range(100):
                # self.recognize_operator_select(recognize_skill=True)
                # self.swipe_screen(-200)
            # self.recognize_operator_select(recognize_skill=True)
            pprint(warmup())
            pprint(bench())

        elif cmd == 'debug_layout':
            self.recognize_layout()
        else:
            print("unknown command:", cmd)
            return 1