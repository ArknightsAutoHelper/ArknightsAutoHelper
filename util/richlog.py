import os
from base64 import b64encode
from functools import lru_cache
from io import BytesIO
import threading
from queue import Queue
from typing import BinaryIO
from html import escape
import atexit
import cv2
from util import cvimage

class _richlog_worker(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()
        self.lock = threading.Lock()
        self.files = {}
        self.daemon = True

    def open(self, filename, overwrite=False) -> bool:
        if filename not in self.files:
            with self.lock:
                if filename not in self.files:
                    f = open(filename, 'wb' if overwrite else 'ab')
                    if f.tell() == 0:
                        f.write(b'<html><head><meta charset="utf-8"></head><body>')
                    self.files[filename] = f
                    return True
        return False

    def run(self):
        while (record := self.queue.get()) is not None:
            try:
                file, overwrite, msgtype, msg = record
                self.open(file, overwrite)
                io: BinaryIO = self.files[file]
                if msgtype == 'html':
                    if isinstance(msg, str):
                        msg = msg.encode('utf-8')
                    io.write(msg)
                elif msgtype == 'text':
                    io.write(b'<pre>%s</pre>\n' % escape(msg).encode('utf-8'))
                elif msgtype == 'image':
                    from PIL import Image as PILImage
                    im: PILImage.Image = msg
                    io.write(b'<p><img src="data:image/webp;base64,')
                    bio = BytesIO()
                    im.save(bio, 'webp', lossless=True, quality=0, method=0)
                    io.write(b64encode(bio.getbuffer()))
                    io.write(b'"></p>\n')
                io.flush()
                self.queue.task_done()
            except Exception as e:
                import traceback
                traceback.print_exc()
                pass
        self.queue.task_done()

    def close(self):
        self.queue.put(None)
        self.queue.join()
        for f in self.files.values():
            f.close()

    def loghtml(self, file, overwrite, html):
        self.queue.put((file, overwrite, 'html', html))

    def logtext(self, file, overwrite, text):
        self.queue.put((file, overwrite, 'text', text))

    def logimage(self, file, overwrite, im: cvimage.Image):
        if im is None:
            return
        pil_im = im.to_pil(always_copy=True)  # PIL Image.save is much more usable than OpenCV imwrite/imencode
        self.queue.put((file, overwrite, 'image', pil_im))
        
_worker = _richlog_worker()
_lock = threading.Lock()
def _ensure_worker():
    if _worker.is_alive():
        return
    with _lock:
        if not _worker.is_alive():
            _worker.start()
            atexit.register(_worker.close)


class RichLogger:
    def __init__(self, file, overwrite=False):
        self.filename = file
        self.overwrite = overwrite

    def logimage(self, image: cvimage.Image):
        _ensure_worker()
        _worker.logimage(self.filename, self.overwrite, image)

    def logfig(self, fig):
        # matplotlib figure
        buf = BytesIO()
        fig.savefig(buf, format='svg')
        _ensure_worker()
        _worker.loghtml(self.filename, self.overwrite, buf.getvalue())

    def logtext(self, text):
        _ensure_worker()
        _worker.logtext(self.filename, self.overwrite, str(text))

    def loghtml(self, html):
        _ensure_worker()
        _worker.loghtml(self.filename, self.overwrite, html)


@lru_cache(maxsize=None)
def get_logger(module):
    import app
    if app.get_instance_id() == 0:
        filename = '%s.html' % module
    else:
        filename = '%s.%d.html' % (module, app.get_instance_id())
    logger = RichLogger(app.logs.joinpath(filename), True)
    return logger
