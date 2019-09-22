from PIL import Image
def any_in(keys, collection):
    for k in keys:
        if k in collection:
            return True
    return False


def get_vwvh(size):
    if isinstance(size, tuple):
        return (size[0]/100, size[1]/100)
    return (size.width/100, size.height/100)

def uniform_size(img1, img2):
    if img1.height < img2.height:
        img2 = img2.resize(img1.size, Image.BILINEAR)
    elif img1.height > img2.height:
        img1 = img1.resize(img2.size, Image.BILINEAR)
    elif img1.width != img2.width:
        img1 = img1.resize(img2.size, Image.BILINEAR)
    return (img1, img2)
