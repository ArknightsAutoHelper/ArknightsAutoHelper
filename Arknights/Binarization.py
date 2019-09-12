from os import sys

from PIL import Image, ImageOps, ImageFilter
from shutil import copy


def binarization_image(filepath, save_backup=False, invert_image=True, threshold=127):
    """
    锐化图片，二值化图像，之后颜色反转，以增加ocr识别精确度
    原因是tesseract在识别黑底白字和白底黑字会有不同表现：
    黑底白字有问题，而白底黑字可以识别
    Arknights中截取的图片大多为黑底白字，所以转变为白底黑字
    :param invert_image: 是否颜色反转图片，绝大部分如理智判断，需要反转图片，但有部分不需要
    :param filepath: 进行二值化的图片路径
    :param save_backup: 是否启动图片备份。
    :param threshold: 临界灰度值，原来是200，现在改为175，有人report问题issue#24; 现在改回PIL默认的127，鬼知道为啥之前的就不行
    :return: 返回二值化图片，但暂时没有用，tesseract的调用方式导致必须有个图片路径，
             变量的方式不知道怎么弄过去，百度OCR倒是可以，但没弄
    """
    # 百度api有的时候需要二值化，有时二值化反而会造成负面影响
    if save_backup:
        # 这里给二值化前的图片留个底，确认二值化异常的原因
        try:
            copy(filepath, filepath + ".DebugBackup.png")
        except IOError as e:
            print("Unable to copy file. {}".format(e))
        except:
            print("Unexpected error:", sys.exc_info())
    picture = Image.open(filepath)
    # 锐化图片
    sharpen = picture.filter(ImageFilter.SHARPEN)
    # 灰度化
    final = sharpen.convert('L')
    # 颜色反转
    if invert_image:
        final = ImageOps.invert(final)
    # 二值化，这里其实可以直接使用inverted_image.convert(1)来完成，但为了保障阈值可控，这里“手动”一下
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
    bim = final.point(table, '1')

    bim.save(filepath)
    return bim

def image_threshold(image, threshold=127):
    """
    threshold filter on L channel
    :param threshold: negative value means inverted output
    """
    if threshold < 0:
        lut = lambda x: 0 if x > -threshold else 1
    else:
        lut = lambda x: 1 if x > threshold else 0
    return image.convert('L').point(lut, '1') 
