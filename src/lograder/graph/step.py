from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Type, TypeVar, cast

from ..common import Empty, Ok, Result, get_bound_types, unwrap_union_types
from ..exception import DeveloperException, LograderException
from .conversion import ConversionRegistry

In = TypeVar("In")
Out = TypeVar("Out")
In2 = TypeVar("In2")
Out2 = TypeVar("Out2")
In3 = TypeVar("In3")
Out3 = TypeVar("Out3")


# noinspection PyPep8Naming
class _IS_ABSTRACT(Empty): ...


# noinspection PyShadowingBuiltins
class Step(Generic[In, Out], ABC):
    _valid_input_types: set[type] | Type[_IS_ABSTRACT]
    _valid_output_type: Type[Out] | Type[_IS_ABSTRACT]
    _mutates_state: bool | Type[_IS_ABSTRACT]

    @abstractmethod
    def __init__(self) -> None: ...

    def __init_subclass__(
        cls,
        **kwargs: Any,
    ) -> None:
        super().__init_subclass__(**kwargs)

        bound_types = get_bound_types(cls, Step)
        if bound_types is None:
            # Should be unreachable.
            raise DeveloperException(
                f"`Step` subclass, `{cls.__name__}`, does not have `Step` in its origin bases, `{'`, `'.join(typ.__name__ for typ in getattr(cls, '__orig_bases__', ()))}`."
            )

        if bound_types == () and not inspect.isabstract(cls):
            raise DeveloperException(
                f"`Step` subclass, `{cls.__name__}`, must specify `In` (can be union of types) and `Out` types in the generic parameters of `Step`."
            )
        elif len(bound_types) != 2:
            raise DeveloperException(
                f"`Step` subclass, `{cls.__name__}`, must have two generic arguments: specify an `In` (can be union of types) type and an `Out` type. Received: `{'`, `'.join(typ.__name__ for typ in bound_types)}`."
            )

        if not inspect.isabstract(cls):
            cls._valid_input_types = unwrap_union_types(bound_types[0])
            cls._valid_output_type = bound_types[1]
            if (
                len(cls._valid_input_types) == 1
                and next(iter(cls._valid_input_types)) == cls._valid_output_type
            ):
                cls._mutates_state = False
            else:
                cls._mutates_state = True
        else:
            cls._valid_input_types = _IS_ABSTRACT
            cls._valid_output_type = _IS_ABSTRACT
            cls._mutates_state = _IS_ABSTRACT

    @classmethod
    def is_abstract(cls) -> bool:
        return (
            cls._valid_input_types is _IS_ABSTRACT
            or cls._valid_output_type is _IS_ABSTRACT
            or cls._mutates_state is _IS_ABSTRACT
        )

    @classmethod
    def is_promiscuous(cls) -> bool:
        return cls._valid_input_types == {Any} and cls._valid_output_type == Any

    @classmethod
    def is_mutating(cls) -> bool:
        if cls.is_abstract():
            raise DeveloperException(
                f"Tried to call `{cls.__name__}.is_mutating(...)` even though `{cls.__name__}` is abstract."
            )
        # noinspection PyUnnecessaryCast
        return cast(bool, cls._mutates_state)

    @classmethod
    def is_root(cls) -> bool:
        if cls.is_abstract():
            raise DeveloperException(
                f"Tried to call `{cls.__name__}.is_root(...)` even though `{cls.__name__}` is abstract."
            )
        # noinspection PyUnnecessaryCast
        return not bool(cast(set[type], cls._valid_input_types))

    @classmethod
    def is_follow(cls, prev: Type[Step]) -> bool:
        if cls.is_abstract():
            raise DeveloperException(
                f"Tried to call `{cls.__name__}.is_follow(`{prev.__name__}`)` even though `{cls.__name__}` is abstract."
            )
        if prev.is_abstract():
            raise DeveloperException(
                f"Tried to call `{cls.__name__}.is_follow(`{prev.__name__}`)` even though `{prev.__name__}` is abstract."
            )

        if cls.is_promiscuous() or cls.get_conversions_from(prev):
            return True
        return False

    @classmethod
    def get_valid_inputs(cls) -> frozenset[type]:
        if cls.is_abstract():
            raise DeveloperException(
                f"Tried to call `{cls.__name__}.get_valid_inputs(...)` even though `{cls.__name__}` is abstract."
            )
        # noinspection PyUnnecessaryCast
        return frozenset(cast(set[type], cls._valid_input_types))

    @classmethod
    def get_valid_output(cls) -> Type[Out]:
        if cls.is_abstract():
            raise DeveloperException(
                f"Tried to call `{cls.__name__}.get_valid_output(...)` even though `{cls.__name__}` is abstract."
            )
        # noinspection PyUnnecessaryCast
        return cast(Type[Out], cls._valid_output_type)

    @classmethod
    def assert_not_abstract(
        cls,
        origin: str = "assert_not_abstract",
        origin_exception_type: Type[LograderException] = DeveloperException,
    ) -> None:
        if cls.is_abstract():
            raise origin_exception_type(
                f"Cannot call `Step` subclass (`{cls.__name__}`)'s `{origin}(...)` class method because `{cls.__name__}` is an abstract class."
            )

    @classmethod
    def assert_mutating(
        cls,
        origin: str = "assert_mutating",
        origin_exception_type: Type[LograderException] = DeveloperException,
    ) -> None:
        if not cls.is_mutating():
            raise origin_exception_type(
                f"`{origin}` requires that step, `{cls.__name__}`, be mutating. Usually this means that this `Step` was called as a starting-step (root node)."
            )

    @classmethod
    def assert_follow(
        cls,
        prev: Type[Step],
        origin: str = "assert_follow",
        origin_exception_type: Type[LograderException] = DeveloperException,
    ) -> None:
        if not cls.is_follow(prev):
            raise origin_exception_type(
                f"`{origin}` requires that step, `{cls.__name__}`, be able to follow, `{prev.__name__}`."
            )

    @staticmethod
    def get_conversions(
        prev: Type[Step[In3, Out3]], next: Type[Step[In2, Out2]]
    ) -> set[Callable[[Out3], Result[In2, Any]]]:
        if prev.is_promiscuous() or next.is_promiscuous():
            # This is a built-in short-circuit. If a `Step` doesn't
            # care what is put into it and doesn't know what comes out
            # of itself, then there's no intelligible way to transform
            # to its type, i.e. it must "do-nothing" to the input and output.

            # noinspection PyUnnecessaryCast
            return {cast(Callable[[Out3], Result[In2, Any]], lambda x: Ok(x))}

        type_from: Type[Out3] = prev.get_valid_output()

        type_to_inp: frozenset[type] = next.get_valid_inputs()
        type_to_reg: frozenset[type] = ConversionRegistry.get_valid_targets(type_from)

        # This is a safe cast because `type_to_inp` is of type `frozenset[In2]`.
        # However, the type was widened to suppress complaints of incompatible types.
        # The intersection of `frozenset[In2]` with any other set is *at least* a
        # `frozenset[In2]`.

        type_tos: frozenset[Type[In2]] = cast(
            frozenset[Type[In2]], type_to_inp & type_to_reg
        )

        # Trivial "do-nothing" conversion always takes priority.
        if type_from in type_tos:
            # Cast is okay because in this case, `Out3` == `In2`.
            # noinspection PyUnnecessaryCast
            return {cast(Callable[[Out3], Result[In2, Any]], lambda x: Ok(x))}

        return {
            ConversionRegistry.get_conversion(type_from, type_to)
            for type_to in type_tos
        }

    @classmethod
    def get_conversions_to(
        cls, next: Type[Step[In2, Out2]]
    ) -> set[Callable[[Out], Result[In2, Any]]]:
        return cls.get_conversions(cls, next)

    @classmethod
    def get_conversions_from(
        cls, prev: Type[Step[In2, Out2]]
    ) -> set[Callable[[Out2], Result[In, Any]]]:
        return cls.get_conversions(prev, cls)
