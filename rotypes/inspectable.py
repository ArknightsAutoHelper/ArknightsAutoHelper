import sys

# we need Python 3.4+ for __del__ to work with circular references
assert sys.hexversion >= 0x03040000

from .idldsl import define_winrt_com_method, funcwrap, _new_rtobj
from .winstring import HSTRING
from .types import *


# unknwn
class IUnknown(c_void_p):
    IID = '00000000-0000-0000-C000-000000000046'
    QueryInterface = funcwrap(WINFUNCTYPE(check_hresult, REFGUID, VOIDPP)(0, "QueryInterface"))
    AddRef = funcwrap(WINFUNCTYPE(ULONG)(1, "AddRef"))
    Release = funcwrap(WINFUNCTYPE(ULONG)(2, "Release"))
    _vtblend = 2
    _own_object = True

    def _detach(self):
        newptr = cast(self, c_void_p)
        self.value = None
        return newptr

    def __del__(self):
        if self._own_object and self.value is not None:
            # print('IUnknown_Release', self.value)
            self.Release()

    def astype(self, interface_type):
        iid = GUID(interface_type.IID)
        obj = _new_rtobj(interface_type)
        self.QueryInterface(byref(iid), byref(obj))
        return obj


# inspectable
class TrustLevel:
    _enum_type_ = INT
    BaseTrust = 0
    PartialTrust = 1
    FullTrust = 2


class IInspectable(IUnknown):
    IID = 'AF86E2E0-B12D-4c6a-9C5A-D7AA65101E90'


define_winrt_com_method(IInspectable, 'GetIids', POINTER(ULONG), POINTER(REFGUID), vtbl=3)
define_winrt_com_method(IInspectable, 'GetRuntimeClassName', retval=HSTRING, vtbl=4)
define_winrt_com_method(IInspectable, 'GetTrustLevel', retval=TrustLevel._enum_type_, vtbl=5)


# activation
class IActivationFactory(IInspectable):
    IID = '00000035-0000-0000-c000-000000000046'


define_winrt_com_method(IActivationFactory, 'ActivateInstance', retval=IInspectable, vtbl=6)
