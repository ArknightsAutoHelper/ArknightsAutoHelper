from . import tesseract, windows_media_ocr, dummy, baidu
from .common import OcrHint, OcrLine, OcrResult, OcrWord
import config

available_engines = []
"""
运行时可用 engine 的列表
一个 engine 需要实现以下接口：
engine.info
engine.is_online
engine.check_supported()
engine.recognize(image, lang, *, hints=None)

理论上 engine 可以是任何实现以上接口的 object，此处使用 import 产生的模块。
更为详细的说明请参阅 dummy.py
"""

if tesseract.check_supported():
    available_engines.append(tesseract)
if windows_media_ocr.check_supported():
    available_engines.append(windows_media_ocr)
if baidu.check_supported():
    available_engines.append(baidu)

if config.engine != 'auto':
    engine = globals()[config.engine]
else:
    engine = available_engines[0] if len(available_engines) != 0 else dummy
# 一个运行时可用的 engine，没有可用 engine 则为 dummy engine

