import sys
import io
import os
from ..common import *
from .common import *
import logging
from . import tessbaseapi

logger = logging.getLogger(__name__)

is_online = False
info = "libtesseract"

get_version = lambda: tessbaseapi.version
check_supported = lambda: True
version = tessbaseapi.version

class LibTesseractEngine(BaseTesseractEngine):
    def __init__(self, lang, **kwargs):
        super().__init__(lang, **kwargs)
        vars = {'debug_file': os.devnull, 'classify_enable_learning': '0'}
        if 'app' in sys.modules:
            import app
            if app.config.debug:
                del vars['debug_file']
                vars['log_level'] = '0'
        try:
            self.baseapi = tessbaseapi.BaseAPI(self.tessdata_prefix, self.tesslang, vars=vars)
        except UnicodeEncodeError:
            if sys.platform == 'win32':
                logger.warning('failed to encode tessdata prefix or language in CP_ACP, trying CRT UTF-8 hack')
                self.baseapi = tessbaseapi.BaseAPI(self.tessdata_prefix, self.tesslang, vars=vars, win32_use_utf8=True)
            else:
                raise
        self.features = ('single_line_hint', 'sparse_hint', 'char_whitelist')

    def recognize(self, image, ppi=70, hints=None, **kwargs):
        self.baseapi.set_image(image, ppi)
        if hints is None:
            hints = []
        tessvars = {}
        if OcrHint.SINGLE_LINE in hints:
            tessvars['tessedit_pageseg_mode'] = '7'
        elif OcrHint.SPARSE in hints:
            tessvars['tessedit_pageseg_mode'] = '11'
        if 'char_whitelist' in kwargs:
            tessvars['tessedit_char_whitelist'] = kwargs.pop('char_whitelist')
        for key, value in kwargs.items():
            tessvars[key] = value
        
        old_tessvars = {name: self.baseapi.get_variable(name) for name in tessvars}
        logger.debug('old tessvars: %r', old_tessvars)
        self.baseapi.recognize()
        result = parse_hocr(io.BytesIO(self.baseapi.get_hocr()))
        for name, value in old_tessvars.items():
            self.baseapi.set_variable(name, value)
        for key in kwargs:
            self.baseapi.set_variable(key, None)
        self.baseapi.clear()
        return result

Engine = LibTesseractEngine


__all__ = ['info', 'get_version', 'check_supported', 'is_online', 'Engine']
