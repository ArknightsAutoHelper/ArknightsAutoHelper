import copy
from dataclasses import dataclass, field
from abc import ABC
from typing import Any, List


def mult_in(needles, haystack):
    for needle in needles:
        if needle in haystack:
            return True
    return False


class OcrHint:
    SINGLE_LINE = 'single_line'
    SPARSE = 'sparse'


class Rect:
    def __init__(self, x, y, w=0, h=0, *, right=None, bottom=None):
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        if right is not None:
            self.right = right
        if bottom is not None:
            self.bottom = bottom

    def __repr__(self):
        return 'Rect(%d, %d, %d, %d)' % (self.x, self.y, self.width, self.height)

    @property
    def right(self):
        return self.x + self.width

    @right.setter
    def right(self, value):
        self.width = value - self.x

    @property
    def bottom(self):
        return self.y + self.height

    @bottom.setter
    def bottom(self, value):
        self.height = value - self.y

    def __iter__(self):
        return iter((self.x, self.y, self.right(), self.bottom()))


@dataclass
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

    def recognize(self, image, ppi=70, *, hints=None):
        raise NotImplementedError()
