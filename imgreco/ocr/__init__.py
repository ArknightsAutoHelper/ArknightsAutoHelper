import importlib
from functools import lru_cache

from . import dummy
from .common import OcrHint, OcrLine, OcrResult, OcrWord

available_engines = ['windows_media_ocr', 'tesseract', 'baidu']
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


def get_engine(name):
    return importlib.import_module("." + name, __name__)


def _auto_engine():
    """返回一个运行时可用的 engine，没有可用 engine 则为 dummy engine"""
    for name in available_engines:
        try:
            eng = get_engine(name)
            if eng.check_supported():
                return eng
        except Exception:
            pass
    return dummy


@lru_cache()
def get_config_engine():
    import config
    if config.engine == 'auto':
        engine = _auto_engine()
    else:
        engine = get_engine(config.engine)
    return engine
