from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, ClassVar, Generic, Type, Optional, TypeVar
from app.schemadef import Schema
from .addon import AddonBase

TAddon = TypeVar('TAddon', bound=AddonBase)
TSchema = TypeVar('TSchema', bound=Schema)

@dataclass
class _task_registry_item:
    name: str
    category: str
    title: str
    owner: Type[TAddon]
    schema_t: Type[TSchema]
    validator: Callable[[TAddon, TSchema], bool]
    handler: Callable[[TAddon, TSchema], None]

_task_registry: list[_task_registry_item] = []


class task(Generic[TAddon, TSchema]):
    def __init__(self, category: str, title: str, ):
        self.category = category
        self.title = title
        self._handler = None
        self._validator = None
    
    def __call__(self, schema: TSchema) -> TSchema:
        self.schema = schema
        return self

    def handler(self, handler: Callable[[TAddon, TSchema], None]):
        self._handler = handler
        return handler

    def validate(self, validator: Callable[[TAddon, TSchema], bool]):
        self._validator = validator
        return validator

    def __set_name__(self, owner: TAddon, name: str):
        _task_registry.append(_task_registry_item(name, self.category, self.title, owner, self.schema, self._validator, self._handler))
        setattr(owner, name, self.schema)
    

