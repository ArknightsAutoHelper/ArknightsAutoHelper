from PIL import Image


def binarization_image(filepath, threshold=200):
    picture = Image.open(filepath)
    _L_form = picture.convert('L')
    table = []
    for i in range(256):
        if i < threshold:
            table.append(1)
        else:
            table.append(0)
    bim = _L_form.point(table, '1')
    bim.save(filepath)
