from ctypes import WINFUNCTYPE, HRESULT, POINTER, Structure, c_void_p, cast, pointer

from .inspectable import IUnknown
from .types import REFGUID, VOIDPP, ULONG, GUID, E_NOINTERFACE, S_OK, E_FAIL

_refmap = {}

_typeof_QueryInterface = WINFUNCTYPE(HRESULT, c_void_p, REFGUID, VOIDPP)
_typeof_AddRef = WINFUNCTYPE(ULONG, c_void_p)
_typeof_Release = WINFUNCTYPE(ULONG, c_void_p)


class _impl_delegate_vtbl(Structure):
    _fields_ = [('QueryInterface', _typeof_QueryInterface), ('AddRef', _typeof_AddRef), ('Release', _typeof_Release),
                ('Invoke', c_void_p)]


class _impl_delegate(Structure):
    _fields_ = [('vtbl', POINTER(_impl_delegate_vtbl))]


def proto(*argtypes, retval=None):
    if retval is not None:
        argtypes = (*argtypes, POINTER(retval))
    proto = WINFUNCTYPE(HRESULT, *argtypes)
    proto._retval = retval
    return proto


class delegatebase:
    @classmethod
    def delegate(cls, func):
        vtbl = _impl_delegate_vtbl()
        iid = GUID(cls.IID)

        def impl_AddRef(this):
            refcnt = _refmap[this][1] + 1
            _refmap[this][1] = refcnt
            return refcnt

        def impl_QueryInterface(this, refiid, ppunk):
            try:
                wantiid = refiid.contents
                if wantiid == GUID(IUnknown.IID) or wantiid == iid:
                    impl_AddRef(this)
                    ppunk[0] = this
                    return S_OK
                ppunk[0] = None
                return E_NOINTERFACE
            except Exception:
                return E_FAIL

        def impl_Release(this):
            refcnt = _refmap[this][1] - 1
            _refmap[this][1] = refcnt
            if refcnt == 0:
                del _refmap[this]
            return refcnt

        proto = cls._funcproto
        if proto._retval is not None:
            def impl_Invoke(this, *args):
                try:
                    for arg in args:
                        if isinstance(arg, IUnknown):
                            arg._own_object = False
                    retval = func(*args[:-1])
                    args[-1][0] = retval
                    return S_OK
                except Exception as e:
                    print(e)
                    return E_FAIL
        else:
            def impl_Invoke(this, *args, **kwargs):
                if isinstance(this, IUnknown):
                    this._own_object = False
                try:
                    for arg in args:
                        if isinstance(arg, IUnknown):
                            arg._own_object = False
                    func(*args, **kwargs)
                    return S_OK
                except Exception as e:
                    print(e)
                    return E_FAIL

        cb = proto(impl_Invoke)

        vtbl.QueryInterface = _typeof_QueryInterface(impl_QueryInterface)
        vtbl.AddRef = _typeof_AddRef(impl_AddRef)
        vtbl.Release = _typeof_Release(impl_Release)
        vtbl.Invoke = cast(cb, c_void_p)

        obj = _impl_delegate()
        obj.vtbl = pointer(vtbl)
        objptr = pointer(obj)

        objptrval = cast(objptr, c_void_p).value

        keepref = (objptr, obj, vtbl, cb, func)
        _refmap[objptrval] = [keepref, 1]
        return cast(objptr, cls)  # reference #1
