from . import tesseract, windows_media_ocr, baidu
from .common import OcrHint, OcrLine, OcrResult, OcrWord

available_engines = []

if tesseract.check_supported():
    available_engines.append(tesseract)
if windows_media_ocr.check_supported():
    available_engines.append(windows_media_ocr)
available_engines.append(baidu)

engine = available_engines[0] if len(available_engines) != 0 else None
