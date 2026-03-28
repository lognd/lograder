from __future__ import annotations

import inspect
from typing import final


class EmptyMeta(type):
    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        # Force zero slots.
        namespace["__slots__"] = ()
        return super().__new__(mcls, name, bases, namespace, **kwargs)


class Empty(metaclass=EmptyMeta): ...


_SINGLETON_INSTANCES: dict[type[Singleton], Singleton] = {}


class Singleton(Empty):
    def __new__(cls) -> Singleton:
        if cls not in _SINGLETON_INSTANCES:
            _SINGLETON_INSTANCES[cls] = super().__new__(cls)
        return _SINGLETON_INSTANCES[cls]


@final
class Unreachable(Empty):
    def __new__(cls) -> Unreachable:
        frame = inspect.currentframe()
        try:
            caller = frame.f_back if frame is not None else None

            if caller is None:
                location = "unknown location"
            else:
                info = inspect.getframeinfo(caller)
                location = f"{info.filename}:{info.lineno} in {info.function}()"

            raise TypeError(
                f"`UNREACHABLE` was instantiated at {location}. "
                f"This sentinel should never be constructed at runtime."
            )
        finally:
            del frame
