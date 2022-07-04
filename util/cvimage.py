from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, overload
from numbers import Real

import builtins
import sys
import os
import io
import math
import warnings
import contextlib
from pathlib import Path

import cv2
import numpy as np

from PIL import Image as PILImage


def isPath(f):
    return isinstance(f, (bytes, str, Path))

NEAREST = NONE = cv2.INTER_NEAREST_EXACT
BILINEAR = LINEAR = cv2.INTER_LINEAR
BICUBIC = CUBIC = cv2.INTER_CUBIC
LANCZOS = ANTIALIAS = cv2.INTER_LANCZOS4
BOX = HAMMING = cv2.INTER_AREA

def _channels(shape):
    if len(shape) == 2:
        return 1
    return shape[-1]

def _get_valid_modes(shape, dtype):
    if len(shape) == 2:
        # single channel
        if dtype == np.uint8:
            return ['L']
        elif dtype == bool:
            return ['1']
        elif dtype == np.int32:
            return ['I']
        elif dtype == np.float32:
            return ['F']
        else:
            raise TypeError('unsupported data format: single channel %r' % dtype)
    elif len(shape) == 3:
        # multi channel
        if dtype not in (np.uint8, np.uint16, np.uint32, np.uint64, np.float32, np.float64):
            raise TypeError('unsupported data format: multi-channel %r' % dtype)
        channels = shape[-1]
        if channels == 3:
            return ['BGR', 'RGB']
        elif channels== 4:
            return ['BGRA', 'RGBA', 'RGBX', 'BGRX', 'RGBa', 'BGRa']
        else:
            raise ValueError(f'unsupported channel count {channels}')
    raise ValueError(f"cannot infer image mode from array shape {shape!r} and dtype {dtype!r}")

pil_mode_mapping = {
    # 'Pillow mode': 'OpenCV mode',
    'RGB':  'RGB',
    'RGBA': 'RGBA',
    'RGBX': 'RGBA',
    'RGBa': 'mRGBA',
    'L':    'GRAY',
    'I':    'GRAY',
    'F':    'GRAY',
    # extra modes for convenience
    'BGR':  'BGR',
    'BGRA': 'BGRA',
    'BGRa': 'mBGRA',
}

def imread(fp, flags=cv2.IMREAD_UNCHANGED):
    exclusive_fp = False
    filename = ""
    if isinstance(fp, Path):
        filename = str(fp.resolve())
    elif isPath(fp):
        filename = fp

    if filename:
        fp = builtins.open(filename, "rb")
        exclusive_fp = True

    try:
        fp.seek(0)
    except (AttributeError, io.UnsupportedOperation):
        fp = io.BytesIO(fp.read())
        exclusive_fp = True
    
    data = fp.read()
    if exclusive_fp:
        fp.close()
    mat = cv2.imdecode(np.asarray(memoryview(data)), flags)
    if mat is None:
        raise cv2.error('imdecode failed')
    ch = _channels(mat.shape)
    target_mode = None
    if ch == 3:
        target_mode = 'BGR'
    elif ch == 4:
        target_mode = 'BGRA'
    if target_mode is not None and mat.dtype != np.uint8:
        if mat.dtype in (np.float32, np.float64):
            maxval = 1.0
        else:
            maxval = np.float32(np.iinfo(mat.dtype).max)
        mat = (mat / maxval * 255).astype(np.uint8)
    return Image(mat, target_mode) 

open = imread

def fromarray(array, mode=None):
    if mode is None:
        ch = _channels(array.shape)
        if ch == 3:
            # use RGB order for compatibility with PIL
            mode = 'RGB'
        elif ch == 4:
            mode = 'RGBA'
    return Image(array, mode)

def from_pil(pil_im: PILImage.Image):
    from util import pil_zerocopy
    array = pil_zerocopy.asarray(pil_im)
    array = np.ascontiguousarray(array)
    return fromarray(array, pil_im.mode)

