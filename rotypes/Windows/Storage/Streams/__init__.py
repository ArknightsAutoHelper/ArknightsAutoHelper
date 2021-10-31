from ctypes import c_uint32, c_void_p, string_at

from rotypes.idldsl import define_winrt_com_method, GUID
from rotypes.inspectable import IInspectable, IUnknown


@GUID('905a0fef-bc53-11df-8c49-001e4fc686da')
class IBufferByteAccess(IUnknown):
    pass


@GUID('905A0FE0-BC53-11DF-8C49-001E4FC686DA')
class IBuffer(IInspectable):
    def __len__(self):
        return self.Length
    def __bytes__(self):
        byteaccess = self.astype(IBufferByteAccess)
        ptr = byteaccess.Buffer()
        return string_at(ptr, len(self))


define_winrt_com_method(IBufferByteAccess, 'Buffer', retval=c_void_p)

define_winrt_com_method(IBuffer, 'get_Capacity', propget=c_uint32)
define_winrt_com_method(IBuffer, 'get_Length', propget=c_uint32)
define_winrt_com_method(IBuffer, 'put_Length', propput=c_uint32)


