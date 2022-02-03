import sys
import os
import contextlib
import ctypes
import ctypes.util
import platform

import numpy as np

def resolve_libpath():
    if sys.platform == 'win32' and 'app' in sys.modules:
        try:
            import app
            vendor_path = str(app.get_vendor_path('tesseract'))
            if vendor_path not in os.environ['PATH']:
                os.environ['PATH'] += os.pathsep + vendor_path
        except:
            pass
    names = [
        # common library name for UNIX-like systems
        'tesseract',
        # MSVC library
        'tesseract41.dll',
        'tesseract50.dll',
        # MinGW library
        'libtesseract-4.dll',
        'libtesseract-5.dll'
    ]
    for name in names:
        lib = ctypes.util.find_library(name)
        if lib:
            return lib
    return None


def get_default_datapath():
    if platform.system() == 'Windows':
        libpath = resolve_libpath()
        if libpath:
            return os.path.dirname(libpath).joinpath('tessdata')
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
    TessBaseAPIInit4 = cfunc(tesseract, 'TessBaseAPIInit4', ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int)
    TessBaseAPISetImage = cfunc(tesseract, 'TessBaseAPISetImage', None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
    TessBaseAPIRecognize = cfunc(tesseract, 'TessBaseAPIRecognize', ctypes.c_void_p, ctypes.c_void_p)
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
    from util.unfuck_crtpath import encode_mbcs_path, crt_use_utf8, find_crt
    _crts = find_crt()
else:
    raise ModuleNotFoundError()


class TessOcrEngineMode:
    OEM_TESSERACT_ONLY = 0
    OEM_LSTM_ONLY = 1
    OEM_TESSERACT_LSTM_COMBINED = 2
    OEM_DEFAULT = 3


class BaseAPI:
    def __init__(self, datapath, language, oem=TessOcrEngineMode.OEM_DEFAULT, configs=None, vars=None, set_only_non_debug_params=False, win32_use_utf8=False):
        self._api_context_factory = lambda: contextlib.nullcontext()
        self.baseapi = None
        self.baseapi = ctypes.c_void_p(TessBaseAPICreate())
        if sys.platform != 'win32' or win32_use_utf8:
            self.fsencoding = 'utf-8'
        else:  # win32
            self.fsencoding = 'mbcs'
        if win32_use_utf8:
            self._api_context_factory = lambda: crt_use_utf8(_crts)
        if datapath is None:
            datapath = get_default_datapath()  # use installation path for windows instead of current executable (python.exe)
        if datapath is not None:  # still can be None here
            if self.fsencoding == 'mbcs':
                datapath = encode_mbcs_path(datapath)
            else:
                datapath = str(datapath).encode(self.fsencoding)
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
            varsitems = list(vars.items())
            varnamearr[:] = [k.encode() for k, v in varsitems]
            varvaluearr = arrtype()
            varvaluearr[:] = [str(v).encode() for k, v in varsitems]
        else:
            varlen = 0
            varnamearr = None
            varvaluearr = None
        with self._api_context_factory():
            result = TessBaseAPIInit4(self.baseapi, datapath, language.encode(self.fsencoding), oem, configsarr, configlen, varnamearr, varvaluearr, varlen, set_only_non_debug_params)
        if result != 0:
            raise RuntimeError('Tesseract initialization failed')

    def __del__(self):
        self.release()

    def release(self):
        if self.baseapi is not None and self.baseapi.value:
            with self._api_context_factory():
                TessBaseAPIEnd(self.baseapi)
                TessBaseAPIDelete(self.baseapi)
            self.baseapi = None

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
        with self._api_context_factory():
            TessBaseAPISetImage(self.baseapi, imgarr.ctypes.data, width, height, bpp, strides[0])
            TessBaseAPISetSourceResolution(self.baseapi, ppi)

    def recognize(self):
        with self._api_context_factory():
            TessBaseAPIRecognize(self.baseapi, None)

    def get_hocr(self):
        with self._api_context_factory():
            ptr = TessBaseAPIGetHOCRText(self.baseapi, 0)
        hocrbytes = ctypes.string_at(ptr)
        TessDeleteText(ptr)
        return hocrbytes

    def set_variable(self, name, value):
        with self._api_context_factory():
            return TessBaseAPISetVariable(self.baseapi, name.encode(), b'' if value is None else value.encode())


if __name__ == '__main__':
    import cv2
    print(version)
    tess = BaseAPI(r"C:\Users\dant\AppData\Local\Tesseract-OCR\tessdata", 'chi_sim', vars={'tessedit_pageseg_mode': '7'})
    tess.set_image(cv2.imread(r"/imgreco/resources/end_operation/end.png"), 144)
    print(tess.get_hocr())
    tess.release()
