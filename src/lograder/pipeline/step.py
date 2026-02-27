from __future__ import annotations

import inspect
from typing import Any, Callable, Iterable, Optional, Type, TypeVar, cast

from typing_extensions import Self

from ..common import Empty, Result
from ..exception import DeveloperException, LograderException, StaffException
from .conversion import ConversionRegistry

T = TypeVar("T")


# noinspection PyPep8Naming
class _IS_ABSTRACT(Empty): ...


class Step:
    _valid_inputs: set[Type[Step]] | Type[_IS_ABSTRACT]
    _output: Optional[Type[Step]] | Type[_IS_ABSTRACT]

    def __init_subclass__(
        cls,
        valid_input_types: Iterable[Type[Step]] | Type[_IS_ABSTRACT] = _IS_ABSTRACT,
        output_type: Optional[Type[Step]] | Type[_IS_ABSTRACT] = _IS_ABSTRACT,
        **kwargs: Any,
    ) -> None: ...

    @classmethod
    def get_valid_inputs(cls) -> frozenset[Type[Step]]: ...

    @classmethod
    def get_valid_output(cls) -> Optional[Type[Step]]: ...

    @classmethod
    def assert_begin(cls) -> None: ...

    @classmethod
    def assert_end(cls) -> None: ...

    @classmethod
    def assert_not_abstract(
        cls,
        origin: str = "assert_not_abstract",
        origin_exception_type: Type[LograderException] = DeveloperException,
    ) -> None:
        if inspect.isabstract(cls) or any(
            typ is _IS_ABSTRACT for typ in (cls._valid_inputs, cls._output)
        ):
            raise origin_exception_type(
                f"Cannot call `Step` subclass (`{cls.__name__}`)'s `{origin}(...)` class method because `{cls.__name__}` is an abstract class."
            )

    @classmethod
    def get_conversions_to(
        cls, next: Type[Step]
    ) -> set[Callable[[Self], Result[T, Any]]]: ...

    @classmethod
    def get_conversions_from(
        cls, prev: Type[Step]
    ) -> set[Callable[[Self], Result[T, Any]]]: ...

    @classmethod
    def assert_follow(cls, previous: Type[Step]) -> None: ...
