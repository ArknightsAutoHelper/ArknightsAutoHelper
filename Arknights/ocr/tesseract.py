import subprocess
from xml.etree import ElementTree
from io import BytesIO
from .common import *

is_online = False


def _translate_bcp47(tag):
    subtags = tag.lower().split('-')

    if subtags[0] == 'en':
        return 'eng'
    elif subtags[0] == 'zh':
        if mult_in(('cn', 'sg', 'my', 'hans'), subtags[1:]):
            return 'chi_sim'
        elif mult_in(('tw', 'hk', 'mo', 'hant'), subtags[1:]):
            return 'chi_tra'

    return None


def get_version():
    try:
        version = subprocess.run(['tesseract', '--version'], capture_output=True).stdout.decode('utf-8').splitlines()[0]
        global info
        info = version
        return version
    except:
        return None


check_supported = lambda: get_version() is not None


def _parse_word(xmlword):
    attrs = dict(attrstr.split(' ', 1)
                 for attrstr in xmlword.attrib['title'].split('; '))
    left, top, right, bottom = tuple(map(int, attrs.pop('bbox').split(' ')))
    rc = Rect(left, top, right=right, bottom=bottom)
    result = OcrWord(rc, xmlword.text)
    result.extra = attrs
    return result


def _parse_line(xmlline):
    words = tuple(
        map(_parse_word, xmlline.findall('.//*[@class="ocrx_word"]')))
    attrs = dict(attrstr.split(' ', 1)
                 for attrstr in xmlline.attrib['title'].split('; '))
    result = OcrLine(words)
    result.extra = attrs
    return result


def parse_hocr(file):
    tree = ElementTree.parse(file)
    root = tree.getroot()
    lines = root.findall('.//*[@class="ocr_line"]')
    ocrlines = tuple(map(_parse_line, lines))
    return OcrResult(ocrlines)


def recognize(image, lang, *, hints=None):
    if hints == None:
        hints = []
    extras = []
    if OcrHint.SINGLE_LINE in hints:
        extras.extend(('--psm', '7'))
    elif OcrHint.SPARSE in hints:
        extras.extend(('--psm', '11'))

    tslang = _translate_bcp47(lang)
    imgbytesio = BytesIO()
    if 'RGB' not in image.mode:
        image = image.convert('RGB')
    image.save(imgbytesio, format='PNG')
    proc = subprocess.run(['tesseract', 'stdin', 'stdout', '-l', tslang, *extras,
                           'hocr'], input=imgbytesio.getvalue(), capture_output=True, check=True)

    return parse_hocr(BytesIO(proc.stdout))


info = "tesseract"
