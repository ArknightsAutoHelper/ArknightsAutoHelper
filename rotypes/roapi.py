from functools import lru_cache

from .inspectable import IInspectable, IActivationFactory
from .types import *
from .winstring import HSTRING

combase = windll.LoadLibrary('combase.dll')
RoGetActivationFactory = combase.RoGetActivationFactory
RoGetActivationFactory.argtypes = (HSTRING, REFGUID, POINTER(IInspectable))
RoGetActivationFactory.restype = check_hresult


class RO_INIT_TYPE(INT):
    RO_INIT_SINGLETHREADED = 0
    RO_INIT_MULTITHREADED = 1


RoInitialize = combase.RoInitialize
RoInitialize.argtypes = (RO_INIT_TYPE,)
RoInitialize.restype = check_hresult


@lru_cache()
def GetActivationFactory(classname, interface=IActivationFactory):
    insp = interface()
    RoGetActivationFactory(classname, interface.GUID, byref(insp))
    return insp

def _ro_init():
    import sys
    coinit_flags = getattr(sys, 'coinit_flags', 2)
    if coinit_flags & 2:
        RoInitialize(RO_INIT_TYPE.RO_INIT_SINGLETHREADED)
    else:
        RoInitialize(RO_INIT_TYPE.RO_INIT_MULTITHREADED)

# _ro_init()
