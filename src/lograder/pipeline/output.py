from abc import ABC, abstractmethod
from typing import Any, Type

from pydantic import BaseModel

from .step import _IS_ABSTRACT, Step


class OutputError(BaseModel):
    pass


class Output(Step, ABC):
    """
    Be careful when using this class; using any `Output` class other than `NothingOutput` may
    produce unexpected results like duplication. Most of the output is implicitly handled via
    logging configurations (which make things such as mid-script breaking non-lethal).
    """

    def __init_subclass__(
        cls,
        valid_input_types: list[Type[Step]] | Type[_IS_ABSTRACT] = _IS_ABSTRACT,
        **kwargs: Any,
    ):
        super().__init_subclass__(valid_input_types, None, **kwargs)

    @abstractmethod
    def __call__(self) -> None: ...


class NothingOutput(Output):
    def __call__(self) -> None:
        pass
