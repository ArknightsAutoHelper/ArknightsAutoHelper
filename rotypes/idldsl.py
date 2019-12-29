from _ctypes import _SimpleCData
from functools import lru_cache

from . import roapi
from .types import *


def STDMETHOD(index, name, *argtypes):
    proto = WINFUNCTYPE(check_hresult, *argtypes)
    func = proto(index, name)
    return func


def define_winrt_com_method(interface, name, *argtypes, retval=None, propget=None, propput=None, vtbl: int = next):
    if vtbl is next:
        vtbl = interface._vtblend + 1
    if retval is not None:
        comfunc = STDMETHOD(vtbl, name, *argtypes, POINTER(retval))
        if retval.__mro__[1] is _SimpleCData:  # if return type is primitive type
            def func(this, *args, **kwargs):
                obj = this.astype(interface)
                result = retval()
                comfunc(obj, *args, byref(result), **kwargs)
                return result.value
        else:
            def func(this, *args, **kwargs):
                obj = this.astype(interface)
                result = _new_rtobj(retval)
                comfunc(obj, *args, byref(result), **kwargs)
                return result
        setattr(interface, '_' + name, comfunc)
        setattr(interface, name, func)
    elif propget is not None:  # name = "get_Something"
        comgetter = STDMETHOD(vtbl, name, *argtypes, POINTER(propget))
        setattr(interface, name, comgetter)
        if name.startswith('get_'):
            propname = name[4:]
            if propname in interface.__dict__:
                setter = interface.__dict__[propname].fset
            else:
                setter = None

            if propget.__mro__[1] is _SimpleCData:  # if return type is primitive type
                def getter(this, *args, **kwargs):
                    obj = this.astype(interface)
                    result = propget()
                    comgetter(obj, *args, byref(result), **kwargs)
                    return result.value
            else:
                def getter(this, *args, **kwargs):
                    obj = this.astype(interface)
                    result = _new_rtobj(propget)
                    comgetter(obj, *args, byref(result), **kwargs)
                    return result
            setattr(interface, propname, property(getter, setter))

    elif propput is not None:  # name = 'put_Something'
        comsetter = STDMETHOD(vtbl, name, *argtypes, propput)
        setattr(interface, name, comsetter)
        if name.startswith('put_'):
            propname = name[4:]
            if propname in interface.__dict__:
                getter = interface.__dict__[propname].fget
            else:
                getter = None

            def setter(this, *args, **kwargs):
                obj = this.astype(interface)
                comsetter(obj, *args, **kwargs)

            setattr(interface, propname, property(getter, setter))
    else:
        comfunc = STDMETHOD(vtbl, name, *argtypes)

        def func(this, *args, **kwargs):
            obj = this.astype(interface)
            comfunc(obj, *args, **kwargs)

        setattr(interface, name, funcwrap(func))

    if vtbl > interface._vtblend:
        interface._vtblend = vtbl


class classproperty(property):
    def __get__(self, obj, type_):
        return self.fget.__get__(None, type_)()

    def __set__(self, obj, value):
        cls = type(obj)
        return self.fset.__get__(None, cls)(value)


def _static_propget(interface, propname):
    def getter(cls):
        statics = roapi.GetActivationFactory(cls._runtimeclass_name(), interface)
        return getattr(statics, propname)

    return classproperty(classmethod(getter))


def _static_method(interface, methodname):
    def func(cls, *args, **kwargs):
        statics = roapi.GetActivationFactory(cls._runtimeclass_name(), interface)
        return getattr(statics, methodname)(*args, **kwargs)

    return classmethod(func)


def funcwrap(f):
    return lambda *args, **kw: f(*args, **kw)


def _non_activatable_init(self):
    raise NotImplementedError('non-activatable runtime class ' + self._runtimeclass_name())


_predefined_sigs = {
    c_uint8: 'u1',
    c_int32: 'i4',
    c_uint32: 'u4',
    c_int64: 'i8',
    c_uint64: 'u8',
    c_float: 'f4',
    c_double: 'f8',
    c_bool: 'b1',
    str: 'string',
    'char16': 'c2',
    GUID: 'g16',
}


def _runtimeclass_signature(classname, interface):
    return 'rc(%s;{%s})' % (classname, interface.IID.lower())


def _get_type_signature(clazz):
    if hasattr(clazz, '_signature'):
        return clazz._signature
    elif isruntimeclass(clazz):
        return _runtimeclass_signature(clazz._runtimeclass_name(), clazz.__mro__[2])
    elif hasattr(clazz, 'IID'):
        return '{%s}' % clazz.IID
    elif clazz in _predefined_sigs:
        return _predefined_sigs[clazz]
    else:
        raise TypeError('no signature for type', clazz)


class runtimeclass:
    @classmethod
    @lru_cache()
    def _runtimeclass_name(cls):
        mod1 = cls.__module__.split('.')
        mod2 = __name__.split('.')
        i = 0
        for i in range(min(len(mod1), len(mod2))):
            if mod1[i] != mod2[i]:
                break
        name = mod1[i:]
        name.append(cls.__name__)
        return '.'.join(name)


def isruntimeclass(clazz):
    return clazz.__mro__[1] is runtimeclass


def _new_rtobj(clazz):
    if isruntimeclass(clazz):  # is a runtimeclass
        return clazz.__mro__[2].__new__(clazz)
    return clazz()


def generics_cache(func):
    def wrapped(*types):
        if types in wrapped.known_types:
            return wrapped.known_types[types]
        return func(*types)

    wrapped.known_types = {}
    return wrapped


def _sigoctets_to_uuid(octets):
    import hashlib
    digest = hashlib.sha1()
    digest.update(octets)
    uuidbytes = bytearray(digest.digest()[:16])
    octet6 = uuidbytes[6]
    octet6 = (octet6 & 0b00001111) | 0b01010000
    uuidbytes[6] = octet6
    octet8 = uuidbytes[8]
    octet8 = (octet8 & 0b00111111) | 0b10000000
    uuidbytes[8] = octet8
    return '%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x' % tuple(uuidbytes)


@lru_cache()
def generate_parameterized_attrs(piid, *generics):
    newsig = 'pinterface({%s};%s)' % (piid, ';'.join(map(_get_type_signature, generics)))
    sigoctets = b'\x11\xF4z\xD5{sB\xC0\xAB\xAE\x87\x8B\x1E\x16\xAD\xEE' + newsig.encode('utf-8')
    guid = _sigoctets_to_uuid(sigoctets)
    return {'IID': guid, '_signature': newsig, '_typeparam': generics}


def fqn(t):
    return t.__module__ + '.' + t.__name__


def pinterface_type(name, piid, typeparams, bases):
    attrs = generate_parameterized_attrs(piid, *typeparams)
    cls = type('%s(%s)' % (name, ','.join(map(fqn, typeparams))), bases, attrs)
    return cls


def define_winrt_com_delegate(cls, *argtypes, retval=None):
    from . import delegate
    if retval is not None:
        define_winrt_com_method(cls, 'Invoke', *argtypes, POINTER(retval), vtbl=3)
    else:
        define_winrt_com_method(cls, 'Invoke', *argtypes, vtbl=3)
    cls._funcproto = delegate.proto(cls, *argtypes, retval=retval)
