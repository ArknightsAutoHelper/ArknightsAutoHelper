from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, ClassVar, Optional, Union, Literal

from dataclasses import dataclass, field
from numbers import Real
import cv2
import numpy as np
import logging
from util import cvimage as Image

from util.richlog import get_logger
from . import imgops
from . import resources

richlogger = get_logger(__name__)
logger = logging.getLogger(__name__)

def check_get_item_popup(img):
    vw, vh = get_vwvh(img.size)
    icon1 = img.crop((50 * vw - 6.389 * vh, 5.556 * vh, 50 * vw + 8.426 * vh, 18.981 * vh)).convert('RGB')
    icon2 = resources.load_image_cached('common/getitem.png', 'RGB')

    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    mse = imgops.compare_mse(np.asarray(icon1), np.asarray(icon2))
    # print(mse, icon1.size)
    richlogger.logimage(icon1)
    richlogger.logtext('check_get_item_popup mse=%f' % mse)
    return mse < 2000


def get_reward_popup_dismiss_rect(viewport):
    vw, vh = get_vwvh(viewport)
    return (100 * vw - 61.944 * vh, 18.519 * vh, 100 * vw - 5.833 * vh, 87.222 * vh)


def check_nav_button(img):
    vw, vh = get_vwvh(img.size)
    icon1 = img.crop((3.194 * vh, 2.222 * vh, 49.722 * vh, 7.917 * vh)).convert('RGB')
    icon2 = resources.load_image_cached('common/navbutton.png', 'RGB')
    threshold = 200
    icon1 = icon1.convert("L").point(lambda p: p > threshold and 255)
    icon2 = icon2.convert("L").point(lambda p: p > threshold and 255)
    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    ccoeff = imgops.compare_ccoeff(np.asarray(icon1), np.asarray(icon2))
    richlogger.logimage(icon1)
    richlogger.logtext('check_nav_button ccoeff=%f' % ccoeff)
    return ccoeff > 0.8


def get_nav_button_back_rect(viewport):
    vw, vh = get_vwvh(viewport)
    return (3.194 * vh, 2.222 * vh, 20.972 * vh, 7.917 * vh)


def check_setting_scene(img):
    vw, vh = get_vwvh(img.size)
    icon1 = img.crop((4.722 * vh, 3.750 * vh, 19.444 * vh, 8.333 * vh)).convert('RGB')
    icon2 = resources.load_image_cached('common/settingback.png', 'RGB')

    icon1, icon2 = imgops.uniform_size(icon1, icon2)
    mse = imgops.compare_mse(np.asarray(icon1), np.asarray(icon2))
    richlogger.logimage(icon1)
    richlogger.logtext('check_setting_scene mse=%f' % mse)
    return mse < 200

def get_setting_back_rect(viewport):
    vw, vh = get_vwvh(viewport)
    return (4.722 * vh, 3.750 * vh, 19.444 * vh, 8.333 * vh)


