from Arknights.Binarization import binarization_image
from config import *

rebase_to_null = " 1>nul 2>nul" \
    if "win32" in os.sys.platform \
    else " 1>/dev/null 2>/dev/null &" \
    if enable_rebase_to_null else ""


def get_loacation(filepath, option="makebox", change_image=False):
    if change_image:
        # image = Image.open(filepath)
        # 对图片进行阈值过滤，然后保存
        # image = image.point(lambda x: 0 if x < 143 else 255)
        # image.save(filepath)
        binarization_image(filepath)
    os.popen(
        'tesseract "{}"  "{}" {}'.format(filepath, filepath, option)
    )

# get_loacation("E:\\GitHub\\ArknightsAutoHelper\\screen_shoot\\20197311333882Screenshot_2019-08-31-10-27-02_4.png")
