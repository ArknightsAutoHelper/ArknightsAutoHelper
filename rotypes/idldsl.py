from _ctypes import _SimpleCData
from functools import lru_cache
import enum

from . import roapi
from .types import *

class CtypesEnum(enum.IntEnum):
    """A ctypes-compatible IntEnum superclass."""
    @classmethod
    def from_param(cls, obj):
        return int(obj)


def STDMETHOD(index, name, *argtypes):
    proto = WINFUNCTYPE(check_hresult, *argtypes)
    func = proto(index, name)
    return func


def define_winrt_com_method(interface, name, *argtypes, retval=None, propget=None, propput=None, vtbl: int = next):
    if vtbl is next:
        vtbl = interface._vtblend + 1
    if getattr(interface, '_method_defs', None) is None:
        setattr(interface, '_method_defs', [])
    if interface._method_defs is getattr(interface.__mro__[1], '_method_defs', None):
        setattr(interface, '_method_defs', [])
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
        interface._method_defs.append((vtbl, name, comfunc))
        setattr(interface, '_' + name, comfunc)
        setattr(interface, name, func)
    elif propget is not None:  # name = "get_Something"
        comgetter = STDMETHOD(vtbl, name, *argtypes, POINTER(propget))
        setattr(interface, name, comgetter)
        interface._method_defs.append((vtbl, name, comgetter))
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
        interface._method_defs.append((vtbl, name, comsetter))
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

        interface._method_defs.append((vtbl, name, comfunc))
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
        statics = roapi.GetActivationFactory(cls._runtimeclass_name, interface)
        return getattr(statics, propname)

    return classproperty(classmethod(getter))


def _static_method(interface, methodname):
    def func(cls, *args, **kwargs):
        statics = roapi.GetActivationFactory(cls._runtimeclass_name, interface)
        return getattr(statics, methodname)(*args, **kwargs)

    return classmethod(func)


def funcwrap(f):
    return lambda *args, **kw: f(*args, **kw)


def _non_activatable_init(self):
    raise NotImplementedError('non-activatable runtime class ' + self._runtimeclass_name)


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


def _runtimeclass_signature(classname, default_iid):
    return 'rc(%s;{%s})' % (classname, str(default_iid).lower())


def _get_type_signature(clazz):
    if hasattr(clazz, '_signature'):
        return clazz._signature
    elif isruntimeclass(clazz):
        return _runtimeclass_signature(clazz._runtimeclass_name, clazz.__mro__[2].GUID)
    elif hasattr(clazz, 'GUID'):
        return '{%s}' % str(clazz.GUID).lower()
    elif clazz in _predefined_sigs:
        return _predefined_sigs[clazz]
    else:
        raise TypeError('no signature for type', clazz)


_runtimeclass_registry = {}

class runtimeclass:
    def __init_subclass__(cls):
        mod1 = cls.__module__.split('.')
        mod2 = __name__.split('.')
        i = 0
        for i in range(min(len(mod1), len(mod2))):
            if mod1[i] != mod2[i]:
                break
        name = mod1[i:]
        name.append(cls.__name__)
        clsname = '.'.join(name)
        cls._runtimeclass_name = clsname
        _runtimeclass_registry[clsname] = cls


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
    return t.__qualname__


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

# def runtimeclass2(cls: type):
#     clsname = getattr(cls, '_runtimeclss_name_', None)
#     if clsname is None:
#         nameparts = cls.__qualname__.split('.')
#         refparts = __name__.split('.')
#         for i in range(min(len(nameparts), len(refparts))):
#                 if nameparts[i] != refparts[i]:
#                     break
#         clsname = '.'.join(nameparts[i:])
#     props = {'_runtimeclass_name': clsname}
#     bases = [runtimeclass]
#     if (default := getattr(cls, '_default_', None)) is not None:
#         bases.append(default)
#     interfaces = getattr(cls, '_default_', ())
#     bases.extend(interfaces)
#     statics = getattr(cls, '_static_', ())
#     for static_intf in statics:
#         static_intf # TODO
#     newcls = type(clsname, tuple(bases), props)
#     return newcls

def runtimeclass_add_statics(cls, interface):
    methods = [x[1] for x in interface._method_defs]
    clsname = cls._runtimeclass_name
    statics = roapi.GetActivationFactory(clsname, interface)
    for method in methods:
        wrapped_method = getattr(statics, method)
        def wrapper(*args, **kwargs):
            return wrapped_method(*args, **kwargs)
        setattr(cls, method, staticmethod(wrapper))
        