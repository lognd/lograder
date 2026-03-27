from __future__ import annotations

from abc import ABC, abstractmethod
from inspect import isabstract
from typing import Any, Generator, Generic, TypeVar, cast, final

from lograder.common import Empty, Result, get_bound_types, unwrap_union_types
from lograder.exception import DeveloperException, LograderException

InputT = TypeVar("InputT")
OkOutputT = TypeVar("OkOutputT")
ErrOutputT = TypeVar("ErrOutputT")
OkDisplayT = TypeVar("OkDisplayT")
ErrDisplayT = TypeVar("ErrDisplayT")


# noinspection PyPep8Naming
@final
class _IS_ABSTRACT(Empty): ...


# I hate that the generic is only positional; I could make a `mypy` plugin and
# do this with a class-decorator but then anybody who uses this will also need
# to include the plugin.
class Step(Generic[InputT, OkOutputT, ErrOutputT, OkDisplayT, ErrDisplayT], ABC):
    _valid_input_types: set[type] | type[_IS_ABSTRACT] = _IS_ABSTRACT
    _valid_output_type: type[OkOutputT] | type[_IS_ABSTRACT] = _IS_ABSTRACT

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        bound_types = get_bound_types(cls, Step)
        if bound_types is None:
            # Should be unreachable.
            raise DeveloperException(
                f"`Step` subclass, `{cls.__name__}`, does not have `Step` in its origin bases, `{'`, `'.join(typ.__name__ for typ in getattr(cls, '__orig_bases__', ()))}`."
            )

        if bound_types == () and not isabstract(cls):
            raise DeveloperException(
                f"`Step` subclass, `{cls.__name__}`, requires FIVE generic parameters in the following order: "
                f"(1) `InputT` (can be union of types), which specifies the type(s) that the step may operate on; "
                f"(2) `OkOutputT`, which specifies the type that is RETURNED as `Ok(<ok-output-instance>)` and passed to the NEXT STEP; "
                f"(3) `ErrOutputT`, which specifies the type that is RETURNED as `Err(<err-output-instance>) and passed to the PACKET LOGGER, causing an early pipeline termination; "
                f"(4) `OkDisplayT`, which specifies the type that is YIELDED as `Ok(ok-display-instance)` and passed to the PACKET LOGGER; and "
                f"(5) `ErrDisplayT`, which specifies the type that is YIELDED as `Err(err-display-instance)` and passed to the PACKET LOGGER, which DOES NOT cause an early pipeline termination."
            )
        elif len(bound_types) != 5:
            raise DeveloperException(
                f"`Step` subclass, `{cls.__name__}`, must have 5 (not {len(bound_types)}) generic parameters in the following order: "
                f"(1) `InputT` (can be union of types), which specifies the type(s) that the step may operate on; "
                f"(2) `OkOutputT`, which specifies the type that is RETURNED as `Ok(<ok-output-instance>)` and passed to the NEXT STEP; "
                f"(3) `ErrOutputT`, which specifies the type that is RETURNED as `Err(<err-output-instance>) and passed to the PACKET LOGGER, causing an early pipeline termination; "
                f"(4) `OkDisplayT`, which specifies the type that is YIELDED as `Ok(ok-display-instance)` and passed to the PACKET LOGGER; and "
                f"(5) `ErrDisplayT`, which specifies the type that is YIELDED as `Err(err-display-instance)` and passed to the PACKET LOGGER, which DOES NOT cause an early pipeline termination. "
                f"Received: `{'`, `'.join(typ.__name__ for typ in bound_types)}`."
            )
        if not isabstract(cls):
            cls._valid_input_types = unwrap_union_types(bound_types[0])
            cls._valid_output_type = bound_types[1]
        else:
            cls._valid_input_types = _IS_ABSTRACT
            cls._valid_output_type = _IS_ABSTRACT

    @abstractmethod
    def __call__(
        self, input: InputT
    ) -> Generator[
        Result[OkDisplayT, ErrDisplayT],
        None,
        Result[OkOutputT, ErrOutputT],
    ]: ...

    @classmethod
    def is_abstract(cls) -> bool:
        return (
            cls._valid_input_types is _IS_ABSTRACT
            or cls._valid_output_type is _IS_ABSTRACT
        )

    @classmethod
    def get_valid_inputs(cls) -> frozenset[type]:
        if cls.is_abstract():
            raise DeveloperException(
                f"Tried to call `{cls.__name__}.get_valid_inputs(...)` even though `{cls.__name__}` is abstract."
            )
        # noinspection PyUnnecessaryCast
        return frozenset(cast(set[type], cls._valid_input_types))

    @classmethod
    def get_valid_output(cls) -> type[OkOutputT]:
        if cls.is_abstract():
            raise DeveloperException(
                f"Tried to call `{cls.__name__}.get_valid_output(...)` even though `{cls.__name__}` is abstract."
            )
        # noinspection PyUnnecessaryCast
        return cast(type[OkOutputT], cls._valid_output_type)

    @classmethod
    def is_follow(cls, prev: type[Step]) -> bool:
        if cls.is_abstract():
            raise DeveloperException(
                f"Tried to call `{cls.__name__}.is_follow(`{prev.__name__}`)` even though `{cls.__name__}` is abstract."
            )
        if prev.is_abstract():
            raise DeveloperException(
                f"Tried to call `{cls.__name__}.is_follow(`{prev.__name__}`)` even though `{prev.__name__}` is abstract."
            )
        if cls.get_valid_output() in prev.get_valid_inputs():
            return True
        return False

    @classmethod
    def assert_follow(
        cls,
        prev: type[Step],
        origin: str = "assert_follow",
        origin_exception_type: type[LograderException] = DeveloperException,
    ) -> None:
        if not cls.is_follow(prev):
            raise origin_exception_type(
                f"`{origin}` requires that step, `{cls.__name__}`, be able to follow, `{prev.__name__}`."
            )
