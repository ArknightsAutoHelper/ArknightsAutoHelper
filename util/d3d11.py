import ctypes
import ctypes.wintypes
from rotypes import IUnknown
from rotypes import idldsl

D3D11_SDK_VERSION = 7
D3D_DRIVER_TYPE_HARDWARE = 1
D3D11_CREATE_DEVICE_BGRA_SUPPORT = 0x20
D3D11_USAGE_STAGING = 3
D3D11_CPU_ACCESS_READ = 0x20000
D3D11_MAP_READ = 1
DXGI_ERROR_DEVICE_REMOVED = 0x887A0005
DXGI_ERROR_DEVICE_RESET = 0x887A0007

class DXGI_SAMPLE_DESC(ctypes.Structure):
    _fields_ = [
        ('Count', ctypes.wintypes.UINT),
        ('Quality', ctypes.wintypes.UINT)
    ]

class D3D11_TEXTURE2D_DESC(ctypes.Structure):
    _fields_ = [
        ('Width', ctypes.wintypes.UINT),
        ('Height', ctypes.wintypes.UINT),
        ('MipLevels', ctypes.wintypes.UINT),
        ('ArraySize', ctypes.wintypes.UINT),
        ('Format', ctypes.wintypes.UINT),
        ('SampleDesc', DXGI_SAMPLE_DESC),
        ('Usage', ctypes.wintypes.UINT),
        ('BindFlags', ctypes.wintypes.UINT),
        ('CPUAccessFlags', ctypes.wintypes.UINT),
        ('MiscFlags', ctypes.wintypes.UINT),
    ]

class D3D11_MAPPED_SUBRESOURCE(ctypes.Structure):
    _fields_ = [
        ('pData', ctypes.c_void_p),
        ('RowPitch', ctypes.wintypes.UINT),
        ('DepthPitch', ctypes.wintypes.UINT)
    ]

@idldsl.GUID('db6f6ddb-ac77-4e88-8253-819df9bbf140')
class ID3D11Device(IUnknown):
    pass

@idldsl.GUID('6f15aaf2-d208-4e89-9ab4-489535d34f9c')
class ID3D11Texture2D(IUnknown):
    pass

@idldsl.GUID('c0bfa96c-e089-44fb-8eaf-26f8796190da')
class ID3D11DeviceContext(IUnknown):
    pass


idldsl.define_winrt_com_method(ID3D11Device, 'CreateTexture2D', ctypes.POINTER(D3D11_TEXTURE2D_DESC), ctypes.c_void_p, retval=ID3D11Texture2D, vtbl=5)
idldsl.define_winrt_com_method(ID3D11Device, 'GetImmediateContext', retval=ID3D11DeviceContext, vtbl=40)
# idldsl.define_winrt_com_method(ID3D11Texture2D, 'GetDevice', retval=ID3D11Texture2D, vtbl=3)
idldsl.define_winrt_com_method(ID3D11Texture2D, 'GetDesc', retval=D3D11_TEXTURE2D_DESC, vtbl=10)
idldsl.define_winrt_com_method(ID3D11DeviceContext , 'Map', IUnknown, ctypes.c_uint, ctypes.c_int, ctypes.c_uint, retval=D3D11_MAPPED_SUBRESOURCE, vtbl=14)
idldsl.define_winrt_com_method(ID3D11DeviceContext , 'Unmap', IUnknown, ctypes.c_uint, vtbl=15)
idldsl.define_winrt_com_method(ID3D11DeviceContext , 'CopyResource', IUnknown, IUnknown, vtbl=47)

D3D11CreateDevice = ctypes.oledll.d3d11.D3D11CreateDevice
D3D11CreateDevice.argtypes = (IUnknown, ctypes.c_int, ctypes.c_void_p, ctypes.wintypes.UINT, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ID3D11Device, ctypes.c_void_p, ID3D11DeviceContext)