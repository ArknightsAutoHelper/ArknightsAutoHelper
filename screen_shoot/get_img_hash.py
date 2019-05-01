import hashlib
from config import *
from PIL import Image


def img_hash(img):
    with open(SCREEN_SHOOT_SAVE_PATH + img, "rb") as m:
        return hashlib.md5(m.read()).hexdigest()


def difference(img1, img2):
    img1 = Image.open(img1).convert('1')
    img2 = Image.open(img2).convert('1')
    hist1 = list(img1.getdata())
    hist2 = list(img2.getdata())
    sum1 = 0
    for i in range(len(hist1)):
        if (hist1[i] == hist2[i]):
            sum1 += 1
        else:
            sum1 += 1 - float(abs(hist1[i] - hist2[i])) / max(hist1[i], hist2[i])
    return sum1 / len(hist1)


if __name__ == '__main__':
    print(difference(
        img1=SCREEN_SHOOT_SAVE_PATH + "battle_end.png",
        img2=STORAGE_PATH + "BATTLE_INFO_BATTLE_END_TRUE.png"
    ))
# print(difference(
#     list(img1.getdata()), list(img2.getdata())
# ))

# print(img_hash("2-1_0.png"))
# print(img_hash("2-1_1.png"))

# 50b61d0d90acf7d9baa9fa99f046c3fc
# 225cd2660e1442f008bf225d72770f22

# 848b08483fe476ae027d917eebb81a97
# 1bced79e315675f1634255867026e53e
