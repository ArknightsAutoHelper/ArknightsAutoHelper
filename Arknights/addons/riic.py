import time
import numpy as np
import cv2

from Arknights.addons.common import CommonAddon
from automator import AddonBase
import imgreco.imgops
import imgreco.resources
import util.cvimage as Image
from util.cvimage import Rect

layout_template = {
    'control_center': (516, 9, 786, 144),
    'meeting_room': (820, 77, 1022, 144),

    'B101':(76.5, 144.5, 210.5, 211),
    'B102':(211.75, 144.5, 345.75, 211),
    'B103':(347, 144.5, 481, 211),
    'dorm1':(516, 144.5, 718, 211),
    'processing':(887, 144.5, 1022, 211),

    'B201':(9, 212, 144, 278.5),
    'B202':(144, 212, 279, 278.5),
    'B203':(280, 212, 414, 278.5),
    'dorm2':(583, 212, 786, 278.5),
    'office':(887, 212, 1022, 278.5),

    'B301':(77, 279.5, 211, 346),
    'B302':(212, 279.5, 346, 346),
    'B303':(347, 279.5, 481, 346),
    'dorm3':(516, 279.5, 718, 346),
    'training':(887, 279.5, 1022, 346),

    'dorm4':(583, 347, 785, 414)
}

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
        self.register_cli_command('riic', self.cli_riic, self.cli_riic.__doc__)
    
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
            self.tap_quadrilateral(result.context.template_corners, post_delay=3)
        else:
            raise RuntimeError('failed to find riic entry')
        while not self.check_in_riic():
            self.delay(1)
        self.logger.info('已进入基建')
        
    def collect_all(self):
        self.enter_riic()
        count = 0
        while count < 2:
            if roi := (self.match_roi('riic/notification', fixed_position=False, method='template_matching') or
                       self.match_roi('riic/dark_notification', fixed_position=False, method='template_matching')):
                self.logger.info('发现蓝色通知')
                self.tap_rect(roi.bbox)
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
        templ_mask = imgreco.resources.load_image_cached('riic/layout.mask.png', 'L').array
        left_mask = imgreco.imgops.scale_to_height(imgreco.resources.load_image_cached('riic/layout.screen_mask.left.png', 'L'), screenshot.height, Image.NEAREST)
        right_mask = imgreco.imgops.scale_to_height(imgreco.resources.load_image_cached('riic/layout.screen_mask.right.png', 'L'), screenshot.height, Image.NEAREST)
        screen_mask = np.concatenate([left_mask.array, np.full((screenshot.height, screenshot.width - left_mask.width - right_mask.width), 255, dtype=np.uint8), right_mask.array], axis=1)
        match = imgreco.imgops.match_feature_orb(imgreco.resources.load_image_cached('riic/layout.png', 'L'), screenshot.convert('L'), templ_mask=templ_mask, haystack_mask=screen_mask, limited_transform=True)
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
            for name, rect in layout_template.items()
        }
        t1 = time.monotonic()
        print('time elapsed:', t1-t0)
        image = screenshot.convert('native')

        for name, rect in layout.items():
            cv2.rectangle(image.array, Rect.from_ltrb(*rect).xywh, [0, 0, 255], 1)
            cv2.putText(image.array, name, [rect[0]+2, rect[3]-2], cv2.FONT_HERSHEY_PLAIN, 2, [0,0,255], 2)

        image.show()
        print(layout)

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
        else:
            print("unknown command:", cmd)
            return 1
