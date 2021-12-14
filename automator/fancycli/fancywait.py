import sys
import os
import time
import logging

from .platform import isatty, check_control_code, getch_timeout
from .termop import TermOp

logger = logging.getLogger('fancywait')

stdinfd = sys.stdout.buffer
stdinfd = getattr(stdinfd, 'raw', stdinfd)

has_tty_input = isatty(stdinfd)


class StatusLineBase:
    def update(self, text):
        pass

    def cleanup(self):
        pass

    def startup(self):
        pass

    def shutdown(self):
        pass

    def __enter__(self):
        self.startup()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


class StatusLineFancy(StatusLineBase):
    def __init__(self, io):
        self.op = TermOp(stdinfd)
        self.io = io

    def update(self, text):
        with self.op.keep_cursor():
            self.io.write(("\r\033[0m\033[K%s\033[0m\033[K\r" % text).encode('utf-8'))

    def cleanup(self):
        self.io.write(b'\033[0m\033[2K')
        self.io.flush()

class StatusLineLegacy(StatusLineBase):
    def __init__(self, io):
        self.io = io

    def update(self, text):
        self.io.write(("\r%s\r" % text).encode('utf-8'))

    def cleanup(self):
        self.io.write(b"\r\n")
        self.io.flush()


class StatusLineDummy(StatusLineBase):
    def __init__(self, io):
        pass


class KeyHandler:
    def __init__(self, label, ch, callback):
        self.label = label
        self.ch = ch
        self.callback = callback


if has_tty_input and check_control_code():
    logger.debug('has tty input and control code')
    StatusLine = StatusLineFancy
elif has_tty_input and stdinfd.isatty():
    logger.debug('has tty input and legacy conhost')
    StatusLine = StatusLineLegacy
else:
    logger.debug('no tty input')
    StatusLine = StatusLineDummy

if has_tty_input:
    def fancy_delay(timeout, status=None, key_handlers=None):
        t0 = time.monotonic()
        timeout0 = timeout
        check_control_code()
        if status is None:
            status = StatusLine(stdinfd)

        if key_handlers is None:
            key_handlers = ()

        try:
            waittime = 1
            while True:
                elapsed = time.monotonic() - t0
                if elapsed > timeout0:
                    return
                text = "[WAIT] %d/%d\t  " % (elapsed, timeout0)
                labels = '  '.join(x.label for x in key_handlers if x.label is not None)
                text += labels
                chs = {x.ch: x for x in key_handlers if x.label is not None}
                status.update(text)
                ch = getch_timeout(min(waittime, timeout))
                if ch is not None and ch in chs:
                    handler = chs[ch]
                    try:
                        handler.callback(handler)
                    except StopIteration:
                        break
                elapsed = time.monotonic() - t0
                timeout = timeout0 - elapsed
                if ch is None:
                    waittime = 1
                else:
                    waittime = 1 - (elapsed % 1)
        finally:
            status.cleanup()
else:
    def fancy_delay(timeout, *args, **kwargs):
        return time.sleep(timeout)


def main():
    # enable_escape_code()
    with StatusLine(stdinfd) as statusline:
        def enter(handler):
            raise StopIteration()
        def toggle(handler):
            toggle.status = not toggle.status
            onoff = 'ON' if toggle.status else 'OFF'
            handler.label = '<r>切换自动补充理智(%s)' % onoff
        toggle.status = True
        enterhandler = KeyHandler('<ENTER>跳过', b'\r', enter)
        togglehandler = KeyHandler('<r>切换自动补充理智(ON)', b'r', toggle)
        dummyskip = KeyHandler('           ', b'', lambda _: None)
        print('hello')
        time.sleep(2)
        print('world1')
        print('world2')
        print('world3')
        print('world3')
        print('world3')
        print('world3')
        t = time.monotonic()
        fancy_delay(20, statusline, [enterhandler, togglehandler])
        print(time.monotonic() - t)
        time.sleep(1)
        fancy_delay(3, statusline, [dummyskip, togglehandler])
        print('world3')
        print('world3')
        print('world3')
        print('fuck')


if __name__ == '__main__':
    main()
