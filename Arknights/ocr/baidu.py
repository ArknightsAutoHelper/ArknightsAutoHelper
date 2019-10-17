from io import BytesIO

from aip import AipOcr

from config import enable_baidu_api, APP_ID, API_KEY, SECRET_KEY
from .common import *

is_online = True
info = "baidu"


def check_supported():
    if enable_baidu_api:
        return True
    else:
        return False


def _options(option):
    options = {}
    subtags = option.lower().split('-')
    if subtags[0] == 'en':
        options["language_type"] = "ENG"
    elif subtags[0] == 'zh':
        options["language_type"] = "CHN_ENG"
    return options


def baidu_ocr(img, options, line=0):
    """
    调用百度api进行图片识别
    :param options: 百度ocr选项
    :param img: 获取图片
    :param line: 选择行数，暂时没有用途，以防万一留下这个变量，默认为第一行
    :return: 返回识别结果
    """
    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    image = img
    """ 调用通用文字识别, 图片参数为本地图片 """
    result = client.basicGeneral(image, _options(options))

    if result["words_result_num"] > 1 or line >= 1:
        # TODO
        raise NotImplementedError
    elif result["words_result_num"] == 1:
        return result["words_result"][line]["words"]
    else:
        return ""


def recognize(image, lang, *, hints=None):
    if hints is None:
        hints = []
    if OcrHint.SINGLE_LINE in hints:
        line = 0
    elif OcrHint.SPARSE in hints:
        # TODO
        line = 1
    imgbytesio = BytesIO()
    if 'RGB' not in image.mode:
        image = image.convert('RGB')
    image.save(imgbytesio, format='PNG')
    result = OcrResult(())
    result.text = baidu_ocr(imgbytesio.getvalue(), lang, line)
    return result
