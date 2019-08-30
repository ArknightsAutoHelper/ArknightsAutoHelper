from os import system

from PIL import Image

from config.developer_config import enable_baidu_api


def binarization_image(filepath, threshold=175):
    """
    二值化图像，增加ocr识别精确度，但这里还直接进行了颜色反转
    原因是tesseract在识别黑底白字和白底黑字会有不同表现：
    黑底白字有问题，而白底黑字可以识别
    Arknights中截取的图片大多为黑底白字，所以转变为白底黑字
    :param filepath: 进行二值化的图片路径
    :param threshold: 临界灰度值，原来是200，现在改为175，有人report问题issue#24
    :return: 返回二值化图片，但暂时没有用，tesseract的调用方式导致必须有个图片路径，
             变量的方式不知道怎么弄过去，百度OCR倒是可以，但没弄
    """
    # 这里给二值化前的图片留个底，确认二值化异常的原因
    if enable_baidu_api is False:
        system(
            'copy {} {}'.format(filepath,
                                filepath + ".debug"))
    picture = Image.open(filepath)
    _L_form = picture.convert('L')
    table = []
    for i in range(256):
        if i < threshold:
            # 一般这里应该是0，但进行反转所以互换
            table.append(1)
        else:
            table.append(0)
    bim = _L_form.point(table, '1')
    bim.save(filepath)
    return bim
