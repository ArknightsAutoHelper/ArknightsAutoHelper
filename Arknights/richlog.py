from html import escape
from io import BytesIO
from base64 import b64encode

class RichLogger:
    def __init__(self, file, overwrite=False):
        self.f = open(file, 'wb' if overwrite else 'ab')

    def logimage(self, image):
        bio = BytesIO()
        image.save(bio, format='PNG')
        imgb64 = b64encode(bio.getvalue())
        self.f.write(b'<p><img src="data:image/png;base64,%s" /></p>\n' % imgb64)
    
    def logtext(self, text):
        self.loghtml('<pre>%s</pre>\n' % text.encode())

    def loghtml(self, html):
        self.f.write(html.encode())

def get_logger(file):
    if not hasattr(get_logger, 'loggers'):
        get_logger.loggers = {}
    loggers = get_logger.loggers
    if file in loggers:
        return loggers[file]
    else:
        logger = RichLogger(file, True)
        loggers[file] = logger
        return logger
