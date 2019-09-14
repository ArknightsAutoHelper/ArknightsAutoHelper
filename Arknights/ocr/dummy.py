is_online = True
# OCR 过程是否需要网络


info = "Dummy OCR Engine"
# 模块说明，用于在 log 中显示

def check_supported():
    """返回模块是否可用"""
    return False


def recognize(img, lang, *, hints=None):
    """
    识别图像中的文本并返回 OcrResult

    :param img: 需要识别的图像, PIL.Image.Image 对象
    :param lang: 需要识别的语言，BCP-47 格式字符串
    :param hints: 对 OCR 引擎的提示，OcrHint 中定义的值的列表
    :returns: OcrResult

    OcrResult = {
        lines: Tuple[OcrLine],
        extra: Any # 引擎返回的额外信息
    }

    OcrLine = {
        words: Tuple[OcrWord],
        extra: Any
    }

    OcrWord = {
        text: str,
        rect: Rect,
        extra: Any     
    }
    """
    from .common import OcrResult
    return OcrResult(tuple())

