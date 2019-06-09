from aip import AipOcr
from config import *

client = AipOcr(APP_ID, API_KEY, SECRET_KEY)


def get_file_content(filePath):
    """ 读取图片 """
    with open(filePath, 'rb') as fp:
        return fp.read()


def ocr(file_path, save_path, line=0):
    """
    调用百度api进行图片识别
    :param file_path: ocr识别图片路径
    :param save_path: 识别结果保存路径
    :param line: 选择行数，暂时没有用途，以防万一留下这个变量，默认为第一行
    :return: 返回总行数（原打算debug使用，现直接在函数内完成）
    """
    image = get_file_content(file_path)

    """ 调用通用文字识别, 图片参数为本地图片 """
    # global result
    result = client.basicGeneral(image)
    f = open(save_path, 'w+', encoding="utf8")
    if result["words_result_num"] is not 0:
        f.write(result["words_result"][line]["words"])
    else:
        f.write("未检测到文本")
    return result["words_result_num"]


# API返回参考
# 文档地址：https://cloud.baidu.com/doc/OCR/OCR-Python-SDK.html#.E9.80.9A.E7.94.A8.E6.96.87.E5.AD.97.E8.AF.86.E5.88.AB
"""
{
# 这个id好像暂时没有用
"log_id": 2471272194,
# 检测文本一共几行
"words_result_num": 2,
# 文本内容
"words_result":
    [
        {"words": " TSINGTAO"},
        {"words": "青島睥酒"}
    ]
}
"""