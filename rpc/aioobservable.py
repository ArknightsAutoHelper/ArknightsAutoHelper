
from __future__ import annotations
import asyncio
from typing import Any, Callable, Coroutine, Generic, Protocol, TypeVar

T = TypeVar('T')

async def foo(x: T) -> None:
    await asyncio.sleep(0.1)

class Observable(Protocol):
    def subscribe(self, observer: Callable[[T], None]):
        ...
    def unsubscribe(self, subscription: Subscription):
        ...

class Subscription:
    def __init__(self, observable: Observable, key):
        self.observable = observable
        self.key = key
    def unsubscribe(self):
        self.observable.unsubscribe(self.key)

class Subject(Generic[T]):
    def __init__(self):
        self.observers = {}
        self.subscription_seq = 0

    def subscribe(self, observer: Callable[[T], None]):
        self.subscription_seq += 1
        key = self.subscription_seq
        self.observers[key] = observer
        return Subscription(self, key)

    def subscribe_async(self, observer: Callable[[T], Coroutine[Any, None, None]], loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        def observer_wrapper(value: T):
            asyncio.run_coroutine_threadsafe(observer(value), loop)
        return self.subscribe(observer_wrapper)

    def unsubscribe(self, subscription: Subscription):
        if subscription.observable is not self:
            raise ValueError("subscription not associated with this subject")
        del self.observers[subscription.key]

    def next(self, value: T):
        observers = list(self.observers.values())
        for observer in observers:
            observer(value)