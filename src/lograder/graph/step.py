from __future__ import annotations

import inspect
from typing import Any, Callable, Iterable, Optional, Type, TypeVar, cast

from ..common import Empty, Result
from ..exception import DeveloperException, LograderException, StaffException
from .conversion import ConversionRegistry

S = TypeVar("S")
T = TypeVar("T")
E = TypeVar("E")


# noinspection PyPep8Naming
class _IS_ABSTRACT(Empty): ...


class Step:
    _valid_input_types: set[type] | Type[_IS_ABSTRACT]
    _valid_output_type: Optional[type] | Type[_IS_ABSTRACT]

    def __init_subclass__(
        cls,
        valid_input_types: Iterable[type] | Type[_IS_ABSTRACT] = _IS_ABSTRACT,
        output_type: Optional[type] | Type[_IS_ABSTRACT] = _IS_ABSTRACT,
        **kwargs: Any,
    ) -> None: ...

    @classmethod
    def get_valid_inputs(cls) -> frozenset[type]: ...

    @classmethod
    def get_valid_output(cls) -> Optional[type]: ...

    @classmethod
    def assert_root(cls) -> None: ...

    @classmethod
    def assert_not_abstract(
        cls,
        origin: str = "assert_not_abstract",
        origin_exception_type: Type[LograderException] = DeveloperException,
    ) -> None:
        if inspect.isabstract(cls) or any(
            typ is _IS_ABSTRACT for typ in (cls._valid_input_types, cls._valid_output_type)
        ):
            raise origin_exception_type(
                f"Cannot call `Step` subclass (`{cls.__name__}`)'s `{origin}(...)` class method because `{cls.__name__}` is an abstract class."
            )

    @classmethod
    def get_conversions_to(
        cls, next: Type[Step]
    ) -> set[Callable[[S], Result[T, E]]]: ...

    @classmethod
    def get_conversions_from(
        cls, prev: Type[Step]
    ) -> set[Callable[[S], Result[T, E]]]: ...

    @classmethod
    def assert_follow(cls, previous: Type[Step]) -> None: ...
