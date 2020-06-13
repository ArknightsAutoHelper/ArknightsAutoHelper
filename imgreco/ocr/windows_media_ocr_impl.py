from PIL import ImageOps

from rotypes import HSTRING
from rotypes.Windows.Globalization import Language
from rotypes.Windows.Graphics.Imaging import SoftwareBitmap, BitmapAlphaMode, BitmapPixelFormat
from rotypes.Windows.Media.Ocr import OcrEngine as WinRTOcrEngine
from rotypes.Windows.Security.Cryptography import CryptographicBuffer

from .common import *


def _dump_rect(rtrect):
    return Rect(rtrect.x, rtrect.y, rtrect.width, rtrect.height)


def _dump_ocrword(word):
    return OcrWord(_dump_rect(word.BoundingRect), str(word.Text))


def _dump_ocrline(line):
    words = list(map(_dump_ocrword, line.Words))
    return OcrLine(words)


def _dump_ocrresult(ocrresult):
    lines = list(map(_dump_ocrline, ocrresult.Lines))
    result = OcrResult(lines)
    if ocrresult.TextAngle:
        result.text_angle = ocrresult.TextAngle.Value
    return result


def _swbmp_from_pil_image(img):
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    pybuf = img.tobytes()
    rtbuf = CryptographicBuffer.CreateFromByteArray(len(pybuf), pybuf)
    return SoftwareBitmap.CreateCopyWithAlphaFromBuffer(rtbuf, BitmapPixelFormat.Rgba8, img.width, img.height, BitmapAlphaMode.Straight)


def check_supported():
    try:
        return WinRTOcrEngine.IsLanguageSupported(Language.CreateLanguage(HSTRING('zh-cn')))
    except Exception:
        return False

class WindowsOcrEngine(OcrEngine):
    def __init__(self, lang, **kwargs):
        super().__init__(lang, **kwargs)
        lang = Language.CreateLanguage(HSTRING(lang))
        if not WinRTOcrEngine.IsLanguageSupported(lang):
            raise ValueError('unsupported language')
        self.winengine = WinRTOcrEngine.TryCreateFromLanguage(lang)

    def recognize(self, img, ppi=70, *, hints=None):
        if hints == None:
            hints = []
        if OcrHint.SINGLE_LINE in hints:
            img = ImageOps.expand(img, 32, fill=img.getpixel((0, 0)))

        swbmp = _swbmp_from_pil_image(img)
        return _dump_ocrresult(self.winengine.RecognizeAsync(swbmp).wait())

Engine = WindowsOcrEngine
