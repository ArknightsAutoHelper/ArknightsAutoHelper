import asyncio
import signal
import threading
from rpc.aioobservable import Subject
import util.early_logs
import util.unfuck_https_proxy

import logging

import app
app.background = True

interrupt_signal = Subject()

class PendingHandler(logging.Handler):
    terminator = '\n'

    def __init__(self):
        super().__init__()
        self.records = []
        self.output = None

    def attach(self, output: logging.Handler):
        self.output = output
        for record in self.records:
            self.output.emit(record)
        self.records.clear()

    def flush(self):
        if self.output is not None:
            self.output.flush()

    def emit(self, record: logging.LogRecord):
        if self.output is None:
            self.records.append(record)
        else:
            self.output.emit(record)

class AsyncWebHandler(logging.Handler):
    terminator = '\n'

    def __init__(self, outq: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.outq = outq
        self.loop = loop

    def flush(self):
        pass

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            asyncio.run_coroutine_threadsafe(self.outq.put(dict(type="log", message=msg, level=level)), self.loop)
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)

loghandler = PendingHandler()
loghandler.setLevel(logging.INFO)
app.init([loghandler])

class WebFrontend:
    def __init__(self, output: Subject[dict], interrupt_signal: Subject, skip_signal: Subject, loop: asyncio.AbstractEventLoop):
        self.output = output
        self.loop = loop
        self.interrupt_signal = interrupt_signal
        self.interrupt_event = threading.Event()
        self.skip_signal = skip_signal
        self.skip_event = threading.Event()

    def attach(self, helper):
        pass
    def alert(self, title, text, level='info', details=None):
        """user-targeted message"""
        self.output.next(dict(type="alert", title=title, message=text, level=level, details=details))
    def notify(self, name, value=None):
        """program-targeted message"""
        # logger.info("sending notify %s %r", name, value)
        self.output.next(dict(type="notify", name=name, value=value))
    def request_device_connector(self):
        try:
            return connector.auto_connect()
        except:
            self.notify_availiable_devices()
            self.notify('web:request-device')
            raise RuntimeError('请选择设备后重试')
    def notify_availiable_devices(self):
        devices = connector.enum_devices()
        self.devices = devices
        self.notify("web:availiable-devices", [x[0] for x in devices])

    def delay(self, secs, allow_skip):
        self.notify("wait", dict(duration=secs, allow_skip=allow_skip))
        intr_sub = self.interrupt_signal.subscribe(lambda x: self.interrupt_event.set)
        skip_sub = self.interrupt_signal.subscribe(lambda x: self.skip_event.set)
        try:
            if not allow_skip:
                self.interrupt_event.wait(secs)
            else:
                if self.interrupt_event.is_set():
                    raise KeyboardInterrupt()
                self.skip_wait_event.clear()
                self.skip_wait_event.wait(secs)
            if self.interrupt_event.is_set():
                raise KeyboardInterrupt()
        finally:
            self.notify("wait", dict(duration=0, allow_skip=False))


def run():
    signal.signal(signal.SIGINT, lambda *args: interrupt_signal.next(None))
    from Arknights.helper import ArknightsHelper
    helper = ArknightsHelper()