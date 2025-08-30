from abc import ABC, abstractmethod
from typing import Sequence, List
from pathlib import Path

from ...common.types import FilePath
from ..common.assignment import PreprocessorOutput, BuilderOutput
from ...tests.test import TestInterface

class PreprocessorResults:
    def __init__(self, output: PreprocessorOutput):
        # The reason why this is a class is in case we want to "expand" later.
        self._output = output

    def get_output(self) -> PreprocessorOutput:
        return self._output

class BuilderResults:
    def __init__(self, executable: FilePath, output: BuilderOutput):
        self._output = output
        self._executable = Path(executable)

    def get_output(self) -> BuilderOutput:
        return self._output

    def get_executable(self) -> Path:
        return self._executable

class RuntimeResults:
    def __init__(self, results: Sequence[TestInterface]):
        self._results = results

    def get_test_cases(self) -> List[TestInterface]:
        return list(self._results)

class BuilderInterface(ABC):
    @abstractmethod
    def __init__(self, project_root: FilePath):
        pass

    @abstractmethod
    def preprocess(self) -> PreprocessorResults:
        pass

    @abstractmethod
    def build(self) -> BuilderResults:
        pass

    @abstractmethod
    def run_tests(self) -> RuntimeResults:
        pass

