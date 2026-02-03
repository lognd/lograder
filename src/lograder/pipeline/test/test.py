from abc import ABC, abstractmethod
from ..artifact import Artifact
from ..step import Step
from ...common.result import Result
from pydantic import BaseModel

class TestError(BaseModel):
    __test__: bool = False
    pass

class TestData(BaseModel):
    __test__: bool = False
    pass

class Test(ABC):
    __test__: bool = False

    def __init__(self, parallel: bool = False):
        self._parallel: bool = parallel

    @property
    def parallel(self) -> bool:
        return self._parallel

    @abstractmethod
    def __call__(self, artifacts: dict[str, Artifact]) -> Result[list[TestData], TestError]:
        ...