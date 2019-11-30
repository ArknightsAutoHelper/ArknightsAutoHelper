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
    RoGetActivationFactory(HSTRING(classname), GUID(interface.IID), byref(insp))
    return insp


RoInitialize(RO_INIT_TYPE.RO_INIT_MULTITHREADED)