@dataclass
class Rect:
    x: Real
    y: Real
    width: Real = 0
    height: Real = 0

    def __init__(self, x, y, w=0, h=0, *, right=None, bottom=None):
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        if right is not None:
            self.right = right
        if bottom is not None:
            self.bottom = bottom

    @classmethod
    def from_xywh(cls, x, y, w, h):
        return cls(x, y, w, h)

    @classmethod
    def from_ltrb(cls, left, top, right, bottom):
        return cls(left, top, right=right, bottom=bottom)

    @property
    def right(self):
        return self.x + self.width

    @right.setter
    def right(self, value):
        self.width = value - self.x

    @property
    def bottom(self):
        return self.y + self.height

    @bottom.setter
    def bottom(self, value):
        self.height = value - self.y

    @property
    def xywh(self):
        """describe this Rect in tuple of (x, y, width, height)"""
        return self.x, self.y, self.width, self.height

    @property
    def ltrb(self):
        """describe this Rect in tuple of (left, top, right, bottom)"""
        return self.x, self.y, self.right, self.bottom

    def round(self):
        """return a Rect that rounded to nearest integer"""
        return Rect.from_ltrb(*(round(x) for x in self.ltrb))

    def scale(self, scale):
        """return a Rect that scaled by given factor"""
        return Rect(*(x*scale for x in self.xywh))

    def iscale(self, scale):
        """return a Rect that scaled by given factor and rounded to nearest integer"""
        return self.scale(scale).round()

    def __iter__(self):
        return iter((self.x, self.y, self.right(), self.bottom()))

