from abc import ABC, abstractmethod
from ..artifact import Artifact
from ..step import Step
from ...common.result import Result
from pydantic import BaseModel

class BuildError(BaseModel):
    pass

class Build(ABC, Step):
    @abstractmethod
    def __call__(self, artifacts: dict[str, Artifact]) -> Result[dict[str, Artifact], BuildError]:
        ...
