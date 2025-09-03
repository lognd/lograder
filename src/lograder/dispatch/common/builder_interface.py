from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Sequence
import json

from .types import AssignmentMetadata
from .. import AssignmentSummary
from ...common.types import FilePath
from ...tests.registry import TestRegistry
from ...tests.test import TestInterface
from ..common.assignment import BuilderOutput, PreprocessorOutput
from colorama import Fore

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
    def __init__(self):
        self._build_fail: bool = False

    def get_build_fail(self) -> bool:
        return self._build_fail

    def set_build_fail(self, fail: bool):
        self._build_fail = fail

    def run(self, out_path: Path = Path('/autograder/results/results.json')) -> AssignmentSummary:
        metadata = self.metadata()
        prep = self.preprocess()
        build = self.build()
        runtime_results = self.run_tests()

        summary = AssignmentSummary(
            metadata=metadata,
            preprocessor_output=prep.get_output(),
            build_output=build.get_output(),
            test_cases=runtime_results.get_test_cases(),
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary.model_dump()))
        return summary

    @abstractmethod
    def metadata(self) -> AssignmentMetadata:
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
