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

    def recognize(self, image, ppi=70, hints=None, **kwargs):
        if hints is None:
            hints = []
        extras = []
        if OcrHint.SINGLE_LINE in hints:
            extras.extend(('--psm', '7'))
        elif OcrHint.SPARSE in hints:
            extras.extend(('--psm', '11'))
        if 'char_whitelist' in kwargs:
            extras.extend(('-c', 'tessedit_char_whitelist=' + kwargs['char_whitelist']))

        tslang = self.tesslang
        imgbytesio = BytesIO()
        if 'RGB' not in image.mode:
            image = image.convert('RGB')
        image.save(imgbytesio, format='PNG')
        proc = subprocess.run(['tesseract', 'stdin', 'stdout', '--dpi', str(ppi), '-l', tslang, *extras,
                               'hocr'], input=imgbytesio.getvalue(), capture_output=True, check=True)

        return parse_hocr(BytesIO(proc.stdout))


Engine = TesseractSubprocessEngine

info = "tesseract (CLI)"

__all__ = ['info', 'get_version', 'check_supported', 'is_online', 'Engine']
