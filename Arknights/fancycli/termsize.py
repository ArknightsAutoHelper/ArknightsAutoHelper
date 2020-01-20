#!/usr/bin/env python
import os
import shlex
import struct
import platform
import subprocess


def get_terminal_size():
    """ getTerminalSize()
     - get width and height of console
     - works on linux,os x,windows,cygwin(windows)
     originally retrieved from:
     http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    """
    tuple_xy = None
    try:
        s = os.get_terminal_size()
        tuple_xy = (s.columns, s.lines)
    except OSError:
        pass
    if tuple_xy is None:
        # needed for window's python in cygwin's xterm!
        tuple_xy = _get_terminal_size_tput()
    if tuple_xy is None:
        tuple_xy = (80, 25)  # default value
    return tuple_xy


def _get_terminal_size_tput():
    # get terminal width
    # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
        cols = int(subprocess.check_call(shlex.split('tput cols')))
        rows = int(subprocess.check_call(shlex.split('tput lines')))
        return (cols, rows)
    except:
        pass

if __name__ == "__main__":
    sizex, sizey = get_terminal_size()
    print(sizex, sizey)
