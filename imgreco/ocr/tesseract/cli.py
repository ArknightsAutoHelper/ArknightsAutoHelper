import os
import subprocess
from io import BytesIO

from imgreco.ocr.common import *
from .common import *

is_online = False


def get_version():
    try:
        version = subprocess.run(['tesseract', '--version'], capture_output=True).stdout.decode('utf-8').splitlines()[0]
        global info
        info = version
        return version
    except:
        return None


check_supported = lambda: get_version() is not None


class TesseractSubprocessEngine(BaseTesseractEngine):
    def __init__(self, lang, **kwargs):
        super().__init__(lang, **kwargs)
        self.features = ('single_line_hint', 'sparse_hint', 'char_whitelist')
        if sys.platform == 'win32' and self.tessdata_prefix is not None:
            from util.unfuck_crtpath import query_short_path
            self.tessdata_prefix = query_short_path(self.tessdata_prefix)

    def recognize(self, image, ppi=70, hints=None, **kwargs):
        if hints is None:
            hints = []
        extras = ['-c', 'tessedit_create_hocr=1', '-c', 'hocr_font_info=0']
        if OcrHint.SINGLE_LINE in hints:
            extras.extend(('--psm', '7'))
        elif OcrHint.SPARSE in hints:
            extras.extend(('--psm', '11'))
        if 'char_whitelist' in kwargs:
            extras.extend(('-c', 'tessedit_char_whitelist=' + kwargs['char_whitelist']))
        for key, value in kwargs:
            extras.extend(('-c', key+'='+value))
        tslang = self.tesslang
        imgbytesio = BytesIO()
        if 'RGB' not in image.mode:
            image = image.convert('RGB')
        image.save(imgbytesio, format='PNG')
        if self.tessdata_prefix is not None:
            env = dict(os.environ)
            env['TESSDATA_PREFIX'] = self.tessdata_prefix
        else:
            env = os.environ
        proc = subprocess.run(['tesseract', 'stdin', 'stdout', '--dpi', str(ppi), '-l', tslang, *extras], 
                              input=imgbytesio.getvalue(), env=env, capture_output=True, check=True)
        return parse_hocr(BytesIO(proc.stdout))


Engine = TesseractSubprocessEngine

info = "tesseract (CLI)"

__all__ = ['info', 'get_version', 'check_supported', 'is_online', 'Engine']