class Image:
    timestamp: Optional[float] = None
    def __init__(self, mat: np.ndarray, mode=None):
        self._mat = mat
        valid_modes = _get_valid_modes(mat.shape, mat.dtype)
        if mode is not None and mode not in valid_modes:
            raise ValueError("Invalid mode")
        if mode is None and len(valid_modes) > 1:
            warnings.warn(f"multiple mode inferred from array shape {mat.shape!r} and dtype {mat.dtype!r}: {' '.join(valid_modes)}, you might want to explicitly specify a mode")
        self._mode = mode or valid_modes[0]

    # for use with numpy.asarray
    def __array__(self, dtype=None):
        return np.asarray(self._mat, dtype=dtype)
    
    # for use with functools.lrucache
    def __hash__(self):
        keys = ['shape', 'typestr', 'descr', 'data', 'strides', 'mask', 'offset', 'version']
        array_intf = self._mat.__array_interface__
        array_intf_tup = tuple(array_intf.get(i, None) for i in keys)
        return builtins.hash((repr(array_intf_tup), self._mode))

    def __repr__(self):
        return f'<{self.__class__.__qualname__} size={self.width}x{self.height} mode={self.mode} dtype={self.dtype} timestamp={self.timestamp}>'

    @property
    def array(self):
        return self._mat

    @property
    def dtype(self):
        return self._mat.dtype

    @property
    def mode(self):
        return self._mode
    
    @property
    def width(self):
        return self._mat.shape[1]
    
    @property
    def height(self):
        return self._mat.shape[0]
    
    @property
    def size(self) -> tuple[int, int]:
        return tuple(self._mat.shape[1::-1])

    @overload
    def subview(self, rect: Rect) -> Image:
        """crop with Rect"""
        ...

    @overload
    def subview(self, rect: tuple[Real, Real, Real, Real]) -> Image:
        """crop with (left, top, right, bottom) tuple"""
        ...
    
    @overload
    def crop(self, rect: Rect) -> Image:
        """crop with Rect"""
        ...

    @overload
    def crop(self, rect: tuple[Real, Real, Real, Real]) -> Image:
        """crop with (left, top, right, bottom) tuple"""
        ...

    def subview(self, rect) -> Image:
        if rect is None:
            return self
        if isinstance(rect, Rect):
            left, top, right, bottom = (int(round(x)) for x in rect.ltrb)
        else:
            left, top, right, bottom = (int(round(x)) for x in rect)
        newmat = self._mat[top:bottom, left:right]
        return Image(newmat, self.mode)

    def crop(self, rect):
        return self.subview(rect).copy()
    
    def convert(self, mode=None, matrix=NotImplemented, dither=NotImplemented, palette=NotImplemented, colors=NotImplemented) -> Image:
        if matrix is not NotImplemented or dither is not NotImplemented or palette is not NotImplemented or colors is not NotImplemented:
            raise NotImplementedError()
        from_cv_mode = pil_mode_mapping[self.mode]
        target_cv_mode = None
        if mode == 'native':
            if self.mode in ('RGBA', 'RGBa', 'BGRA', 'BGRa'):
                target_cv_mode = 'BGRA'
                target_pil_mode = 'BGRA'
            elif self.mode in ('RGB', 'BGR', 'RGBX', 'BGRX'):
                target_cv_mode = 'BGR'
                target_pil_mode = 'BGR'
            elif self.mode in ('L', 'I', 'F'):
                target_cv_mode = 'GRAY'
                target_pil_mode = self.mode
        elif mode == '1':
            limg = self.convert('L') if self.mode != 'L' else self
            _, newmat = cv2.threshold(limg.array, 127, 1, cv2.THRESH_BINARY)
            return Image(newmat.astype(bool), '1')
        else:
            target_cv_mode = pil_mode_mapping[mode]
            target_pil_mode = mode

        if target_pil_mode == self.mode:
            return self if mode == 'native' else self.copy()
        else:
            if target_cv_mode is None:
                if mode in pil_mode_mapping:
                    target_cv_mode = pil_mode_mapping[mode]
                else:
                    raise NotImplementedError(f'conversion from {self.mode} to {mode} not implemented yet')
            conv = getattr(cv2, f'COLOR_{from_cv_mode}2{target_cv_mode}', None)
            if conv is None:
                raise NotImplementedError(f'conversion from {self.mode} to {mode} not implemented yet')
            newmat = cv2.cvtColor(self._mat, conv)
            return Image(newmat, target_pil_mode)
    
    def getbbox(self):
        mat = self._mat
        if mat.dtype == bool:
            mat = mat.astype(np.uint8)
        _, thim = cv2.threshold(mat, 0, 255, cv2.THRESH_BINARY)
        ch = _channels(thim.shape)
        if ch > 1:
            thim = cv2.transform(thim, np.ones(ch, dtype=np.float32).reshape(1, ch))
        x, y, w, h = cv2.boundingRect(thim)
        if w == 0 and h == 0:
            return None
        rect = (x, y, x+w, y+h)
        return rect
    
    def copy(self):
        return Image(self._mat.copy(), self.mode)

    def tobytes(self):
        return self._mat.tobytes()

    def rotate(self, angle, resample=NEAREST, expand=False, center=None, translate=None, fillcolor=None):
        # use original PIL code to generate affine matrix
        angle = angle % 360.0
        if not (center or translate):
            if angle == 0:
                return self.copy()
            if angle == 180:
                return Image(cv2.rotate(self._mat, cv2.ROTATE_180), self.mode)
            if angle == 90 and expand:
                return Image(cv2.rotate(self._mat, cv2.ROTATE_90_COUNTERCLOCKWISE), self.mode)
            if angle == 270 and expand:
                return Image(cv2.rotate(self._mat, cv2.ROTATE_90_CLOCKWISE), self.mode)
        w, h = self.size

        if translate is None:
            post_trans = (0, 0)
        else:
            post_trans = translate
        if center is None:
            # FIXME These should be rounded to ints?
            rotn_center = (w / 2.0, h / 2.0)
        else:
            rotn_center = center

        angle = -math.radians(angle)
        matrix = [
            round(math.cos(angle), 15),
            round(math.sin(angle), 15),
            0.0,
            round(-math.sin(angle), 15),
            round(math.cos(angle), 15),
            0.0,
        ]

        def transform(x, y, matrix):
            (a, b, c, d, e, f) = matrix
            return a * x + b * y + c, d * x + e * y + f

        matrix[2], matrix[5] = transform(
            -rotn_center[0] - post_trans[0], -rotn_center[1] - post_trans[1], matrix
        )
        matrix[2] += rotn_center[0]
        matrix[5] += rotn_center[1]

        if expand:
            # calculate output size
            xx = []
            yy = []
            for x, y in ((0, 0), (w, 0), (w, h), (0, h)):
                x, y = transform(x, y, matrix)
                xx.append(x)
                yy.append(y)
            nw = math.ceil(max(xx)) - math.floor(min(xx))
            nh = math.ceil(max(yy)) - math.floor(min(yy))

            # We multiply a translation matrix from the right.  Because of its
            # special form, this is the same as taking the image of the
            # translation vector as new translation vector.
            matrix[2], matrix[5] = transform(-(nw - w) / 2.0, -(nh - h) / 2.0, matrix)
            w, h = nw, nh

        newmat = cv2.warpAffine(self._mat, np.array(matrix).reshape(2, 3), (w,h), flags=resample, borderMode=cv2.BORDER_CONSTANT, borderValue=fillcolor)
        return Image(newmat, self.mode)

    def resize(self, size, resample=None, box=NotImplemented, reducing_gap=NotImplemented):
        if resample is None:
            if self.mode == '1':
                resample = NEAREST
            else:
                resample = BICUBIC
        newmat = cv2.resize(self._mat, (int(round(size[0])), int(round(size[1]))), interpolation=resample)
        return Image(newmat, self.mode)

    def save(self, fp, format=None, imwrite_params=None, **params):
        filename = ""
        open_fp = False
        if isPath(fp):
            filename = fp
            open_fp = True
        elif isinstance(fp, Path):
            filename = str(fp)
            open_fp = True
        elif fp == sys.stdout:
            try:
                fp = sys.stdout.buffer
            except AttributeError:
                pass
        if not filename and hasattr(fp, "name") and isPath(fp.name):
            # only set the name for metadata purposes
            filename = fp.name
        if open_fp:
            fp = builtins.open(filename, "w+b")
            context = fp
        else:
            context = contextlib.nullcontext()
        with context:
            if format is None:
                format = os.path.splitext(filename)[1].lower()
            if not format:
                format = 'png'
            buf = self.imencode(format, imwrite_params)
            fp.write(buf)

    def imencode(self, format='png', params=None):
        image = self.convert('native')
        if not format.startswith('.'):
            format = '.' + format
        result, buf = cv2.imencode(format, image.array, params)
        if result:
            return buf
        else:
            raise cv2.error('imencode failed')

    def show(self):
        native = self.convert('native')
        import multiprocessing
        from . import _cvimage_imshow_helper
        title = f'Image: {self.width}x{self.height} {self.mode} {self.dtype}'
        multiprocessing.Process(target=_cvimage_imshow_helper.imshow, args=(title, native.array)).start()

    def to_pil(self, always_copy):
        result, copied = self.to_pil2(always_copy)
        return result

    def to_pil2(self, always_copy=False) -> tuple[PILImage.Image, bool]:
        """returns a PIL image and a flag indicating whether the image was copied or not"""
        oldmat = self.array
        need_convert = None
        real_pil_mode = self.mode
        pil_internal_mode = None
        w, h = self.size
        if self.mode == 'RGB' or self.mode == 'BGR':
            need_convert = 'RGBA'
            real_pil_mode = 'RGB'
            pil_internal_mode = 'RGBA'
        elif self.mode[0:3] == 'BGR':
            need_convert = 'RGB' + self.mode[3:]
            real_pil_mode = need_convert
        if pil_internal_mode is None:
            pil_internal_mode = real_pil_mode
        if need_convert is not None:
            img = self.convert(need_convert)
        else:
            img = self
        if always_copy and img is self:
            img = img.copy()
        mat = img.array
        assert mat.dtype == np.uint8
        if not mat[0].data.c_contiguous:
            mat = np.ascontiguousarray(mat)
        ystride = mat.strides[0]
        ystep = 1
        if ystride < 0:
            ystride = -ystride
            ystep = -1
        fulllen = ystride * h
        contmat = np.lib.stride_tricks.as_strided(mat[::ystep, ...], shape=(fulllen,), strides=(1,))
        return PILImage.frombuffer(real_pil_mode, (w, h), contmat, 'raw', pil_internal_mode, ystride, ystep), mat is not oldmat

def _test():
    im = open(r"D:\dant\Pictures\items\100px-道具_带框_量子二踢脚.png", cv2.IMREAD_COLOR)
    im = im.subview((20, 20, 70, 70))
    im.show()
    bio = io.BytesIO()
    pil_im = im.to_pil()
    pil_im.show()
    pil_im.save(bio, 'png')
    bio.seek(0)
    im2 = open(bio)
    im2.show()


if __name__ == '__main__':
    _test()
