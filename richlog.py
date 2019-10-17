from base64 import b64encode
from functools import lru_cache
from io import BytesIO


class RichLogger:
    def __init__(self, file, overwrite=False):
        self.f = open(file, 'wb' if overwrite else 'ab')
        if self.f.tell() == 0:
            self.loghtml('<html><head><meta charset="utf-8"></head><body>')

    def logimage(self, image):
        bio = BytesIO()
        image.save(bio, format='PNG')
        imgb64 = b64encode(bio.getvalue())
        self.f.write(b'<p><img src="data:image/png;base64,%s" /></p>\n' % imgb64)

    def logtext(self, text):
        self.loghtml('<pre>%s</pre>\n' % text)

    def loghtml(self, html):
        self.f.write(html.encode())


@lru_cache(maxsize=None)
def get_logger(file):
    logger = RichLogger(file, True)
    return logger
