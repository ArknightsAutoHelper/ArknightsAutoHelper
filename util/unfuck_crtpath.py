import sys
import os
import ctypes
import contextlib

if sys.platform == 'win32':
    def find_crt() -> list[ctypes.CDLL]:
        GetModuleHandle = ctypes.windll.kernel32.GetModuleHandleW
        GetModuleHandle.restype = ctypes.c_void_p
        crtlist = [
            'ucrtbase',
            'msvcr120',
            'msvcr110',
            'msvcr100',
            'msvcr90',
            'msvcr80',
            # 'msvcrt'  # msvcrt does not support UTF-8
        ]
        result = []
        for crt in crtlist:
            if hmod := GetModuleHandle(crt):
                lib = ctypes.CDLL(crt, handle=hmod)
                lib.setlocale.restype = ctypes.c_char_p
                result.append(lib)
        return result

    class crt_use_utf8:
        LC_ALL = 0
        _ENABLE_PER_THREAD_LOCALE = 0x0001
        GetModuleHandle = ctypes.windll.kernel32.GetModuleHandleW
        GetModuleHandle.restype = ctypes.c_void_p
        crtlist = [
            'ucrtbase',
            'msvcr120',
            'msvcr110',
            'msvcr100',
            'msvcr90',
            'msvcr80',
            # 'msvcrt'  # msvcrt does not support UTF-8
        ]
        def __init__(self, crts: list[ctypes.CDLL] = None):
            if crts is None:
                crts = find_crt()
            self.crts = crts
            self.saved_locale = [None for _ in self.crts]
            

        def __enter__(self):
            for i, libc in enumerate(self.crts):
                old_threadlocale = libc._configthreadlocale(self._ENABLE_PER_THREAD_LOCALE)
                old_locale = libc.setlocale(self.LC_ALL, b'.65001')
                self.saved_locale[i] = (old_threadlocale, old_locale)
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            for i, libc in enumerate(self.crts):
                old_threadlocale, old_locale = self.saved_locale[i]
                libc._configthreadlocale(old_threadlocale)
                if old_locale is not None:
                    libc.setlocale(self.LC_ALL, old_locale)

    def query_short_path(path: os.PathLike) -> str:
        path = os.fspath(path)
        length = ctypes.windll.kernel32.GetShortPathNameW(path, None, 0)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.kernel32.GetShortPathNameW(path, buf, length+1)
        return buf.value

    def encode_mbcs_path(path: os.PathLike) -> bytes:
        """Try to encode path in CP_ACP. Use 8.3 names if necessary."""
        path = os.fspath(path)
        try:
            bpath = path.encode('mbcs')
            return bpath
        except UnicodeEncodeError:
            pass  # avoid nested exception
        # try 8.3 name
        return query_short_path(path).encode('mbcs')

else:
    def find_crt():
        return []
    crt_use_utf8 = contextlib.nullcontext
    query_short_path = os.fspath
    encode_mbcs_path = os.fsencode
