from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from ..common import Result
from .step import Step

T = TypeVar("T")
V = TypeVar("V")


class CheckError(BaseModel):
    pass


class Conversion(Generic[T, V], Step, ABC):
    @abstractmethod
    def __call__(self, from_: T) -> Result[V, CheckError]:
        pass
