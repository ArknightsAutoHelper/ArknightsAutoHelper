import os
import sys
import tty
import termios
import select

def getch_timeout(timeout):
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        r, w, x = select.select([fd], [], [], timeout)
        if r:
            ch = os.read(fd, 1)
            if ch == b'\x03':
                os.kill(os.getpid(), 2)  # SIGINT
            return ch
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def isatty(io):
    return io.isatty()


def check_control_code():
    if 'TERM' in os.environ and os.environ['TERM'] != 'dumb':
        return sys.stdout.isatty()


__all__ = ['getch_timeout', 'isatty', 'check_control_code']
