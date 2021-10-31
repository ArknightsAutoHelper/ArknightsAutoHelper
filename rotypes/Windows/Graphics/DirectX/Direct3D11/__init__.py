import ctypes
import rotypes
import rotypes.idldsl
import rotypes.Windows.Foundation
from rotypes.types import REFGUID

@rotypes.idldsl.GUID('A37624AB-8D5F-4650-9D3E-9EAE3D9BC670')
class _IDirect3DDevice(rotypes.IInspectable):
    pass

class IDirect3DDevice(_IDirect3DDevice, rotypes.Windows.Foundation.IClosable):
    pass

@rotypes.idldsl.GUID('0BF4A146-13C1-4694-BEE3-7ABF15EAF586')
class _IDirect3DSurface(rotypes.IInspectable):
    pass

class IDirect3DSurface(_IDirect3DSurface, rotypes.Windows.Foundation.IClosable):
    pass

@rotypes.idldsl.GUID('A9B3D012-3DF2-4EE3-B8D1-8695F457D3C1')
class IDirect3DDxgiInterfaceAccess(rotypes.IUnknown):
    pass

rotypes.idldsl.define_winrt_com_method(IDirect3DDxgiInterfaceAccess, 'GetInterface', REFGUID, retval=rotypes.IUnknown)

_CreateDirect3D11DeviceFromDXGIDevice = ctypes.oledll.d3d11.CreateDirect3D11DeviceFromDXGIDevice
_CreateDirect3D11DeviceFromDXGIDevice.argtypes = (rotypes.IUnknown, ctypes.POINTER(rotypes.IInspectable))

def CreateDirect3D11DeviceFromDXGIDevice(dxgidev):
    outptr = rotypes.IInspectable()
    _CreateDirect3D11DeviceFromDXGIDevice(dxgidev, ctypes.byref(outptr))
    return outptr
