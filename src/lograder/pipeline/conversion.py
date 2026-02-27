from abc import ABC
from typing import Any, TypeVar, Type

from typing import Callable, cast

from ..common import Result

from ..exception import DeveloperException, StaffException

A = TypeVar("A")
B = TypeVar("B")

class ConversionRegistry(ABC):
    _registered_conversions: dict[tuple[type, type], Callable[[Any], Result[Any, Any]]] = {}
    _f_map: dict[type, set[type]] = {}
    _r_map: dict[type, set[type]] = {}

    @classmethod
    def register_conversion(cls, type_from: Type[A], type_to: Type[B], conversion: Callable[[A], Result[B, Any]]) -> None:
        if (type_from, type_to) in cls._registered_conversions:
            raise DeveloperException(
                f"Tried to register a second conversion (`{conversion.__qualname__}`) from `{type_from.__name__}` to `{type_to.__name__}`, but another conversion was already defined (`{cls._registered_conversions[(type_from, type_to)].__qualname__}`)."
            )
        cls._f_map.setdefault(type_from, set()).add(type_to)
        cls._r_map.setdefault(type_to, set()).add(type_from)
        cls._registered_conversions[(type_from, type_to)] = conversion

    @classmethod
    def _error_helper(cls, type_from: Type[A], type_to: Type[B]) -> str:
        msg = []
        if type_from in cls._f_map:
            msg.append(f"The only registered conversions from `{type_from.__name__}` are `{'`, `'.join(typ.__name__ for typ in cls.get_valid_targets(type_from))}`.")
        else:
            msg.append(f"There are no registered conversions from `{type_from.__name__}`.")
        if type_to in cls._r_map:
            msg.append(f"The only registered conversions to `{type_to.__name__}` are `{'`, `'.join(typ.__name__ for typ in cls.get_valid_sources(type_to))}`.")
        else:
            msg.append(f"There are no registered conversions to `{type_from.__name__}`.")
        return " ".join(msg)

    @classmethod
    def get_conversion(cls, type_from: Type[A], type_to: Type[B]) -> Callable[[A], Result[B, Any]]:
        if (type_from, type_to) not in cls._registered_conversions:
            raise StaffException(
                f"Tried to get a conversion that doesn't exist (from `{type_from.__name__}` to `{type_to.__name__}`). "
                + cls._error_helper(type_from, type_to)
            )
        # This cast is necessary; I type-erased because class variables can't be generic.
        # However, because of the invariance of this class (see the `register_conversion`
        # method), we can safely say that the registered function has the correct type and
        # can be narrow-casted.

        # noinspection PyUnnecessaryCast
        return cast(Callable[[A], Result[B, Any]], cls._registered_conversions[(type_from, type_to)])

    @classmethod
    def get_valid_targets(cls, type_from: type) -> frozenset[type]:
        return frozenset(cls._f_map[type_from])

    @classmethod
    def get_valid_sources(cls, type_to: type) -> frozenset[type]:
        return frozenset(cls._r_map[type_to])


def convert(type_from: Type[A], type_to: Type[B]) -> Callable[[A], Result[B, Any]]:
    return ConversionRegistry.get_conversion(type_from, type_to)

def register_conversion(type_from: Type[A], type_to: Type[B]) -> Callable[[Callable[[A], B]], Callable[[A], B]]:
    def wrapper(func: Callable[[A], Result[B, Any]]) -> Callable[[A], Result[B, Any]]:
        ConversionRegistry.register_conversion(type_from, type_to, func)
        return func
    return wrapper
