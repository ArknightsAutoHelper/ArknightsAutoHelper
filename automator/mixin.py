from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from typing import Annotated, Literal, Optional, Sequence, Union
    from numbers import Real
    import imgreco.common
    TupleRect = tuple[Annotated[Real, 'left'], Annotated[Real, 'top'], Annotated[Real, 'right'], Annotated[Real, 'bottom']]
    RoiDef = Union[str, imgreco.common.RegionOfInterest]
    from .helper import BaseAutomator

class RoiMatchingArgs(TypedDict):
    method: Union[Literal['template_matching'], Literal['compare_mse'], Literal['feature_matching'], None]
    fixed_position: bool

import logging
from random import uniform, randint, gauss
import time

import numpy as np
from util.cvimage import Image, Rect
import imgreco.common
import imgreco.imgops
import imgreco.resources


class AddonMixin(imgreco.common.RoiMatchingMixin):
    if TYPE_CHECKING:
        helper: BaseAutomator
        logger: logging.Logger
        viewport: tuple[int, int]
    
    def _implicit_screenshot(self) -> Image:
        return self.helper.device.screenshot(False)

    def delay(self, n: Real=10,  # 等待时间中值
               MANLIKE_FLAG=True, allow_skip=False):  # 是否在此基础上设偏移量
        if MANLIKE_FLAG:
            m = uniform(0, 0.3)
            n = uniform(n - m * 0.5 * n, n + m * n)
        self.helper.frontend.delay(n, allow_skip)

    def tap_point(self, pos, post_delay=0.5, randomness=(5, 5)):
        x, y = pos
        rx, ry = randomness
        x += randint(-rx, rx)
        y += randint(-ry, ry)
        self.helper.device.touch_tap((x, y))
        self.delay(post_delay)

    def tap_rect(self, rc: Union[TupleRect, Rect], post_delay=1):
        if isinstance(rc, Rect):
            rc = rc.ltrb
        self.logger.debug('tap_rect %r', rc)
        hwidth = (rc[2] - rc[0]) / 2
        hheight = (rc[3] - rc[1]) / 2
        midx = rc[0] + hwidth
        midy = rc[1] + hheight
        xdiff = max(-1.0, min(1.0, gauss(0, 0.2)))
        ydiff = max(-1.0, min(1.0, gauss(0, 0.2)))
        tapx = int(midx + xdiff * hwidth)
        tapy = int(midy + ydiff * hheight)
        self.helper.device.touch_tap((tapx, tapy))
        self.delay(post_delay, MANLIKE_FLAG=True)

    def tap_quadrilateral(self, pts, post_delay=1):
        pts = np.asarray(pts)
        acdiff = max(0.0, min(2.0, gauss(1, 0.2)))
        bddiff = max(0.0, min(2.0, gauss(1, 0.2)))
        halfac = (pts[2] - pts[0]) / 2
        m = pts[0] + halfac * acdiff
        pt2 = pts[1] if bddiff > 1 else pts[3]
        halfvec = (pt2 - m) / 2
        finalpt = m + halfvec * bddiff
        self.helper.device.touch_tap(tuple(int(x) for x in finalpt))
        self.delay(post_delay, MANLIKE_FLAG=True)

    def wait_for_still_image(self, threshold=16, crop=None, timeout=60, raise_for_timeout=True, check_delay=1):
        if crop is None:
            shooter = lambda: self.helper.device.screenshot(False)
        else:
            shooter = lambda: self.helper.device.screenshot(False).crop(crop)
        screenshot = shooter()
        t0 = time.monotonic()
        ts = t0 + timeout
        n = 0
        minerr = 65025
        message_shown = False
        while (t1 := time.monotonic()) < ts:
            if check_delay > 0:
                self.delay(check_delay, False, True)
            screenshot2 = shooter()
            mse = imgreco.imgops.compare_mse(screenshot, screenshot2)
            if mse <= threshold:
                return screenshot2
            screenshot = screenshot2
            if mse < minerr:
                minerr = mse
            if not message_shown and t1-t0 > 10:
                self.logger.info("等待画面静止")
        if raise_for_timeout:
            raise RuntimeError("%d 秒内画面未静止，最小误差=%d，阈值=%d" % (timeout, minerr, threshold))
        return None

    def swipe_screen(self, move, rand=100, origin_x=None, origin_y=None):
        origin_x = (origin_x or self.viewport[0] // 2) + randint(-rand, rand)
        origin_y = (origin_y or self.viewport[1] // 2) + randint(-rand, rand)
        self.helper.device.touch_swipe2((origin_x, origin_y), (move, max(250, move // 2)), randint(600, 900))

    def wait_for_roi(self, roi: RoiDef, timeout: Real = 10, threshold=None, **roi_matching_args: RoiMatchingArgs) -> imgreco.common.RoiMatchingResult:
        t0 = time.monotonic()
        result = imgreco.common.RoiMatchingResult.NoMatch
        while time.monotonic() < t0 + timeout:
            result = self.match_roi(roi, **roi_matching_args)
            if threshold is not None:
                result = result.with_threshold(threshold)
            if result:
                break
            self.delay(0.5, False, False)
        return result
    
    def wait_and_tap_roi(self, roi: RoiDef, timeout: Real = 10, threshold=None, **roi_matching_args: RoiMatchingArgs) -> imgreco.common.RoiMatchingResult:
        result = self.wait_for_roi(roi, timeout, threshold, **roi_matching_args)
        if result:
            self.tap_rect(roi.bbox.ltrb)
        return result
    
    def wait_for_any_roi(self, rois: Sequence[RoiDef], timeout: Real = 10, threshold=None, **roi_matching_args: RoiMatchingArgs) -> tuple[bool, list[imgreco.common.RoiMatchingResult]]:
        rois = [self._ensure_roi(roi) for roi in rois]
        t0 = time.monotonic()
        results = [imgreco.common.RoiMatchingResult.NoMatch] * len(rois)
        while time.monotonic() < t0 + timeout:
            results = [self.match_roi(roi, **roi_matching_args) for roi in rois]
            if threshold is not None:
                results = [result.with_threshold(threshold) for result in results]
            if any(results):
                return True, results
            self.delay(0.5, False, False)
        return False, results
    
    def wait_for_all_roi(self, rois: Sequence[RoiDef], timeout: Real = 10, threshold=None, **roi_matching_args: RoiMatchingArgs) -> tuple[bool, list[imgreco.common.RoiMatchingResult]]:
        rois = [self._ensure_roi(roi) for roi in rois]
        t0 = time.monotonic()
        results = [imgreco.common.RoiMatchingResult.NoMatch] * len(rois)
        while time.monotonic() < t0 + timeout:
            results = [self.match_roi(roi, **roi_matching_args) for roi in rois]
            if threshold is not None:
                results = [result.with_threshold(threshold) for result in results]
            if all(results):
                return True, results
            self.delay(0.5, False, False)
        return False, results
