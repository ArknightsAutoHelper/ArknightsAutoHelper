from _ctypes import POINTER
from ctypes import c_uint, c_uint32, c_bool
from functools import lru_cache

from rotypes.idldsl import define_winrt_com_method, pinterface_type
from rotypes.inspectable import IInspectable


class IIterator_helpers:
    def __next__(self):
        if self.HasCurrent:
            value = self.Current
            self.MoveNext()
            return value
        raise StopIteration
    def __iter__(self):
        return self

@lru_cache()
def IIterator(T):
    cls = pinterface_type('IIterator', '6a79e863-4300-459a-9966-cbb660963ee1', (T,), (IInspectable, IIterator_helpers))
    define_winrt_com_method(cls, 'get_Current', propget=T, vtbl=6)
    define_winrt_com_method(cls, 'get_HasCurrent', propget=c_bool, vtbl=7)
    define_winrt_com_method(cls, 'MoveNext', retval=c_bool, vtbl=8)
    define_winrt_com_method(cls, 'GetMany', c_uint, POINTER(T), POINTER(c_uint), retval=c_uint32, vtbl=9)
    return cls


class IIterable_helpers:
    def __iter__(self):
        return self.First

@lru_cache()
def IIterable(T):
    cls = pinterface_type('IIterable', 'faa585ea-6214-4217-afda-7f46de5869b3', (T,), (IInspectable, IIterable_helpers))
    define_winrt_com_method(cls, 'get_First', propget=IIterator(T), vtbl=6)
    return cls


class IVectorView_helpers:
    def __len__(self):
        return self.Size
    def __getitem__(self, item):
        return self.GetAt(c_uint(item))


@lru_cache()
def IVectorView(T):
    cls = pinterface_type('IVectorView', 'bbe1fa4c-b0e3-4583-baef-1f1b2e483e56', (T,), (IIterable(T), IVectorView_helpers))
    define_winrt_com_method(cls, 'GetAt', c_uint, retval=T, vtbl=6)
    define_winrt_com_method(cls, 'get_Size', propget=c_uint32, vtbl=7)
    define_winrt_com_method(cls, 'IndexOf', T, POINTER(c_uint32), retval=c_bool, vtbl=8)
    define_winrt_com_method(cls, 'GetMany', c_uint, c_uint, POINTER(IInspectable), POINTER(c_uint), vtbl=9)
    return cls
