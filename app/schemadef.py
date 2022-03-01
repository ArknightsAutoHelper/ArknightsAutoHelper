from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
from typing import Any, Callable, ClassVar, Sequence, Type, TypeVar, Generic, Optional, Union

FieldType = TypeVar('FieldType')
ElementType = TypeVar('ElementType')
SubType = TypeVar('SubType')

class action:
    pass
_action_tag = action()

class Field(Generic[FieldType]):
    def __init__(self, type: Type[FieldType], default: FieldType, title: str = None, doc: str = None):
        self.type = type
        self.default = default
        self.title = title
        self.doc = doc
        self.name: str = ''  # will be set later

    def __set_name__(self, owner: Type[Schema], name: str):
        self.name = name
        if '_fields' not in owner.__dict__:
            if not hasattr(owner, '_fields'):
                owner._fields = OrderedDict()
            else:
                owner._fields = owner._fields.copy()
        owner._fields[name] = self

    def __get__(self, instance: Schema, owner: Type[Schema]) -> FieldType:
        if instance is None:
            return self
        return instance._store.get(self.name, self.default)

    def __set__(self, instance: Schema, value: FieldType):
        if value is not None:
            if not isinstance(value, self.type):
                raise TypeError(f'{value} is not {self.type}')
        instance._store[self.name] = value

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


class IntField(Field[int]):
    def __init__(self, default: int, title: str = None, doc: str = None, min: int = None, max: int = None):
        super().__init__(int, default, title, doc)
        self.min = min
        self.max = max

class Action(Field[object]):
    def __init__(self, button: str = None, title: str = None, doc: str = None):
        super().__init__(action, button, title, doc)
        self._handler = None
    
    def handler(self, func):
        self._handler = func
        return func

class Namespace(Field[SubType]):
    def __init__(self, title=None, doc=None):
        super().__init__(None, None, title, doc)

    def __call__(self, subtype: Type[SubType]) -> SubType:
        if not issubclass(subtype, Schema):
            newtype = type(subtype.__name__, (Schema, subtype), {})
            newtype.__qualname__ = subtype.__qualname__
            newtype.__module__ = subtype.__module__
            subtype = newtype
        self.type = subtype
        return self

    def __set_name__(self, owner: Type[Schema], name: str):
        super().__set_name__(owner, name)
        self.type._parent_schema = self.type

    def __get__(self, instance: Schema, owner: Type[Schema]) -> SubType:
        if instance is None:
            return self.type
        return instance._namespaces[self.name]
    
    def __set__(self, instance, value):
        raise AttributeError('Namespace is read-only')

class Schema:
    _parent_schema: ClassVar[Optional[Type[Schema]]] = None
    _fields: ClassVar[OrderedDict[str, Field]]
    def __init__(self, store: Optional[Mapping] = None, parent: Optional[Schema] = None):
        if store is None:
            store = _generate_default_store(self.__class__)
        self._store = store
        self._namespaces = {}
        self._parent = parent
        self._dirty = False
        for name, defn in self.__class__._fields.items():
            if isinstance(defn, Namespace):
                self._namespaces[name] = defn.type(store.get(name, None), self)
    def _set_dirty(self):
        if self._parent is not None:
            self._parent._set_dirty()
        else:
            self._dirty = True
    def __len__(self):
        return len(self._fields)
    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)
    def __iter__(self):
        for f in self._fields:
            yield (f, getattr(self, f))

def _generate_default_store(cls: Union[Type[Schema], Namespace], indent=0):
    if isinstance(cls, Namespace):
        cls = cls.type
    import ruamel.yaml
    ydoc = ruamel.yaml.CommentedMap()
    if hasattr(cls, '__version__'):
        ydoc['__version__'] = cls.__version__
    first_field = True
    for name, field in cls._fields.items():
        if name.startswith('_'):
            continue
        if isinstance(field, Field):
            if isinstance(field, Action):
                continue
            comment_lines = []
            if first_field:
                first_field = False
            else:
                comment_lines.append('')
            if isinstance(field, Namespace):
                ydoc[name] = _generate_default_store(field.type, indent + 2)
            else:
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

def _to_viewmodel(schema: Schema, name_prefix='', values: dict = None):
    result = []
    if values is None:
        values = {}
    for name, field in schema.__class__._fields.items():
        full_name = name_prefix + name
        item = dict(field_type=type(field).__name__, local_name=name, full_name=name_prefix + name, title=field.title, doc=field.doc)
        if isinstance(field, Namespace):
            item['fields'] = _to_viewmodel(getattr(schema, name), name_prefix + name + '.', values)[0]
        elif isinstance(field, Action):
            item['button'] = field.default
        else:
            values[full_name] = getattr(schema, name)
            item['default'] = field.default
            if isinstance(field, ListField):
                item['element_type'] = field.element_type.__name__
            elif isinstance(field, EnumField):
                item['enum_values'] = field.values
            else:
                item['value_type'] = field.type.__name__
        result.append(item)
    return result, values

def to_viewmodel(schema: Schema):
    return _to_viewmodel(schema)

def set_flat_values(schema: Schema, values: Mapping[str, Any]):
    for name, value in values.items():
        *parents, child = name.split('.')
        parent = schema
        for p in parents:
            parent = getattr(parent, p)
        setattr(parent, child, value)

__all__ = ['Schema', 'Field', 'EnumField', 'ListField', 'Namespace', 'is_dirty']
