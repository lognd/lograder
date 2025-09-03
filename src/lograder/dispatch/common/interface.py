from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Sequence
import json

from tests.test import ExecutableTestInterface
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
    def __init__(self, results: Sequence[ExecutableTestInterface]):
        self._results = results

    def get_test_cases(self) -> List[ExecutableTestInterface]:
        return list(self._results)

class ProcessInterface(ABC):
    _linked_preprocessors: set[PreprocessorInterface] = set()
    _linked_builders: set[BuilderInterface] = set()
    _linked_runners: set[RunnerInterface] = set()

    @classmethod
    def register_builder(cls, builder: BuilderInterface):
        cls._linked_builders.add(builder)

    @classmethod
    def register_preprocessor(cls, preprocessor: PreprocessorInterface):
        cls._linked_preprocessors.add(preprocessor)

    @classmethod
    def register_runner(cls, runner: RunnerInterface):
        cls._linked_runners.add(runner)

    @classmethod
    def is_build_successful(cls) -> bool:
        for builder in cls._linked_builders:
            if builder.get_build_error():
                return False
        return True

    @classmethod
    def is_preprocessor_successful(cls) -> bool:
        return cls.get_validation_multiplier() == 1.0

    @classmethod
    def get_validation_multiplier(cls) -> float:
        scores = [prep.get_validation_penalty() for prep in cls._linked_preprocessors]
        score = 1.0
        for score in scores:
            score *= score
        return score

    def __eq__(self, other):
        return id(self) == id(other)  # default "is" comparison, but it's here in case it changes.

    def __hash__(self):
        return hash(id(self))

class PreprocessorInterface(ProcessInterface, ABC):
    def __init__(self):
        super().__init__()
        ProcessInterface.register_preprocessor(self)
        self._validation_penalty: float = 0.0

    def set_validation_penalty(self, penalty: float):
        self._validation_penalty = penalty

    def get_validation_penalty(self) -> float:
        return self._validation_penalty

    def get_validation_multiplier(self) -> float:
        return 1.0 - min(max(self.get_validation_penalty(), 0.0), 1.0)

    def set_validation_error(self):
        self.set_validation_penalty(1.0)

    @abstractmethod
    def validate(self):
        pass

class BuilderInterface(ProcessInterface, ABC):
    def __init__(self):
        super().__init__()
        ProcessInterface.register_builder(self)
        self._build_error: bool = False

    def set_build_error(self, build_error: bool):
        self._build_error = build_error

    def get_build_error(self) -> bool:
        return self._build_error

    @abstractmethod
    def build(self) -> BuilderResults:
        pass

class RunnerInterface(ProcessInterface, ABC):
    def __init__(self):
        super().__init__()
        ProcessInterface.register_runner(self)

    def run(self) -> RuntimeResults:
        results = self.run_tests()
        for test_case in results.get_test_cases():
            if not self.is_build_successful():
                test_case.force_unsuccessful()


    @abstractmethod
    def run_tests(self) -> RuntimeResults:
        pass

class DispatcherInterface(ABC):
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
