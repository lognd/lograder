from abc import ABC, abstractmethod

from pydantic import BaseModel

from ...common.result import Result
from ..package import Package
from ..step import Step


class CheckError(BaseModel):
    pass


class Check(Step, ABC):
    def __init__(self, parallel: bool = False):
        self._parallel: bool = parallel

    @property
    def parallel(self) -> bool:
        return self._parallel

    @abstractmethod
    def __call__(self, package: Package) -> Result[Package, CheckError]: ...
