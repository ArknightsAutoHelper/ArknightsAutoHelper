import sys
from PIL import Image, ImageFont
import numpy as np

def fuck(fontname, fontsize, text, savefile):
    font = ImageFont.truetype(fontname, int(fontsize))
    mask = font.getmask(text, 'L')
    img = Image.new('L', mask.size)
    img.putdata(mask)
    
    lut = np.zeros(256, dtype=np.uint8)
    lut[127:] = 1
    maskim = img.point(lut, '1')

    bbox = maskim.getbbox()
    img = img.crop(bbox)
    img.save(savefile)

if __name__ == "__main__":
    names = ('常规掉落','额外物资', '特殊掉落', '幸运掉落', '首次掉落', '报酬', '理智返还', '1.2倍声望&龙门币奖励', '1.0倍声望&龙门币奖励')
    for name in names:
        fuck(r'D:\projects\akimgreco\NotoSansCJKsc-Medium.otf', 25, name, name+'.png')
