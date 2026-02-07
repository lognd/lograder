from __future__ import annotations

import inspect
from typing import Any, Optional, Type, cast

from ..common import Empty
from ..exception import DeveloperException, LograderException, StaffException


# noinspection PyPep8Naming
class _IS_ABSTRACT(Empty): ...


class Step:
    _valid_inputs: list[Type[Step]] | Type[_IS_ABSTRACT]
    _output: Optional[Type[Step]] | Type[_IS_ABSTRACT]

    def __init_subclass__(
        cls,
        valid_input_types: list[Type[Step]] | Type[_IS_ABSTRACT] = _IS_ABSTRACT,
        output_type: Optional[Type[Step]] | Type[_IS_ABSTRACT] = _IS_ABSTRACT,
        **kwargs: Any,
    ):
        super().__init_subclass__(**kwargs)
        if valid_input_types is _IS_ABSTRACT and not inspect.isabstract(cls):
            raise DeveloperException(
                f"If `Step` subclass (`{cls.__name__}`) is not abstract, then it must specify `valid_input_types` (or explicitly, `[]`, if no inputs) in its subclass arguments."
            )
        elif output_type is _IS_ABSTRACT and not inspect.isabstract(cls):
            raise DeveloperException(
                f"If `Step` subclass (`{cls.__name__}`) is not abstract, then it must specify `output_type` (or explicitly, `None`, if no output) in its subclass arguments."
            )
        cls._valid_inputs = valid_input_types
        cls._output = output_type

    @classmethod
    def get_valid_inputs(cls) -> list[Type[Step]]:
        if inspect.isabstract(cls):
            raise DeveloperException(
                f"Cannot call `Step` subclass (`{cls.__name__}`)'s `get_valid_inputs()` class method because `{cls.__name__}` is an abstract class."
            )
        if cls._valid_inputs is _IS_ABSTRACT:
            # This call shouldn't be possible, as it should have been caught in __init_subclass__, but just in case.
            raise DeveloperException(
                f"Called `Step` subclass (`{cls.__name__}`)'s `get_valid_inputs()` class method with unspecified valid input types."
            )
        # Cast is safe because if cls._valid_inputs is _IS_ABSTRACT, then it should have been caught by the above.
        # I could use a TypeGuard, but I'm a little lazy.
        # noinspection PyUnnecessaryCast
        return cast(list[Type[Step]], cls._valid_inputs)

    @classmethod
    def assert_begin(cls) -> None:
        cls.assert_not_abstract(
            "assert_begin", StaffException
        )  # This is called to validate the pipeline the graders create; thus it would be a `StaffException` rather than a `DeveloperException`
        if cls._valid_inputs:
            # cls.assert_not_abstract ensures that cls._valid_inputs cannot be _IS_ABSTRACT
            raise StaffException(
                f'Pipeline tried to begin with `Step` subclass, `{cls.__name__}`, but `{cls.__name__}` is not a "beginning step". (In other words, the step accepts input types of [`{"`, `".join(typ.__name__ for typ in cast(list[type[Step]], cls._valid_inputs))}`] rather than simply `[]`.)'
            )

    @classmethod
    def assert_end(cls) -> None:
        cls.assert_not_abstract(
            "assert_end", StaffException
        )  # This is called to validate the pipeline the graders create; thus it would be a `StaffException` rather than a `DeveloperException`
        if cls._output is not None:
            raise StaffException(
                f'Pipeline tried to end with `Step` subclass, `{cls.__name__}`, but `{cls.__name__}` is not an "final step". (In other words, the step outputs type `{cls._output.__name__}` rather than simply `None`.)'
            )

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
    def assert_follow(cls, previous: Type[Step]) -> None:
        cls.assert_not_abstract(
            "assert_follow", StaffException
        )  # This is called to validate the pipeline the graders create; thus it would be a `StaffException` rather than a `DeveloperException`
        if not cls._valid_inputs:
            raise StaffException(
                f"Tried to follow a `Step` (`{previous.__name__}`) with a beginning step, `{cls.__name__}`, (a step with no input, typically a load-from-file for an autograder)."
            )
        if previous._output is None:
            raise StaffException(
                f"Tried to follow a final step (a step with no output, typically a write-to-file for an autograder) `{previous.__name__}` with another step, `{cls.__name__}`."
            )
        if not any(issubclass(previous._output, c) for c in cls.get_valid_inputs()):
            # cls.assert_not_abstract ensures that cls._valid_inputs cannot be _IS_ABSTRACT
            # PyTypeChecker is bugged; @property __mro__(self) returns a tuple corresponding to MRO without needing to "call" it.
            # noinspection PyTypeChecker,PyUnnecessaryCast
            raise StaffException(
                f"Invalid block sequence defined: `{cls.__name__}` occurs after `{previous.__name__}`, but\n"
                f"`{cls.__name__}` only takes the following blocks (and their subclasses) as valid input `{'`, `'.join(b.__name__ for b in cast(list[Type[Step]], cls._valid_inputs))}`.\n"
                f"For reference, the MRO for `{previous.__name__}` is `{'`, `'.join(b.__name__ for b in previous.__mro__)}`.\n"
                f"Fix your pipeline and make sure the block sequence that is used is valid."
            )
