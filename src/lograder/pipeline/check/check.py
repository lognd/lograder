from abc import ABC, abstractmethod
from ..package import Package
from ..step import Step
from ...common.result import Result
from pydantic import BaseModel

class CheckError(BaseModel):
    pass

class Check(ABC, Step):
    def __init__(self, parallel: bool = False):
        self._parallel: bool = parallel

    @property
    def parallel(self) -> bool:
        return self._parallel

    @abstractmethod
    def __call__(self, package: Package) -> Result[Package, CheckError]:
        ...
