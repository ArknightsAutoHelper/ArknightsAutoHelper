import os
import ctypes
import ctypes.util
import platform

import numpy as np

def getlibname(base, sover=None):
    system = platform.system()
    if system == 'Windows':
        return 'lib{}-{}.dll'.format(base, sover) if sover is not None else 'lib{}.dll'.format(base)
    elif system == 'Linux':
        return 'lib{}.so.{}'.format(base, sover) if sover is not None else 'lib{}.so'.format(base)
    else:
        raise NotImplementedError()


def resolve_libpath():
    lib = ctypes.util.find_library(getlibname('tesseract', '5'))
    if lib:
        return lib
    lib = ctypes.util.find_library(getlibname('tesseract', '4'))
    if lib:
        return lib
    return None


def resolve_datapath():
    if platform.system() == 'Windows':
        libpath = resolve_libpath()
        if libpath:
            return os.path.join(os.path.dirname(libpath), 'tessdata')
    return None


def cfunc(lib, name, restype, *argtypes):
    func = getattr(lib, name)
    func.restype = restype
    func.argtypes = argtypes
    return func


libname = resolve_libpath()
if libname:
    tesseract = ctypes.cdll.LoadLibrary(libname)
    TessVersion = cfunc(tesseract, 'TessVersion', ctypes.c_char_p)
    TessBaseAPICreate = cfunc(tesseract, 'TessBaseAPICreate', ctypes.c_void_p)
    TessBaseAPIInit4 = cfunc(tesseract, 'TessBaseAPIInit4', ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int)
    TessBaseAPISetImage = cfunc(tesseract, 'TessBaseAPISetImage', None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
    TessBaseAPIGetHOCRText = cfunc(tesseract, 'TessBaseAPIGetHOCRText', ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int)
    TessDeleteText = cfunc(tesseract, 'TessDeleteText', None, ctypes.c_void_p)
    TessBaseAPIEnd = cfunc(tesseract, 'TessBaseAPIEnd', None, ctypes.c_void_p)
    TessBaseAPIDelete = cfunc(tesseract, 'TessBaseAPIDelete', None, ctypes.c_void_p)
    TessBaseAPISetSourceResolution = cfunc(tesseract, 'TessBaseAPISetSourceResolution', None, ctypes.c_void_p, ctypes.c_int)
    TessBaseAPISetVariable = cfunc(tesseract, 'TessBaseAPISetVariable', ctypes.c_bool, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p)
    version = TessVersion().decode()
    import logging
    logger = logging.getLogger(__name__)
    logger.debug('using libtesseract C interface %s', version)
else:
    raise ModuleNotFoundError()


class TessOcrEngineMode:
    OEM_TESSERACT_ONLY = 0
    OEM_LSTM_ONLY = 1
    OEM_TESSERACT_LSTM_COMBINED = 2
    OEM_DEFAULT = 3


class BaseAPI:
    def __init__(self, datapath, language, oem=TessOcrEngineMode.OEM_DEFAULT, configs=None, vars=None, set_only_non_debug_params=False):
        self.baseapi = None
        self.baseapi = ctypes.c_void_p(TessBaseAPICreate())
        if datapath is not None:
            datapath = datapath.encode()
        if configs is not None:
            configlen = len(configs)
            configsarr = (ctypes.c_char_p * configlen)()
            configsarr[:] = (x.encode() for x in configs)
        else:
            configsarr = None
            configlen = 0
        if vars is not None:
            varlen = len(vars)
            arrtype = ctypes.c_char_p * varlen
            varnamearr = arrtype()
            varnamearr[:] = [x.encode() for x in vars.keys()]
            varvaluearr = arrtype()
            varvaluearr[:] = [str(x).encode() for x in vars.values()]
        else:
            varlen = 0
            varnamearr = None
            varvaluearr = None
        result = TessBaseAPIInit4(self.baseapi, datapath, language.encode(), oem, configsarr, configlen, varnamearr, varvaluearr, varlen, set_only_non_debug_params)
        if result != 0:
            raise RuntimeError('Tesseract initialization failed')

    def __del__(self):
        self.release()

    def release(self):
        if self.baseapi is not None and self.baseapi.value:
            TessBaseAPIEnd(self.baseapi)
            TessBaseAPIDelete(self.baseapi)
        self.release = lambda: None

    def set_image(self, image, ppi=70):
        imgarr = np.asarray(image)
        height, width, *channels = imgarr.shape
        if len(channels) == 0:
            channels = 1
        else:
            channels = channels[0]
        arrdata = imgarr.ctypes
        strides = list(arrdata.strides)
        if strides[1] != channels:
            imgarr = np.array(image)
            arrdata = imgarr.ctypes
            strides = arrdata.strides
            if strides[1] != channels:
                raise RuntimeError("unable to get image data with correct bpp")
        bpp = channels * imgarr.itemsize
        TessBaseAPISetImage(self.baseapi, imgarr.ctypes.data, width, height, bpp, strides[0])
        TessBaseAPISetSourceResolution(self.baseapi, ppi)

    def get_hocr(self):
        ptr = ctypes.c_void_p(TessBaseAPIGetHOCRText(self.baseapi, 0))
        hocrbytes = ctypes.string_at(ptr)
        TessDeleteText(ptr)
        return hocrbytes

    def set_variable(self, name, value):
        return TessBaseAPISetVariable(self.baseapi, name.encode(), value.encode())


if __name__ == '__main__':
    import cv2
    print(version)
    tess = BaseAPI(r"C:\Users\dant\AppData\Local\Tesseract-OCR\tessdata", 'chi_sim', vars={'tessedit_pageseg_mode': '7'})
    tess.set_image(cv2.imread(r"/imgreco/resources/end_operation/end.png"), 144)
    print(tess.get_hocr())
    tess.release()
