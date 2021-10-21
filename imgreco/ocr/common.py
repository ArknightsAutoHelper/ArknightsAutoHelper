from dataclasses import dataclass, field
from abc import ABC
from typing import Any, List
from util.cvimage import Rect

def mult_in(needles, haystack):
    for needle in needles:
        if needle in haystack:
            return True
    return False


class OcrHint:
    SINGLE_LINE = 'single_line'
    SPARSE = 'sparse'


dataclass
class OcrObject:
    extra: Any = field(default=None, init=False)


@dataclass
class OcrWord(OcrObject):
    rect: Rect
    text: str


@dataclass
class OcrLine(OcrObject):
    words: List[OcrWord]

    @property
    def text(self):
        return ' '.join(x.text for x in self.words)


@dataclass
class OcrResult(OcrObject):
    lines: List[OcrLine]

    @property
    def text(self):
        return ' '.join(x.text for x in self.lines)

    def __contains__(self, text):
        return text in self.text.replace(' ', '')

    def __repr__(self):
        return 'OcrResult[%s]' % repr(self.text)


class OcrEngine(ABC):
    def __init__(self, lang, **kwargs):
        self.lang = lang
        self.kwargs = kwargs
        self.features = ()

    def recognize(self, image, ppi=70, hints=None, **kwargs):
        raise NotImplementedError()
