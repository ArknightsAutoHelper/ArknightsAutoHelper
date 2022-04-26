import random
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np
import textdistance

from Arknights.addons.common import CommonAddon
from app.schemadef import Field
from automator import AddonBase, cli_command, task_sched
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

class RIICAddon(AddonBase):
    def on_attach(self) -> None:
        self.sync_richlog()
        self.ocr = tesseract.Engine(lang=None, model_name='chi_sim')
        self.tag = time.time()
        self.seq = 0
    
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

    def recognize_operator_select(self, recognize_skill=False, skill_facility_hint=None) -> list[OperatorBox]:
        screenshot = self.device.screenshot(cached=False).convert('RGB')
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
                    if key not in dedup_set:
                        rc = Rect.from_xywh(x, y, 184, 411).iscale(self.scale)
                        operators.append((screenshot.subview(rc), rc))
                        dedup_set.add(key)
                else:
                    break
        operators.sort(key=lambda x: (x[1].x // (184 * self.scale // 2), x[1].y))
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
        self.logger.debug("time elapsed: %.06f s", t)
        return result

    def recognize_operator_box(self, img: Image.Image, recognize_skill=False, skill_facility_hint=None) -> OperatorBox:
        name_img = img.subview((0, 375*self.scale, img.width, img.height - 2*self.scale)).convert('L')
        name_img = imgops.enhance_contrast(name_img, 90, 220)
        name_img = imgops.crop_blackedge2(name_img, x_threshold=name_img.height * 0.3)
        name_img = Image.fromarray(cv2.copyMakeBorder(255 - name_img.array, 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=[255, 255, 255]))
        # save image for training ocr
        # name_img.save(os.path.join(config.SCREEN_SHOOT_SAVE_PATH, '%d-%04d.png' % (self.tag, self.seq)))
        self.seq += 1
        # OcrHint.SINGLE_LINE (PSM 7) will ignore some operator names, use raw line for LSTM (PSM 13) here
        # the effect of user-words is questionable, it seldom produce improved output (maybe we need LSTM word-dawg instead)
        ocrresult = self.ocr.recognize(name_img, ppi=240, tessedit_pageseg_mode='13', user_words_file='operators')
        name = ocrresult.text.replace(' ', '')
        if name not in operator_set:
            comparisions = [(n, textdistance.levenshtein(name, n)) for n in operator_set]
            comparisions.sort(key=lambda x: x[1])
            self.logger.debug('%s not in operator set, closest match: %s' % (name, comparisions[0][0]))
            if comparisions[0][1] == comparisions[1][1]:
                self.logger.warning('multiple fixes availiable for %r', ocrresult)
            name = comparisions[0][0]
        mood_img = img.subview(Rect.from_xywh(44, 358, 127, 3).iscale(self.scale)).convert('L').array
        mood_img = np.max(mood_img, axis=0)
        mask = (mood_img >= 200).astype(np.uint8)
        mood = np.count_nonzero(mask) / mask.shape[0] * 24

        on_shift = resources.load_image_cached('riic/on_shift.png', 'RGB')
        distracted = resources.load_image_cached('riic/distracted.png', 'RGB')
        rest = resources.load_image_cached('riic/rest.png', 'RGB')
        tagimg = img.subview(Rect.from_ltrb(35, 209, 155, 262).iscale(self.scale)).resize(on_shift.size)
        tag = None
        if imgops.compare_mse(tagimg, on_shift) < 3251:
            tag = 'on_shift'
        elif imgops.compare_mse(tagimg, distracted) < 3251:
            tag = 'distracted'
        elif imgops.compare_mse(tagimg, rest) < 3251:
            tag = 'rest'
        
        selected_check = np.mean(np.power(img.array[0:5].astype(np.float32) - [0, 152, 220], 2))
        self.richlogger.logtext(f'selected_check mse={selected_check}')
        selected = selected_check < 3251  # has drop shadow over it
        if selected:
            has_room_check_color = [48, 79, 93]  # blue-tinted
        else:
            has_room_check_color = [60, 60, 60]
        has_room_check = img.subview(Rect.from_xywh(111,9,10,4).iscale(self.scale))
        mse = np.mean(np.power(has_room_check.array.astype(np.float32) - has_room_check_color, 2))
        self.richlogger.logtext(f'has_room_check mse={mse}')
        if mse < 200:
            room_img = img.subview(Rect.from_xywh(42, 9, 74, 27).iscale(self.scale)).array
            room_img = imgops.enhance_contrast(Image.fromarray(np.max(room_img, axis=2)), 64, 220)
            room_img = Image.fromarray(255 - room_img.array)
            self.richlogger.logimage(room_img)
            room = self.ocr.recognize(room_img, ppi=240, hints=[ocr.OcrHint.SINGLE_LINE], char_whitelist='0123456789FB').text.replace(' ', '')
        else:
            room = None

        if recognize_skill:
            skill1_icon = img.subview(Rect.from_xywh(4,285,54,54).iscale(self.scale))
            skill2_icon = img.subview(Rect.from_xywh(67,285,54,54).iscale(self.scale))
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
        self.richlogger.logtext(repr(ocrresult))
        result = OperatorBox(None, name, mood, tag, room, skill_icons=skill_icons, selected=selected)
        self.richlogger.logtext(repr(result))
        return result

    def recognize_skill(self, icon, facility_hint=None) -> tuple[str, float]:
        self.richlogger.logimage(icon)
        skill_check = np.mean(icon.array)
        self.richlogger.logtext(f'skill_check mean={skill_check}')
        if skill_check < 60:
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
        screenshot = self.device.screenshot().convert('RGB')
        if self.match_roi('riic/clear_operator'):
            pass
        elif roi := self.match_roi('riic/operator_button', method='mse', fixed_position=False, screenshot=screenshot.subview((0, 0, screenshot.height * 0.18611, screenshot.height))):
            self.tap_rect(roi.bbox)
        self.tap_rect(self.load_roi('riic/first_operator_in_list').bbox)

    def select_operators(self, operators):
        pending_operators: list = operators[:]
        last_page_set = set()
        while True:
            current_page = self.recognize_operator_select(recognize_skill=False)
            current_page_set = set()
            for op in current_page:
                current_page_set.add(op.name)
                if op.name in pending_operators:
                    pending_operators.remove(op.name)
                    if op.selected:
                        self.logger.info(f'{op.name} 已选择')
                    else:
                        self.logger.info('选择干员：%s', op.name)
                        self.tap_rect(op.box, post_delay=0)
                else:
                    if op.selected:
                        self.logger.info(f'取消选择: {op.name}')
                        self.tap_rect(op.box, post_delay=0)
            if len(pending_operators) == 0 or current_page_set == last_page_set:
                break
            last_page_set = current_page_set
            t0 = time.perf_counter()
            self.device.input.swipe(
                random.uniform(85,90)*self.vw, random.uniform(40*self.vh, 60*self.vh),
                random.uniform(60,65)*self.vh, random.uniform(40*self.vh, 60*self.vh),
                0.3, hold_before_release=0.3, interpolation='spline')
            # self.wait_for_still_image(threshold=500, check_delay=0)
            t1 = time.perf_counter()
            self.logger.info('滑动耗时 %.3f 秒', t1-t0)
            # FIXME: overscroll animation
            time.sleep(0.6)
        if pending_operators:
            self.logger.warning('未发现干员：%r', pending_operators)


    def shift(self, room, operators):
        self.enter_operator_selection(room)
        self.select_operators(operators)
        self.logger.info('确认换班')
        self.tap_rect(self.load_roi('riic/confirm_select').bbox)
        if roi := self.match_roi('riic/confirm_shift', method='mse'):
            self.logger.info('二次确认换班')
            self.tap_rect(roi.bbox)

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
        if cmd == 'collect':
            self.collect_all()
            return 0
        if cmd == 'shift':
            room, *operators = argv[2:]
            self.shift(room, operators)
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

    @task_sched.task(category='基建', title='一键收取')
    class RIICCollectTask(task_sched.Schema):
        """收取贸易站、制造站、信赖"""
        pass

    @RIICCollectTask.handler
    def handle_task(self, task: RIICCollectTask):
        self.collect_all()

    @task_sched.task(category='基建', title='线索交流')
    class RIICClueTask(task_sched.Schema):
        """收取线索、赠送线索、开启线索交流"""
        pass

    @RIICClueTask.handler
    def handle_task(self, task: RIICClueTask):
        raise NotImplementedError

    @task_sched.task(category='基建', title='自动换班')
    class RIICShiftTask(task_sched.Schema):
        strategy = Field(str, default='', title='换班策略', doc='留空使用自带策略。自定义策略请参考开发文档。')

    @RIICShiftTask.handler
    def handle_task(self, task: RIICShiftTask):
        raise NotImplementedError