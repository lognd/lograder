from abc import ABC, abstractmethod
from typing import Any, Optional, Type

from pydantic import BaseModel

from ..common import Result
from .package import Package
from .step import Step


class InputError(BaseModel):
    pass


class Input(Step, ABC):
    @abstractmethod
    def __call__(self) -> Result[Package, InputError]: ...
