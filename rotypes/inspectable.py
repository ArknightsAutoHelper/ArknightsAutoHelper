import sys

# we need Python 3.4+ for __del__ to work with circular references
assert sys.hexversion >= 0x03090000

from .idldsl import define_winrt_com_method, funcwrap, _new_rtobj
from .winstring import HSTRING
from .types import *

CoTaskMemFree = windll.ole32.CoTaskMemFree
CoTaskMemFree.argtypes = (c_void_p,)

# unknwn
@GUID('00000000-0000-0000-C000-000000000046')
class IUnknown(c_void_p):
    _method_defs = [
        (0, 'QueryInterface', WINFUNCTYPE(check_hresult, REFGUID, VOIDPP)(0, "QueryInterface")),
        (1, 'AddRef', WINFUNCTYPE(ULONG)(1, "AddRef")),
        (2, 'Release', WINFUNCTYPE(ULONG)(2, "Release"))
    ]
    QueryInterface = funcwrap(_method_defs[0][2])
    _AddRef = funcwrap(_method_defs[1][2])
    _Release = funcwrap(_method_defs[2][2])
    _vtblend = 2

    def _detach(self):
        newptr = cast(self, c_void_p)
        self.value = None
        return newptr

    def Release(self):
        if self.value is not None:
            self._Release()
            self.value = None

    def __del__(self):
        self.Release()

    def astype(self, interface_type):
        iid = interface_type.GUID
        obj = _new_rtobj(interface_type)
        self.QueryInterface(byref(iid), byref(obj))
        return obj

    def __init_subclass__(cls):
        cls._method_defs = []


# inspectable
class TrustLevel:
    _enum_type_ = INT
    BaseTrust = 0
    PartialTrust = 1
    FullTrust = 2

@GUID('AF86E2E0-B12D-4c6a-9C5A-D7AA65101E90')
class IInspectable(IUnknown):
    def __class_getitem__(cls, name):
        return cls
    def __init_subclass__(cls, requires=()):
        super().__init_subclass__()

    def GetIids(self):
        size = ULONG()
        ptr = REFGUID()
        self._GetIids(byref(size), byref(ptr))
        result = [GUID(str(ptr[i])) for i in range(size.value)]
        CoTaskMemFree(ptr)
        return result



define_winrt_com_method(IInspectable, '_GetIids', POINTER(ULONG), POINTER(REFGUID), vtbl=3)
define_winrt_com_method(IInspectable, 'GetRuntimeClassName', retval=HSTRING, vtbl=4)
define_winrt_com_method(IInspectable, 'GetTrustLevel', retval=TrustLevel._enum_type_, vtbl=5)


# activation
@GUID('00000035-0000-0000-c000-000000000046')
class IActivationFactory(IInspectable):
    pass


define_winrt_com_method(IActivationFactory, 'ActivateInstance', retval=IInspectable, vtbl=6)
