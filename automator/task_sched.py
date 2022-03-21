from __future__ import annotations

from dataclasses import dataclass
import dataclasses
import random
import string
from typing import Callable, ClassVar, Generic, Literal, Type, Optional, TypeVar
from collections import OrderedDict
from app.schemadef import Schema
from .helper import BaseAutomator
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

_task_registry: OrderedDict[str, _task_registry_item] = OrderedDict()


class task(Generic[TAddon, TSchema]):
    def __init__(self, category: str, title: str):
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
        _task_registry[name] = _task_registry_item(name, self.category, self.title, owner, self.schema, self._validator, self._handler)
        setattr(owner, name, self.schema)



@dataclass
class _task_record:
    id: str
    title: str
    status_text: str
    task_status: Literal['pending', 'running', 'success', 'failure']
    type: str
    config: Schema
    cron: Optional[str] = None


def serialize_task_record(task_record: _task_record):
    fields = dataclasses.fields(task_record)
    result = {}
    for field in fields:
        if field.name == 'config':
            result[field.name] = dict(task_record.config)
        else:
            result[field.name] = getattr(task_record, field.name)
    result['doc'] = task_record.config.__class__.__doc__
    return result

class TaskScheduler:
    def __init__(self, parent: BaseAutomator):
        self.parent = parent
        self.tasks: list[_task_record] = []
        self.cookie = random.choices(string.ascii_letters + string.digits, k=8)
        self.seq = 0
        self.current_task: _task_record = None
        self.pause = False

    def notify_list_update(self):
        self.parent.frontend.notify('task_list', [serialize_task_record(x) for x in self.tasks])

    def add_task(self, defn: dict):
        task_type = defn['type']
        task_config = defn['config']
        task_id = f'{self.cookie}-{self.seq:#04d}'
        reg = _task_registry[task_type]
        schema_type = reg.schema_t
        task_config = schema_type(task_config)
        if reg.validator is not None:
            if not reg.validator(self.parent.addon(reg.owner), task_config):
                raise ValueError(f'Task config is invalid: {task_config}')
        task_cron = defn.get('cron', None)
        self.tasks.append(_task_record(task_id, reg.title, '', task_type, task_config, task_cron))
        self.notify_list_update()

    def run(self):
        pass
    
    def reorder_task(self, moved_id, over_id):
        try:
            new_pos = next(i for i, x in enumerate(self.tasks) if x.id == over_id)
            old_pos = next(i for i, x in enumerate(self.tasks) if x.id == moved_id)
            self.tasks.insert(new_pos, self.tasks.pop(old_pos))
            self.notify_list_update()
        except StopIteration:  # no matching id
            pass
