from ctypes import *
from ctypes.wintypes import *

VOIDPP = POINTER(c_void_p)

S_OK = 0
S_FALSE = 1

E_FAIL = -2147467259  # 0x80004005L
E_NOTIMPL = -2147467263  # 0x80004001L
E_NOINTERFACE = -2147467262  # 0x80004002L
E_BOUNDS = -2147483637  # 0x8000000BL


def check_hresult(hr):
    # print('HRESULT = 0x%08X' % (hr & 0xFFFFFFFF))
    if (hr & 0x80000000) != 0:
        if hr == E_NOTIMPL:
            raise NotImplementedError
        elif hr == E_NOINTERFACE:
            raise TypeError("E_NOINTERFACE")
        elif hr == E_BOUNDS:
            raise IndexError  # for old style iterator protocol
        e = OSError("[HRESULT 0x%08X] %s" % (hr & 0xFFFFFFFF, FormatError(hr)))
        e.winerror = hr & 0xFFFFFFFF
        raise e
    return hr


class GUID(Structure):
    _fields_ = [("Data1", DWORD),
                ("Data2", WORD),
                ("Data3", WORD),
                ("Data4", c_uint8 * 8)]

    def __init__(self, *initwith):
        if len(initwith) == 1 and isinstance(initwith[0], str):
            strrepr = initwith[0]
            if strrepr.startswith('{'):
                strrepr = strrepr[1:-1]
            part1, part2, part3, part4, part5 = strrepr.split('-', 5)
            self.Data1 = int(part1, 16)
            self.Data2 = int(part2, 16)
            self.Data3 = int(part3, 16)
            self.Data4 = (int(part4[0:2], 16), int(part4[2:4], 16),
                          int(part5[0:2], 16), int(part5[2:4], 16), int(part5[4:6], 16), int(part5[6:8], 16),
                          int(part5[8:10], 16), int(part5[10:12], 16))
        elif len(initwith) == 4:
            self.Data1, self.Data2, self.Data3, self.Data4 = initwith
        elif len(initwith) == 11:
            self.Data1, self.Data2, self.Data3, self.Data4 = (*initwith[0:3], initwith[3:])
        else:
            raise ArgumentError(len(initwith))

    def __str__(self):
        return '%08x-%04x-%04x-%02x%02x-%02x%02x%02x%02x%02x%02x' % (
        self.Data1, self.Data2, self.Data3, *list(self.Data4))

    def __repr__(self):
        return 'GUID(%s)' % repr(str(self))

    def __eq__(self, other):
        return isinstance(other, GUID) and bytes(self) == bytes(other)

    def __hash__(self):
        # We make GUID instances hashable, although they are mutable.
        return hash(bytes(self))

    def __call__(self, victim):
        '''for use as class decorator'''
        victim.GUID = self
        return victim

REFGUID = POINTER(GUID)
