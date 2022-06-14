from __future__ import annotations
import inspect
from collections.abc import Mapping
from typing import Callable, ClassVar, Sequence, Type, TypeVar, Generic, Optional, Union

FieldType = TypeVar('FieldType')
ElementType = TypeVar('ElementType')
SubType = TypeVar('SubType')

_default_tag = object()
class UseDecoratedFunction:
    def __call__(self):
        raise NotImplementedError()

_use_decorated_function = UseDecoratedFunction()
class Field(Generic[FieldType]):
    def __init__(self, type: Type[FieldType], default: Union[FieldType, UseDecoratedFunction] = _use_decorated_function, title: str = None, doc: str = None):
        self.type = type
        self.default = default
        self.lazy_default = default is _use_decorated_function
        self.title = title
        self.doc = doc
        self.name: str = ''  # will be set later

    def __set_name__(self, owner: Type[Schema], name: str):
        self.name = name

    def __get__(self, instance: Schema, owner: Type[Schema]) -> FieldType:
        if instance is None:
            return self
        value = instance._mapping.get(self.name, _default_tag)
        if value is _default_tag:
            if self.lazy_default:
                value = self.default(instance)
                instance._mapping[self.name] = value
            else:
                value = self.default
        return value

    def __set__(self, instance: Schema, value: FieldType):
        if value is not None:
            if not isinstance(value, self.type):
                raise TypeError(f'{value} is not {self.type}')
        instance._mapping[self.name] = value
        instance._set_dirty()

    def __call__(self, default_factory: Callable[[Schema], FieldType]):
        self.default = default_factory
        return self

class UserReadOnlyField(Field[FieldType]):
    pass

class EnumField(Field[FieldType]):
    def __init__(self, values: Sequence[FieldType], default: FieldType, title=None, doc=None):
        super().__init__(type(values[0]), default, title, doc)
        self.values = values

    def __set__(self, instance: Schema, value: FieldType):
        if value not in self.values:
            raise TypeError(f'{value} is not in {self.values}')
        super().__set__(instance, value)

class ListField(Field[list[ElementType]]):
    def __init__(self, element_type: Type[ElementType], default: list[ElementType], title=None, doc=None):
        super().__init__(list, default, title, doc)
        self.element_type = element_type

    def __set__(self, instance: Schema, value: list[ElementType]):
        if value is not None:
            if not all(isinstance(e, self.element_type) for e in value):
                raise TypeError(f'{value} is not {self.element_type}')
        super().__set__(instance, value)


class Namespace(Field[SubType]):
    def __init__(self, title=None, doc=None):
        super().__init__(None, None, title, doc)

    def __call__(self, subtype: Type[SubType]) -> SubType:
        if not issubclass(subtype, Schema):
            subtype = type(subtype.__name__, (Schema, subtype), {k: v for k, v in subtype.__dict__.items()})
        self.type = subtype
        return self

    def __set_name__(self, owner: Type[Schema], name: str):
        super().__set_name__(owner, name)
        self.type._parent_schema = self.type

    def __get__(self, instance: Schema, owner: Type[Schema]) -> SubType:
        if instance is None:
            return self
        return instance._namespaces[self.name]
    
    def __set__(self, instance, value: Schema):
        if not isinstance(value, Schema):
            raise TypeError(f'value is not a Schema instance')
        instance._mapping[self.name] = value._mapping
        instance._namespaces[self.name] = value
        

class Schema:
    _parent_schema: ClassVar[Optional[Type[Schema]]] = None
    def __init__(self, store: Optional[Mapping] = None, parent: Optional[Schema] = None):
        if store is None:
            store = _generate_default_store(self.__class__)
        self._mapping = store
        self._namespaces = {}
        self._parent = parent
        self._dirty = False
        for name, defn in self.__class__.__dict__.items():
            if isinstance(defn, Namespace):
                self._namespaces[name] = defn.type(store.get(name, None), self)
    def _set_dirty(self):
        if self._parent is not None:
            self._parent._set_dirty()
        else:
            self._dirty = True


def _get_declared_fields(cls: Type[Schema]) -> dict[str, Field]:
    result = {}
    mros = inspect.getmro(cls)
    for base in mros[::-1]:
        base_dict = getattr(base, '__dict__', {})
        for name, value in base_dict.items():
            if name not in result and isinstance(value, Field):
                result[name] = value
    return result

def _generate_default_store(cls: Union[Type[Schema], Namespace], indent=0):
    if isinstance(cls, Namespace):
        cls = cls.type
    import ruamel.yaml
    ydoc = ruamel.yaml.CommentedMap()
    if hasattr(cls, '__version__'):
        ydoc['__version__'] = cls.__version__
    first_field = True
    for name, field in _get_declared_fields(cls).items():
        comment_lines = []
        if first_field:
            first_field = False
        else:
            comment_lines.append('')
        if isinstance(field, Namespace):
            ydoc[name] = _generate_default_store(field.type, indent + 2)
        else:
            if not field.lazy_default:
                ydoc[name] = field.default
        if field.title:
            comment_lines.append(field.title)
        if field.doc:
            comment_lines.append(field.doc)
        comment = '\n'.join(comment_lines)
        if comment:
            ydoc.yaml_set_comment_before_after_key(name, before=comment, indent=indent)
    return ydoc


def is_dirty(schema: Schema):
    return schema._dirty

__all__ = ['Schema', 'Field', 'EnumField', 'ListField', 'Namespace', 'is_dirty']
