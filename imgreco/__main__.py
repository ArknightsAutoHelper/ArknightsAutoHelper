import sys
import logging

logging.basicConfig(level=logging.NOTSET)

if len(sys.argv) > 1:
    from util import cvimage as Image
    import imgreco
    obj = imgreco
    objname = '.'.join(sys.argv[1:-1])
    print('> imgreco.%s(Image.open(%s))' % (objname, repr(sys.argv[-1])))
    known = ['imgreco']
    tag = object()
    for k in sys.argv[1:-1]:
        obj = getattr(obj, k, tag)
        if obj is tag:
            print("%s has no attribute %r, try import" % ('.'.join(known), k))
            import importlib
            obj = importlib.import_module('.'.join(known+[k]))
    print(obj(Image.open(sys.argv[-1])))
else:
    print('usage: python -m imgreco module_name function_name image_file')
