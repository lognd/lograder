from abc import ABC, abstractmethod
from typing import Any, Optional, Type

from pydantic import BaseModel

from ..common import Result
from .package import Package
from .step import _IS_ABSTRACT, Step


class InputError(BaseModel):
    pass


class Input(Step, ABC):
    def __init_subclass__(
        cls,
        output_type: Optional[Type[Step]] | Type[_IS_ABSTRACT] = _IS_ABSTRACT,
        **kwargs: Any,
    ):
        super().__init_subclass__([], output_type, **kwargs)

    @abstractmethod
    def __call__(self) -> Result[Package, InputError]: ...
