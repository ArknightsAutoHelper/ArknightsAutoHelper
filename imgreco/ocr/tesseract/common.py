from abc import ABC
from xml.etree import ElementTree
from ..common import *

def translate_bcp47(tag):
    subtags = tag.lower().split('-')

    if subtags[0] == 'en':
        return 'eng'
    elif subtags[0] == 'zh':
        if mult_in(('cn', 'sg', 'my', 'hans'), subtags[1:]):
            return 'chi_sim'
        elif mult_in(('tw', 'hk', 'mo', 'hant'), subtags[1:]):
            return 'chi_tra'

    return None


def _parse_word(xmlword):
    attrs = dict(attrstr.split(' ', 1)
                 for attrstr in xmlword.attrib['title'].split('; '))
    left, top, right, bottom = tuple(map(int, attrs.pop('bbox').split(' ')))
    rc = Rect(left, top, right=right, bottom=bottom)
    result = OcrWord(rc, xmlword.text)
    result.extra = attrs
    return result


def _parse_line(xmlline):
    words = list(
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
    ocrlines = list(map(_parse_line, lines))
    return OcrResult(ocrlines)


class BaseTesseractEngine(OcrEngine, ABC):
    def __init__(self, lang, **kwargs):
        super().__init__(lang, **kwargs)
        self.tesslang = translate_bcp47(lang)
