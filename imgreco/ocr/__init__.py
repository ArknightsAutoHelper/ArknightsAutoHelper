import importlib
from functools import lru_cache

from . import dummy
from .common import OcrEngine, OcrHint, OcrLine, OcrResult, OcrWord
import atexit

available_engines = ['tesseract', 'windows_media_ocr', 'baidu']
"""
适配的 engine 列表
一个 engine 需要实现以下接口：
engine.info
engine.is_online
engine.check_supported()
engine.recognize(image, lang, *, hints=None)

理论上 engine 可以是任何实现以上接口的 object，此处使用 importlib.import_module 产生的模块。
更为详细的说明请参阅 dummy.py
"""


def get_impl(name):
    return importlib.import_module("." + name, __name__)


def _auto_impl():
    """返回一个运行时可用的 engine，没有可用 engine 则为 dummy engine"""
    for name in available_engines:
        try:
            eng = get_impl(name)
            if eng.check_supported():
                return eng
        except Exception:
            pass
    return dummy


@lru_cache()
def get_config_impl():
    import app
    if app.config.ocr.backend == 'auto':
        engine = _auto_impl()
    else:
        engine = get_impl(app.config.ocr.backend)
    return engine


@lru_cache()
def acquire_engine_global_cached(lang, **kwargs) -> OcrEngine:
    impl = get_config_impl()
    return impl.Engine(lang, **kwargs)

atexit.register(acquire_engine_global_cached.cache_clear)


def match_distance(text, collection):
    import textdistance
    comparisions = []
    for index, item in enumerate(collection):
        if text == item:
            return index, 0
        comparisions.append((index, textdistance.levenshtein(text, item)))
    return min(comparisions, key=lambda x: x[1])
