import io
import os
from ..common import *
from .common import *
from . import tessbaseapi

is_online = False
info = "libtesseract"

get_version = lambda: tessbaseapi.version
check_supported = lambda: True
version = tessbaseapi.version

class LibTesseractEngine(BaseTesseractEngine):
    def __init__(self, lang, **kwargs):
        super().__init__(lang, **kwargs)
        self.baseapi = tessbaseapi.BaseAPI(tessbaseapi.resolve_datapath(), self.tesslang, vars={'debug_file': os.devnull})
        self.features = ('single_line_hint', 'sparse_hint', 'char_whitelist')

    def recognize(self, image, ppi=70, hints=None, **kwargs):
        self.baseapi.set_image(image, ppi)
        if hints is None:
            hints = []
        if OcrHint.SINGLE_LINE in hints:
            self.baseapi.set_variable('tessedit_pageseg_mode', '7')
        elif OcrHint.SPARSE in hints:
            self.baseapi.set_variable('tessedit_pageseg_mode', '11')
        if 'char_whitelist' in kwargs:
            self.baseapi.set_variable('tessedit_char_whitelist', kwargs['char_whitelist'])

        result = parse_hocr(io.BytesIO(self.baseapi.get_hocr()))
        self.baseapi.set_variable('tessedit_pageseg_mode', '')
        if 'char_whitelist' in kwargs:
            self.baseapi.set_variable('tessedit_char_whitelist', '')

        return result

Engine = LibTesseractEngine


__all__ = ['info', 'get_version', 'check_supported', 'is_online', 'Engine']
