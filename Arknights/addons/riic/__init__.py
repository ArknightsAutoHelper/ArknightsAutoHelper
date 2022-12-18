import random
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np
import textdistance

from Arknights.addons.common import CommonAddon
from automator import AddonBase, cli_command
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
    selected: bool = False

def transform_rect(rc, M):
    l, t, r, b = rc
    pts = np.asarray([l,t, r,t, r,b, l,b], dtype=np.float32).reshape(-1, 1, 2)
    tpts: np.ndarray = cv2.transform(pts, M).reshape(-1, 2)
    left = int(round(tpts[:, 0].min()))
    top = int(round(tpts[:, 1].min()))
    right = int(round(tpts[:, 0].max()))
    bottom = int(round(tpts[:, 1].max()))
    return left, top, right, bottom

def batch_compare_mse_alpha(roi, roi_mask, stacked_templates):
    stack = stacked_templates[..., :-1]
    while stack.shape[-1] == 1:
        stack = stack.reshape(stack.shape[:-1])
    stack_mask = stacked_templates[..., -1]
    all_diff = stack - roi
    all_diff[stack_mask == 0] = 0
    all_diff[:, roi_mask == 0] = 0
    np.square(all_diff, out=all_diff)
    all_mse = np.average(all_diff, axis=tuple(range(len(all_diff.shape)))[1:])
    return all_mse

def batch_compare_mse(roi, stacked_templates):
    all_diff = stacked_templates - roi
    np.square(all_diff, out=all_diff)
    all_mse = np.average(all_diff, axis=tuple(range(len(all_diff.shape)))[1:])
    return all_mse

def deblend(image, blend_color, blend_alpha, dtype=np.uint8):
    blend = np.asarray(image).astype(np.float32)
    blend_alpha = np.float32(blend_alpha)
    base = (blend - np.asarray(blend_color).astype(np.float32) * blend_alpha) / (1 - blend_alpha)
    return np.clip(base, 0, 255, base).astype(dtype, copy=False)

