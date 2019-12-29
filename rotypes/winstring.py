import ctypes

from .types import check_hresult

combase = ctypes.windll.LoadLibrary("combase.dll")
WindowsCreateString = combase.WindowsCreateString
WindowsCreateString.argtypes = (ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p))
WindowsCreateString.restype = check_hresult

WindowsDeleteString = combase.WindowsDeleteString
WindowsDeleteString.argtypes = (ctypes.c_void_p,)
WindowsDeleteString.restype = check_hresult

WindowsGetStringRawBuffer = combase.WindowsGetStringRawBuffer
WindowsGetStringRawBuffer.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32))
WindowsGetStringRawBuffer.restype = ctypes.c_void_p


class HSTRING(ctypes.c_void_p):
    def __init__(self, s=None):
        super().__init__()
        if s is None or len(s) == 0:
            self.value = None
            return
        u16str = s.encode("utf-16-le") + b"\x00\x00"
        u16len = (len(u16str) // 2) - 1
        WindowsCreateString(u16str, ctypes.c_uint32(u16len), ctypes.byref(self))

    def __str__(self):
        if self.value is None:
            return ""
        length = ctypes.c_uint32()
        ptr = WindowsGetStringRawBuffer(self, ctypes.byref(length))
        return ctypes.wstring_at(ptr, length.value)

    def __del__(self):
        if self.value is None:
            return
        WindowsDeleteString(self)

    def __repr__(self):
        return "HSTRING(%s)" % repr(str(self))
