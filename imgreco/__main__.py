import sys

if len(sys.argv) > 1:
    from PIL import Image
    import imgreco
    obj = imgreco
    objname = '.'.join(sys.argv[1:-1])
    for k in sys.argv[1:-1]:
        obj = getattr(obj, k)
    print('> imgreco.%s(Image.open(%s))' % (objname, repr(sys.argv[-1])))
    print(obj(Image.open(sys.argv[-1])))
else:
    print('usage: python -m imgreco module_name function_name image_file')
