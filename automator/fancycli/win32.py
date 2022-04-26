import ctypes
from functools import lru_cache
import msvcrt
import os
import struct
import sys
import time
import logging

logger = logging.getLogger(__name__)

k32 = ctypes.windll.kernel32
STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -12
GetStdHandle = k32.GetStdHandle
WaitForSingleObject = k32.WaitForSingleObject
WAIT_TIMEOUT = 0x00000102
WAIT_OBJECT_0 = 0x00000000
GetFileInformationByHandleEx = k32.GetFileInformationByHandleEx
FileNameInfo = 2
GetConsoleMode = k32.GetConsoleMode
SetConsoleMode = k32.SetConsoleMode
ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
DISABLE_NEWLINE_AUTO_RETURN = 0x0008
GetModuleHandle = k32.GetModuleHandleW
FlushConsoleInputBuffer = k32.FlushConsoleInputBuffer
GetFileType = k32.GetFileType
FILE_TYPE_CHAR = 0x0002
RtlGetVersion = ctypes.windll.ntdll.RtlGetVersion

class OSVERSIONINFOW(ctypes.Structure):
    _fields_ = [
        ('dwOSVersionInfoSize', ctypes.c_ulong),
        ('dwMajorVersion', ctypes.c_ulong),
        ('dwMinorVersion', ctypes.c_ulong),
        ('dwBuildNumber', ctypes.c_ulong),
        ('dwPlatformId', ctypes.c_ulong),
        ('szCSDVersion', ctypes.c_wchar * 128),
    ]


@lru_cache(1)
def _build_number():
    info = OSVERSIONINFOW(dwOSVersionInfoSize=ctypes.sizeof(OSVERSIONINFOW))
    RtlGetVersion(ctypes.byref(info))
    return info.dwBuildNumber

def getch_timeout(timeout):
    hstdin = GetStdHandle(STD_INPUT_HANDLE)
    timeout0 = timeout
    t0 = time.monotonic()
    while True:
        res = WaitForSingleObject(hstdin, int(timeout * 1000))
        if res == WAIT_TIMEOUT:
            return None
        elif res == WAIT_OBJECT_0:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                if ch == b'\x00' or ch == b'\xe0':
                    ch = msvcrt.getch()
                return ch
            else:
                FlushConsoleInputBuffer(hstdin)
        else:
            raise OSError()
        t1 = time.monotonic()
        t = t1 - t0
        timeout = timeout0 - t
        if timeout < 0:
            return None


# there is no clean way to control cygwin pty from win32 process without spawning a cygwin process
# therefore we can't implement getch() in cygwin pty from a win32 process
# however msvcrt isatty says true for cygwin pty pipes so we need to examine the pipe names

def is_cygwin_pty(io):
    if hasattr(io, 'raw'):
        io = io.raw
    if not hasattr(io, 'fileno'):
        return False
    fd = io.fileno()
    try:
        handle = msvcrt.get_osfhandle(fd)
    except OSError:
        return False
    buf = ctypes.create_string_buffer(65540)
    if GetFileInformationByHandleEx(handle, FileNameInfo, buf, 65540):
        length = struct.unpack_from('I', buf, 0)[0]
        s = buf[4:4 + length].decode('utf-16-le')
        return 'cygwin-' in s and '-pty' in s
    return False


def isatty(io):
    # MSVC isatty returns nonzero for cygwin/msys2 pty named pipes, but we can't use WaitForMultipleObjects on pipes
    if not hasattr(io, 'fileno'):
        return False
    try:
        handle = msvcrt.get_osfhandle(io.fileno())
    except OSError:
        return False
    # outmode = ctypes.c_uint32()
    # return bool(GetConsoleMode(handle, ctypes.byref(outmode)))
    # return io.isatty() and (not is_cygwin_pty(io))
    return GetFileType(handle) == FILE_TYPE_CHAR


def check_control_code():
    if not isatty(sys.stdout):
        return False

    hout = GetStdHandle(STD_OUTPUT_HANDLE)
    outmode = ctypes.c_uint32()
    try:
        if _build_number() >= 14393:
            logger.debug('using Windows ENABLE_VIRTUAL_TERMINAL_PROCESSING')
            if not GetConsoleMode(hout, ctypes.byref(outmode)):
                return False
            if not SetConsoleMode(hout, outmode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING):
                return False
            GetConsoleMode(hout, ctypes.byref(outmode))
            SetConsoleMode(hout, outmode.value | DISABLE_NEWLINE_AUTO_RETURN)
            # if isatty(sys.stdin):
            #     import atexit
            #     hin = GetStdHandle(STD_INPUT_HANDLE)
            #     GetConsoleMode(hin, ctypes.byref(outmode))
            #     SetConsoleMode(hin, outmode.value | ENABLE_VIRTUAL_TERMINAL_INPUT)
            #     oldmode = outmode.value
            #     def fini():
            #         SetConsoleMode(hin, oldmode)
            #     atexit.register(fini)
            return True

        else:
            if not GetConsoleMode(hout, ctypes.byref(outmode)):
                return False
            # check for ansicon/ConEmu hook dlls
            hooked = bool(GetModuleHandle('ansi32.dll') or GetModuleHandle('ansi64.dll') or GetModuleHandle(
                'conemuhk64.dll') or GetModuleHandle('conemuhk.dll'))
            if hooked:
                logger.debug('using ansicon/conemu hook')
            else:
                logger.debug('using colorama as fallback')
                import colorama
                colorama.init()  # for basic color output
            return hooked
    finally:
        logger.setLevel(logging.ERROR)


__all__ = ['getch_timeout', 'isatty', 'check_control_code']
