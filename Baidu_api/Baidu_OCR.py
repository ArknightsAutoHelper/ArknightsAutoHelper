from aip import AipOcr
from config import *

client = AipOcr(APP_ID, API_KEY, SECRET_KEY)


def get_file_content(filePath):
    """ 读取图片 """
    with open(filePath, 'rb') as fp:
        return fp.read()


def ocr(file_path, save_path, line=0):
    image = get_file_content(file_path)

    """ 调用通用文字识别, 图片参数为本地图片 """
    result = client.basicGeneral(image)
    with open(save_path, 'w+', encoding="utf8") as f:
        f.write(result["words_result"][line]["words"])
    return result["words_result"][line]["words"]
