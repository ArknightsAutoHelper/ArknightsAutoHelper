import asyncio
import base64

from PIL import ImageOps
from winrt.windows.globalization import Language
from winrt.windows.graphics.imaging import SoftwareBitmap, BitmapAlphaMode, BitmapPixelFormat
# pip3 install winrt
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.security.cryptography import CryptographicBuffer

from .common import *


def _dump_rect(rtrect):
    return Rect(rtrect.x, rtrect.y, rtrect.width, rtrect.height)


def _dump_ocrword(word):
    return OcrWord(_dump_rect(word.bounding_rect), word.text)


def _dump_ocrline(line):
    words = list(map(_dump_ocrword, line.words))
    return OcrLine(words)


def _dump_ocrresult(ocrresult):
    lines = list(map(_dump_ocrline, ocrresult.lines))
    result = OcrResult(lines)
    if ocrresult.text_angle:
        result.text_angle = ocrresult.text_angle.value
    return result


def _ibuffer(s):
    """create WinRT IBuffer instance from a bytes-like object"""
    return CryptographicBuffer.decode_from_base64_string(base64.b64encode(s).decode('ascii'))


def _swbmp_from_pil_image(img):
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    pybuf = img.tobytes()
    rtbuf = _ibuffer(pybuf)
    return SoftwareBitmap.create_copy_from_buffer(rtbuf, BitmapPixelFormat.RGBA8, img.width, img.height,
                                                  BitmapAlphaMode.STRAIGHT)


async def _ensure_coroutine(awaitable):
    return await awaitable


def _blocking_wait(awaitable):
    return asyncio.run(_ensure_coroutine(awaitable))


def recognize(img, lang, *, hints=None):
    if hints == None:
        hints = []
    if OcrHint.SINGLE_LINE in hints:
        img = ImageOps.expand(img, 32, fill=img.getpixel((0, 0)))

    lang = Language(lang)
    assert (OcrEngine.is_language_supported(lang))
    eng = OcrEngine.try_create_from_language(lang)
    swbmp = _swbmp_from_pil_image(img)
    return _dump_ocrresult(_blocking_wait(eng.recognize_async(swbmp)))
