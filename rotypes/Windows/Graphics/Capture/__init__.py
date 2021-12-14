from ctypes import c_bool, c_int, c_int32, c_int64, c_void_p
from ctypes.wintypes import HWND, HMONITOR
from rotypes.Windows.Foundation import IClosable, TypedEventHandler

from rotypes.inspectable import IInspectable, IUnknown
from rotypes.idldsl import define_winrt_com_method, _static_method, runtimeclass, GUID, runtimeclass_add_statics
from rotypes.types import REFGUID
from rotypes.winstring import HSTRING
from rotypes.Windows.Graphics import SizeInt32
from rotypes.Windows.Graphics.DirectX import DirectXPixelFormat
@GUID('FA50C623-38DA-4B32-ACF3-FA9734AD800E')
class IDirect3D11CaptureFrame(IInspectable):
    pass


@GUID('24EB6D22-1975-422E-82E7-780DBD8DDF24')
class IDirect3D11CaptureFramePool(IInspectable):
    pass


@GUID('589B103F-6BBC-5DF5-A991-02E28B3B66D5')
class IDirect3D11CaptureFramePoolStatics2(IInspectable):
    pass

@GUID('79C3F95B-31F7-4EC2-A464-632EF5D30760')
class IGraphicsCaptureItem(IInspectable):
    pass

@GUID('814E42A9-F70F-4AD7-939B-FDDCC6EB880D')
class IGraphicsCaptureSession(IInspectable):
    pass

@GUID('2C39AE40-7D2E-5044-804E-8B6799D4CF9E')
class IGraphicsCaptureSession2(IInspectable):
    pass

@GUID('3628E81B-3CAC-4C60-B7F4-23CE0E0C3356')
class IGraphicsCaptureItemInterop(IUnknown):
    pass

class Direct3D11CaptureFrame(runtimeclass, IDirect3D11CaptureFrame, IClosable):
    pass

class Direct3D11CaptureFramePool(runtimeclass, IDirect3D11CaptureFramePool, IClosable):
    pass

class GraphicsCaptureItem(runtimeclass, IGraphicsCaptureItem):
    pass

class GraphicsCaptureSession(runtimeclass, IGraphicsCaptureSession, IGraphicsCaptureSession2, IClosable):
    pass

define_winrt_com_method(IDirect3D11CaptureFrame, 'get_Surface', propget=IInspectable)
define_winrt_com_method(IDirect3D11CaptureFrame, 'get_SystemRelativeTime', propget=c_int64) #FIXME: Windows.Foundation.TimeSpan
define_winrt_com_method(IDirect3D11CaptureFrame, 'get_ContentSize', propget=SizeInt32)

define_winrt_com_method(IDirect3D11CaptureFramePool, 'Recreate', IInspectable['Windows.Graphics.DirectX.Direct3D11.IDirect3DDevice'], DirectXPixelFormat, c_int32, SizeInt32) #FIXME: Windows.Graphics.DirectX.DirectXPixelFormat
define_winrt_com_method(IDirect3D11CaptureFramePool, 'TryGetNextFrame', retval=Direct3D11CaptureFrame)
define_winrt_com_method(IDirect3D11CaptureFramePool, 'add_FrameArrived', TypedEventHandler(Direct3D11CaptureFramePool, IInspectable), retval=c_int64)
define_winrt_com_method(IDirect3D11CaptureFramePool, 'remove_FrameArrived', c_int64)
define_winrt_com_method(IDirect3D11CaptureFramePool, 'CreateCaptureSession', GraphicsCaptureItem, retval=GraphicsCaptureSession)
define_winrt_com_method(IDirect3D11CaptureFramePool, 'get_DispatcherQueue', propget=IInspectable['Windows.System.DispatcherQueue'])

define_winrt_com_method(IDirect3D11CaptureFramePoolStatics2, 'CreateFreeThreaded', IInspectable['Windows.Graphics.DirectX.Direct3D11.IDirect3DDevice'], DirectXPixelFormat, c_int32, SizeInt32, retval=Direct3D11CaptureFramePool) #FIXME: Windows.Graphics.DirectX.DirectXPixelFormat

define_winrt_com_method(IGraphicsCaptureItem, 'get_DisplayName', propget=HSTRING)
define_winrt_com_method(IGraphicsCaptureItem, 'get_Size', propget=SizeInt32)
define_winrt_com_method(IGraphicsCaptureItem, 'add_Closed', TypedEventHandler(GraphicsCaptureItem, IInspectable), retval=c_int64)
define_winrt_com_method(IGraphicsCaptureItem, 'remove_Closed', c_int64)

define_winrt_com_method(IGraphicsCaptureSession, 'StartCapture')

define_winrt_com_method(IGraphicsCaptureSession2, 'get_IsCursorCaptureEnabled', propget=c_bool)
define_winrt_com_method(IGraphicsCaptureSession2, 'put_IsCursorCaptureEnabled', propput=c_bool)

define_winrt_com_method(IGraphicsCaptureItemInterop, 'CreateForWindow', HWND, REFGUID, retval=GraphicsCaptureItem)
define_winrt_com_method(IGraphicsCaptureItemInterop, 'CreateForMonitor', HMONITOR, REFGUID, retval=GraphicsCaptureItem)

runtimeclass_add_statics(Direct3D11CaptureFramePool, IDirect3D11CaptureFramePoolStatics2)