class RIICAddon(AddonBase):
    def on_attach(self) -> None:
        self.sync_richlog()
        self.ocr = tesseract.Engine(lang=None, model_name='chi_sim')
        self.tag = time.time()
        self.seq = 0
        self.skin_table = None
    
    def refresh_cache(self):
        t0 = time.perf_counter()
        from Arknights.gamedata_loader import load_table
        new_skin_table = load_table('skin_table')
        if self.skin_table is not new_skin_table:
            self.portrait_to_char = {x['portraitId'].lower(): x['charId'] for x in new_skin_table['charSkins'].values() if x.get('portraitId')}
            self.skin_table = new_skin_table
        self.character_table = load_table('character_table')
        from . import riic_resource
        riic_resource.refresh_pack()
        t1 = time.perf_counter()
        self.logger.debug('cache refreshed in %.03f ms', (t1-t0)*1000)

    def check_in_riic(self, screenshot=None):
        if self.match_roi('riic/overview', method='template_matching', screenshot=screenshot):
            return True
        if roi := self.match_roi('riic/pending', method='template_matching', screenshot=screenshot):
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
            if roi := self.match_roi('riic/notification2', fixed_position=False, method='mse'):
                while True:
                    self.logger.info('发现蓝色通知')
                    self.tap_rect(roi.bbox)
                    if self.match_roi('riic/pending'):
                        break
                    self.logger.info('重试点击蓝色通知')
                while roi := self.wait_for_roi('riic/collect_all2', timeout=2, fixed_position=False, method='mse'):
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
        if not self.check_in_riic():
            raise RuntimeError('not here')
        self.logger.info('正在识别基建布局')
        screenshot = self.screenshot()
        
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
        # print('M=', M)
        layout = {
            name: transform_rect(rect, M)
            for name, rect in database.layout_template.items()
        }
        t1 = time.monotonic()
        self.logger.debug('time elapsed: %.06f s', t1-t0)
        image = screenshot.convert('BGR')

        for name, rect in layout.items():
            cv2.rectangle(image.array, Rect.from_ltrb(*rect).xywh, (0, 0, 255), 1)
            cv2.putText(image.array, name, [rect[0]+2, rect[3]-2], cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)

        self.richlogger.logimage(image)
        # image.show()
        # print(layout)
        return layout

    def recognize_operator_select(self, full_recognize=False, skill_facility_hint=None) -> list[OperatorBox]:
        screenshot = self.screenshot(cached=False).convert('RGB')
        self.scale = screenshot.height / 1080
        if not (roi := self.match_roi('riic/sort_button', screenshot=screenshot)):
            raise RuntimeError('not here')
        # self.tap_rect(roi.bbox, post_delay=0)
        t0 = time.monotonic()
        scaled_screenshot = imgops.scale_to_height(screenshot, 1080)
        dbg_screen = screenshot.copy()
        xs = []
        operators = []
        # cropim = screenshot.array[485:485+37]
        # cropim = cv2.cvtColor(cropim, cv2.COLOR_RGB2GRAY)
        # thim = cv2.threshold(cropim, 55, 1, cv2.THRESH_BINARY)[1]
        # ysum = np.sum(thim, axis=0).astype(np.int16)
        # ysumdiff=np.diff(ysum)
        # row1xs = np.where(ysumdiff<=ysumdiff.min()+3)[0] + 1

        # for x in row1xs:
        #     if x < 605 or x + 184 > screenshot.width:
        #         continue
        #     rc = Rect.from_xywh(x, 113, 184, 411)
        #     operators.append((screenshot.subview(rc), rc))

        # cropim = screenshot.array[909:909+36]
        # cropim = cv2.cvtColor(cropim, cv2.COLOR_RGB2GRAY)
        # thim = cv2.threshold(cropim, 55, 1, cv2.THRESH_BINARY)[1]
        # ysum = np.sum(thim, axis=0).astype(np.int16)
        # ysumdiff=np.diff(ysum)
        # row2xs = np.where(ysumdiff<=ysumdiff.min()+3)[0] + 1

        # for x in row2xs:
        #     if x < 605 or x + 184 > screenshot.width:
        #         continue
        #     rc = Rect.from_xywh(x, 534, 184, 411)
        #     operators.append((screenshot.subview(rc), rc))

        img2find = np.concatenate([scaled_screenshot.array[455:492, 605:], scaled_screenshot.array[876:913, 605:]], axis=0)
        dedup_set = set()
        for color in ('green', 'yellow', 'red'):
            face = resources.load_image_cached(f'riic/{color}_face.png', 'RGB')
            w, h = face.size
            res = cv2.matchTemplate(img2find, face.array, cv2.TM_CCOEFF_NORMED)
            while True:
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if max_val > 0.9:
                    cv2.rectangle(res, (max_loc[0]-4, max_loc[1]-4), (max_loc[0]+4, max_loc[1]+4), 0, -1)
                    # res[max_loc[1]-4:max_loc[1]+4+1, max_loc[0]-4:max_loc[0]+4+1] = 0
                    x = max_loc[0] - 14 + 605
                    if x < 605 or x + 184 > scaled_screenshot.width:
                        continue
                    xs.append(x)
                    if max_loc[1] < img2find.shape[0] // 2:
                        y = 113
                    else:
                        y = 534
                    key = (round(x/(184/2)), y)
                    # print(key)
                    if key not in dedup_set:
                        rc = Rect.from_xywh(x, y, 184, 411).iscale(self.scale)
                        operators.append((screenshot.subview(rc), rc, color))
                        dedup_set.add(key)
                else:
                    break
        operators.sort(key=lambda x: (x[1].x // (184 * self.scale // 2), x[1].y))
        for o, rc, color in operators:
            cv2.rectangle(dbg_screen.array, rc.xywh, [255,0,0, 1])
        self.richlogger.logimage(dbg_screen)
        result = []
        for o, rc, color in operators:
            self.richlogger.logimage(o)
            box = self.recognize_operator_box(o, full_recognize, color)
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
        self.richlogger.logtext(f"time elapsed: {t:.06f} s")
        return result

    def match_box_portrait(self, boximg: Image.Image, red_hint=False):
        from .riic_resource import portrait_mask_64, portrait_names, portrait_maskclip_stack, portrait_mask_64_clipbox, portrait_mask_64_clip
        portrait2match = boximg.subview(Rect.from_ltrb(5,15,183,370)).resize(portrait_mask_64.size, Image.BILINEAR).subview(portrait_mask_64_clipbox)
        if red_hint:
            portrait2match = Image.fromarray(deblend(portrait2match.array, [100, 0, 0], 0.5), 'RGB')
            self.richlogger.logimage(portrait2match)
        mse_stack = batch_compare_mse_alpha(portrait2match.convert('L').array, portrait_mask_64_clip.array[..., 3], portrait_maskclip_stack)
        minidx = np.argmin(mse_stack)
        self.richlogger.logtext(f'max mse={mse_stack.max()}')
        return portrait_names[minidx], mse_stack[minidx]

    def recognize_operator_box(self, img: Image.Image, full_recognize=False, face_hint=None) -> OperatorBox:
        t00 = time.perf_counter()

        selected_check = np.mean(np.power(img.array[0:5].astype(np.float32) - [0, 152, 220], 2))
        self.richlogger.logtext(f'selected_check mse={selected_check}')
        selected = selected_check < 3251  # has drop shadow over it

        if selected:
            img = Image.fromarray(deblend(img.array, [0, 152, 220], 0.2), 'RGB')
            self.richlogger.logimage(img)

        name_img = img.subview((0, 375*self.scale, img.width, img.height - 2*self.scale)).convert('L')
        name_img = imgops.enhance_contrast(name_img, 90, 220)
        name_img = imgops.crop_blackedge2(name_img, x_threshold=name_img.height * 0.3)
        name_img = Image.fromarray(cv2.copyMakeBorder(255 - name_img.array, 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=[255, 255, 255]))
        # save image for training ocr
        # name_img.save(os.path.join(config.SCREEN_SHOOT_SAVE_PATH, '%d-%04d.png' % (self.tag, self.seq)))
        self.seq += 1

        # OcrHint.SINGLE_LINE (PSM 7) will ignore some operator names, use raw line for LSTM (PSM 13) here
        # the effect of user-words is questionable, it seldom produce improved output (maybe we need LSTM word-dawg instead)
        # ocrresult = self.ocr.recognize(name_img, ppi=240, tessedit_pageseg_mode='13', user_words_file='operators')
        # name = ocrresult.text.replace(' ', '')
        # if name not in operator_set:
        #     comparisions = [(n, textdistance.levenshtein(name, n)) for n in operator_set]
        #     comparisions.sort(key=lambda x: x[1])
        #     self.logger.debug('%s not in operator set, closest match: %s' % (name, comparisions[0][0]))
        #     if comparisions[0][1] == comparisions[1][1]:
        #         self.logger.warning('multiple fixes availiable for %r', ocrresult)
        #     name = comparisions[0][0]
        if face_hint == 'green':
            mood = 24.0
        else:
            mood_img = img.subview(Rect.from_xywh(44, 358, 127, 3).iscale(self.scale)).convert('L').array
            mood_img = np.max(mood_img, axis=0)
            mask = (mood_img >= 200).astype(np.uint8)
            mood = np.count_nonzero(mask) / mask.shape[0] * 24

        on_shift = resources.load_image_cached('riic/on_shift.png', 'RGB')
        distracted = resources.load_image_cached('riic/distracted.png', 'RGB')
        rest = resources.load_image_cached('riic/rest.png', 'RGB')
        tagimg = img.subview(Rect.from_ltrb(35, 209, 155, 262).iscale(self.scale)).resize(on_shift.size, Image.BILINEAR)
        tag = None
        if imgops.compare_mse(tagimg, on_shift) < 3251:
            tag = 'on_shift'
        elif imgops.compare_mse(tagimg, distracted) < 3251:
            tag = 'distracted'
        elif imgops.compare_mse(tagimg, rest) < 3251:
            tag = 'rest'
        
        has_room_check_color = [60, 60, 60]
        room = None

        t0 = time.perf_counter()
        portrait_id, mse = self.match_box_portrait(img, face_hint == 'red')
        t = time.perf_counter() - t0
        self.richlogger.logtext(f'matched {portrait_id} with {mse=} in {t*1000} ms')

        if full_recognize:
            t0 = time.perf_counter()
            skill1_icon = img.subview(Rect.from_xywh(4,285,54,54).iscale(self.scale))
            skill2_icon = img.subview(Rect.from_xywh(67,285,54,54).iscale(self.scale))
            skill1, score1 = self.recognize_skill(skill1_icon)
            skill2, score2 = self.recognize_skill(skill2_icon)
            t = time.perf_counter() - t0
            self.richlogger.logtext(f'skill recognized in {t*1000} ms')

            has_room_check = img.subview(Rect.from_xywh(111,9,10,4).iscale(self.scale))
            mse = np.mean(np.power(has_room_check.array.astype(np.float32) - has_room_check_color, 2))
            self.richlogger.logtext(f'has_room_check mse={mse}')
            if mse < 200:
                room_img = img.subview(Rect.from_xywh(42, 9, 74, 27).iscale(self.scale)).array
                room_img = imgops.enhance_contrast(Image.fromarray(np.max(room_img, axis=2)), 64, 220)
                room_img = Image.fromarray(255 - room_img.array)
                self.richlogger.logimage(room_img)
                from imgreco.ocr.ppocr import ocr_for_single_line
                room = ocr_for_single_line(room_img.convert('RGB').array, '0123456789FB')
                # room = self.ocr.recognize(room_img, ppi=240, hints=[ocr.OcrHint.SINGLE_LINE], char_whitelist='0123456789FB').text.replace(' ', '')

        else:
            skill1 = None
            skill2 = None

        skill_icons = []
        if skill1 is not None:
            skill_icons.append(skill1)
        if skill2 is not None:
            skill_icons.append(skill2)
        # self.richlogger.logimage(name_img)
        # self.richlogger.logtext(repr(ocrresult))
        name = self.character_table[self.portrait_to_char[portrait_id.lower()]]['name']
        result = OperatorBox(None, name, mood, tag, room, skill_icons=skill_icons, selected=selected)
        t01 = time.perf_counter()
        self.richlogger.logtext(repr(result))
        self.richlogger.logtext(f'box recognized in {(t01-t00)*1000} ms')
        return result

    def recognize_skill(self, icon) -> tuple[str, float]:
        self.richlogger.logimage(icon)
        skill_check_mean = np.mean(icon.array)
        skill_check_max = np.max(icon.array)
        self.richlogger.logtext(f'{skill_check_mean=} {skill_check_max=}')
        if skill_check_mean < 60 and skill_check_max < 125:
            self.richlogger.logtext('no skill')
            return None, 114514
        from . import riic_resource
        icon = icon.resize(riic_resource.icon_size, Image.BILINEAR)
        
        if skill_check_max > 200:
            self.richlogger.logtext('using stack normal_icons_stack')
            use_stack = riic_resource.normal_icons_stack
        else:
            self.richlogger.logtext('using stack dark_icons_stack')
            use_stack = riic_resource.dark_icons_stack

        msestack = batch_compare_mse(icon, use_stack)
        match_idx = np.argmin(msestack)
        result = (riic_resource.icon_names[match_idx], msestack[match_idx])
        
        # normalized_icon = icon.array.astype(np.float32)
        # normalized_icon = normalized_icon / (normalized_icon.max() / 255.0)
        # normalized_msestack = batch_compare_mse(normalized_icon, bskill_cache.normalized_icons_stack)
        # normalized_match_idx = np.argmin(normalized_msestack)
        # normalized_match = (bskill_cache.icon_names[normalized_match_idx], normalized_msestack[normalized_match_idx])

        # self.richlogger.logtext('normalized match: ' + repr(normalized_match))

        if result[1] > 800:
            self.richlogger.logtext('no match')
            return None, 0

        self.richlogger.logtext(f'matched {result[0]} with mse {result[1]}')

        return result

    def enter_room(self, room):
        self.enter_riic()
        self.logger.info(f'进入房间 {room}')
        layout = self.recognize_layout()
        left, top, right, bottom = layout[room]
        if left < 0:
            left = 0
        if top < 0:
            top = 0
        if right > self.viewport[0]:
            right = self.viewport[0]
        if bottom > self.viewport[1]:
            bottom = self.viewport[1]
        rect = Rect.from_ltrb(left, top, right, bottom)
        self.logger.info(f'{room} @ {rect!r}')
        if rect.width <= 0 or rect.height <= 0:
            raise ValueError('invalid rect')
        self.tap_rect(rect)
        if self.check_in_riic():
            self.logger.info('等待收取提示消失')
            self.delay(3)
            self.tap_rect(rect)

    def enter_operator_selection(self, room='dorm1'):
        self.enter_room(room)
        screenshot = self.screenshot().convert('RGB')
        if self.match_roi('riic/clear_operator'):
            pass
        elif roi := self.match_roi('riic/operator_button', method='mse', fixed_position=False, screenshot=screenshot.subview((0, 0, screenshot.height * 0.18611, screenshot.height))):
            self.tap_rect(roi.bbox)
        self.tap_rect(self.load_roi('riic/first_operator_in_list').bbox)

    def select_operators(self, operators):
        pending_operators: list = operators[:]
        for current_page in self.iter_operator_list_pages():
            current_page = self.recognize_operator_select(full_recognize=False)
            for op in current_page:
                if op.name in pending_operators:
                    pending_operators.remove(op.name)
                    if op.selected:
                        self.logger.info(f'{op.name} 已选择')
                    else:
                        self.logger.info('选择干员：%s', op.name)
                        self.tap_rect(op.box, post_delay=0)
                elif op.name not in operators:
                    if op.selected:
                        self.logger.info(f'取消选择: {op.name}')
                        self.tap_rect(op.box, post_delay=0)
            if len(pending_operators) == 0:
                break
        if pending_operators:
            self.logger.warning('未发现干员：%r', pending_operators)

    def iter_operator_list_pages(self, full_recognize=False):
        last_page_set = set()
        while True:
            current_page = self.recognize_operator_select(full_recognize=full_recognize)
            current_page_set = set()
            for op in current_page:
                current_page_set.add(op.name)
            if current_page_set == last_page_set:
                break
            yield current_page
            last_page_set = current_page_set
            t0 = time.perf_counter()
            self.control.input.touch_swipe(
                random.uniform(85,90)*self.vw, random.uniform(40*self.vh, 60*self.vh),
                random.uniform(60,65)*self.vh, random.uniform(40*self.vh, 60*self.vh),
                0.3, hold_before_release=0.3, interpolation='spline')
            # self.wait_for_still_image(threshold=500, check_delay=0)
            t1 = time.perf_counter()
            # self.logger.info('滑动耗时 %.3f 秒', t1-t0)
            # FIXME: overscroll animation
            time.sleep(0.6)

    def shift(self, room, operators):
        self.enter_operator_selection(room)
        self.select_operators(operators)
        self.logger.info('确认换班')
        self.tap_rect(self.load_roi('riic/confirm_select').bbox)
        if roi := self.match_roi('riic/confirm_shift', method='mse'):
            self.logger.info('二次确认换班')
            self.tap_rect(roi.bbox)

    def populate(self):
        self.enter_operator_selection()
        from pprint import pprint
        for page in self.iter_operator_list_pages(True):
            for box in page:
                print(box)

    @cli_command('riic')
    def cli_riic(self, argv):
        """
        riic <subcommand>
        基建功能（开发中）
        riic collect
        收取制造站及贸易站
        riic shift <room> <operator1> <operator2> ...
        指定干员换班
        room: B101 B102 B103 B201 B202 B203 B301 B302 B303 dorm1 dorm2 dorm3 dorm4 meeting workshop office
        """
        if len(argv) == 1:
            print("usage: riic <subcommand>")
            return 1
        cmd = argv[1]
        self.refresh_cache()
        self.refresh_cache()
        if cmd == 'collect':
            self.collect_all()
            return 0
        if cmd == 'shift':
            room, *operators = argv[2:]
            self.shift(room, operators)
        elif cmd == 'debug_list':
            from pprint import pprint
            def warmup():
                return self.recognize_operator_select(full_recognize=True)
            def bench():
                return self.recognize_operator_select(full_recognize=True)
            # for i in range(100):
                # self.recognize_operator_select(recognize_skill=True)
                # self.swipe_screen(-200)
            # self.recognize_operator_select(recognize_skill=True)
            warmup()
            page = bench()
            for box in page:
                print(box)
        elif cmd == 'populate':
            self.populate()
        elif cmd == 'debug_layout':
            self.recognize_layout()
        else:
            print("unknown command:", cmd)
            return 1