def find_close_button(img):
    # raise NotImplementedError
    scale = 1
    if img.height != 720:
        scale = img.height / 720
        img = imgops.scale_to_height(img, 720)
    righttopimg = img.crop((img.width // 2, 0, img.width, img.height // 2)).convert('L')
    template = resources.load_image_cached('common/closebutton.png', 'L')
    mtresult = cv2.matchTemplate(np.asarray(righttopimg), np.asarray(template), cv2.TM_CCOEFF_NORMED)
    maxidx = np.unravel_index(np.argmax(mtresult), mtresult.shape)
    y, x = maxidx
    x += img.width // 2
    rect = np.array((x, y, x + template.width, y + template.height)) * scale
    return tuple(rect.astype(np.int32)), mtresult[maxidx]

def check_dialog(img):
    # vw, vh = get_vwvh(img.size)
    # buttons = img.crop((0, 64.861*vh, 100.000*vw, 75.417*vh)).convert('RGB')
    oldheight = img.height
    img = img.resize((1280, 720), Image.BILINEAR).convert('RGB').crop((0, 360, 1280, 640))
    yesno = resources.load_image_cached('common/dialog_2btn.png', 'RGB')
    ok = resources.load_image_cached('common/dialog_1btn.png', 'RGB')
    pt1, coef1 = imgops.match_template(img, yesno)
    pt2, coef2 = imgops.match_template(img, ok)
    # print(pt1, coef1, pt2, coef2)
    if max(coef1, coef2) > 0.5:
        return ('yesno', (pt1[1] + 360)/720 * oldheight) if coef1 > coef2 else ('ok', (pt2[1] + 360)/720 * oldheight)
    return None, None

def recognize_dialog(img):
    dlgtype, _ = check_dialog(img)
    if dlgtype is None:
        return None, None
    from . import ocr
    vw, vh = get_vwvh(img.size)
    content = img.crop((0, 22.222*vh, 100.000*vw, 64.167*vh)).convert('L')
    return dlgtype, ocr.acquire_engine_global_cached('zh-cn').recognize(content, int(vh * 20), tessedit_pageseg_mode=11)

def get_dialog_left_button_rect(img):
    vw, vh = get_vwvh(img)
    dlgtype, y = check_dialog(img)
    assert dlgtype == 'yesno'
    return (0, y-4*vh, 50*vw, y+4*vh)

def get_dialog_right_button_rect(img):
    vw, vh = get_vwvh(img)
    dlgtype, y = check_dialog(img)
    assert dlgtype == 'yesno'
    return (50*vw, y-4*vh, 100*vw, y+4*vh)

def get_dialog_ok_button_rect(img):
    vw, vh = get_vwvh(img)
    dlgtype, y = check_dialog(img)
    assert dlgtype == 'ok'
    return (25*vw, y-4*vh, 75*vw, y+4*vh)


def convert_to_pil(cv_img, color_code=cv2.COLOR_BGR2RGB):
    return Image.fromarray(cv2.cvtColor(cv_img, color_code))


def convert_to_cv(pil_img, color_code=cv2.COLOR_BGR2RGB):
    return cv2.cvtColor(np.asarray(pil_img), color_code)


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)

def get_vwvh(size):
    if isinstance(size, tuple):
        return (size[0] / 100, size[1] / 100)
    return (size.width / 100, size.height / 100)

@dataclass
class RegionOfInterest:
    name: str
    template: Optional[Image.Image] = None
    mask: Optional[Image.Image] = None
    bbox_matrix: Optional[np.matrix] = None
    native_resolution: Optional[tuple[int, int]] = None
    bbox: Optional[Image.Rect] = None
    matching_preference: dict = field(default_factory=dict)

    def with_target_viewport(self, width, height):
        if self.bbox_matrix is None:
            return self
        vw = width / 100
        vh = height / 100
        left, top, right, bottom = np.asarray(self.bbox_matrix * np.matrix(np.matrix([[vw], [vh], [1]]))).reshape(4)
        bbox = Image.Rect.from_ltrb(left, top, right, bottom)
        return RegionOfInterest(self.name, self.template, self.mask, self.bbox_matrix, self.native_resolution, bbox)

@dataclass
class RoiMatchingResult:
    roi_name: str
    score: Real = None
    threshold: Real = None
    optimal_score: Real = None
    bbox: Optional[Image.Rect] = None
    context: Any = None
    if TYPE_CHECKING:
        NoMatch: ClassVar[RoiMatchingResult]

    def __bool__(self):
        if self.threshold > self.optimal_score:
            return bool(self.score < self.threshold)
        elif self.threshold <= self.optimal_score:
            return bool(self.score > self.threshold)

RoiMatchingResult.NoMatch = RoiMatchingResult(None, 65025, 1, 0)

class RoiMatchingMixin:
    viewport: tuple[int, int]

    def _implicit_screenshot(self) -> Image.Image:
        raise NotImplementedError()

    def load_roi(self, name: str, mode: str = 'RGB') -> RegionOfInterest:
        roi = resources.load_roi(name, mode)
        return self._localize_roi(roi)
    
    def _localize_roi(self, roi: RegionOfInterest):
        return roi.with_target_viewport(*self.viewport)

    def _ensure_roi(self, roidef: Union[str, RegionOfInterest], mode) -> RegionOfInterest:
        if isinstance(roidef, str):
            return self.load_roi(roidef, mode)
        else:
            return self._localize_roi(roidef)

    def match_roi(self, roi: Union[str, RegionOfInterest], fixed_position: Optional[bool] = None, method: Literal["template_matching", "mse", "sift", None] = None, threshold=None, mode='RGB', screenshot=None, matching_mask=None) -> RoiMatchingResult:
        roi = self._ensure_roi(roi, mode)
        if screenshot is None:
            screenshot = self._implicit_screenshot()
        if screenshot.mode != mode:
            screenshot = screenshot.convert(mode)
        result = RoiMatchingResult(roi.name)
        if fixed_position is None:
            fixed_position = roi.matching_preference.get('fixed_position', True)
        if method is None:
            method = roi.matching_preference.get('method', None)
        if threshold is None:
            threshold = roi.matching_preference.get('threshold', None)
        if fixed_position:
            result.bbox = roi.bbox
            compare = screenshot.crop(roi.bbox)
            template, compare = imgops.uniform_size(roi.template, compare)
            mask = roi.mask.resize(template.size) if roi.mask is not None else None
            if method is None:
                method = 'mse'
            if method == 'mse':
                result.score = imgops.compare_mse(template, compare, mask)
                result.optimal_score = 0
                result.threshold = threshold if threshold is not None else 650
            elif method == 'template_matching' or method == 'ccoeff':
                result.score = imgops.compare_ccoeff(template, compare, mask)
                result.optimal_score = 1
                result.threshold = threshold if threshold is not None else 0.8
            elif method == 'sift':
                feature_result = imgops.match_feature(template, compare, templ_mask=mask.array)
                result.score = feature_result.matched_keypoint_count
                result.optimal_score = feature_result.template_keypooint_count
                result.threshold = min(feature_result.template_keypooint_count, 10)
                result.context = feature_result
            else:
                raise RuntimeError("unsupported matching method %s for fixed-position ROI" % method)

        else:
            if method is None:
                method = 'ccoeff'
            if method == 'template_matching' or method == 'ccoeff' or method == 'mse':
                if method == 'mse':
                    cv_method = cv2.TM_SQDIFF_NORMED
                    result.optimal_score = 0
                    result.threshold = threshold if threshold is not None else 0.06
                else:
                    cv_method = cv2.TM_CCOEFF_NORMED
                    result.optimal_score = 1
                    result.threshold = threshold if threshold is not None else 0.8
                scaled_template = roi.template.resize((roi.bbox.width, roi.bbox.height))
                mask = roi.mask.resize(scaled_template.size) if roi.mask is not None else None
                center, score = imgops.match_template(screenshot, scaled_template, method=cv_method, template_mask=mask.array)
                point = (center[0] - scaled_template.width / 2, center[1] - scaled_template.height / 2)
                result.score = score
                result.bbox = Image.Rect.from_xywh(point[0], point[1], scaled_template.width, scaled_template.height)
            elif method == 'sift':
                feature_result = imgops.match_feature(roi.template, screenshot, templ_mask=roi.mask.array, haystack_mask=matching_mask)
                result.score = feature_result.matched_keypoint_count
                result.optimal_score = feature_result.template_keypooint_count
                result.threshold = min(feature_result.template_keypooint_count, 10)
                result.context = feature_result
                x, y, w, h = cv2.boundingRect(feature_result.template_corners)
                result.bbox = Image.Rect.from_xywh(x, y, w, h)
            else:
                raise RuntimeError("unsupported matching method %s for non-fixed-position ROI" % method)
        uselogger = getattr(self, 'logger', logger)
        uselogger.debug('%r', result)
        return result
class ImageRoiMatchingContext(RoiMatchingMixin):
    def __init__(self, img: Image.Image):
        self.image = img
        self.viewport = img.size

    def _implicit_screenshot(self) -> Image.Image:
        return self.image

if __name__ == "__main__":
    import sys

    print(globals()[sys.argv[-2]](Image.open(sys.argv[-1])))
