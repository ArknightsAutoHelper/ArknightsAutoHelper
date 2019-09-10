import copy

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
            self.set_right(right)
        if bottom is not None:
            self.set_bottom(bottom)

    def __repr__(self):
        return 'Rect(%d, %d, %d, %d)' % (self.x, self.y, self.width, self.height)

    def right(self):
        return self.x + self.width

    def bottom(self):
        return self.y + self.height

    def set_right(self, value):
        self.width = value - self.x

    def set_bottom(self, value):
        self.height = value - self.y
    
    def __iter__(self):
        return iter((self.x, self.y, self.right(), self.bottom()))

class OcrObject:
    def __init__(self):
        self.extra = None

    def __repr__(self):
        return self.__dict__.__repr__()

class OcrWord(OcrObject):
    def __init__(self, rect, text):
        super().__init__()
        self.rect = rect
        self.text = text

class OcrLine(OcrObject):
    def __init__(self, words):
        super().__init__()
        self.words = words
        self.merged_words = merge_words(words)
        self.merged_text = ' '.join(x.text for x in self.merged_words)
        self.text = ' '.join(x.text for x in self.words)

class OcrResult(OcrObject):
    def __init__(self, lines):
        super().__init__()
        self.lines = lines
        self.text = ' '.join(x.text for x in lines)

def merge_words(words):
    if len(words) == 0:
        return words
    new_words = [copy.deepcopy(words[0])]
    words = words[1:]
    for word in words:
        lastnewword = new_words[-1]
        lastnewwordrect = new_words[-1].rect
        wordrect = word.rect
        if len(word.text) == 1 and wordrect.x - lastnewwordrect.right() <= wordrect.width * 0.2:
            lastnewword.text += word.text
            lastnewwordrect.x = min((wordrect.x, lastnewwordrect.x))
            lastnewwordrect.y = min((wordrect.y, lastnewwordrect.y))
            lastnewwordrect.set_right(max((wordrect.right(), lastnewwordrect.right())))
            lastnewwordrect.set_bottom(max((wordrect.bottom(), lastnewwordrect.bottom())))
        else:
            new_words.append(copy.deepcopy(word))
    return new_words
