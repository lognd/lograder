from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Sequence

from ...common.types import FilePath
from ...static import LograderBasicConfig, LograderMessageConfig
from ...tests.common.exceptions import TestNotRunError

if TYPE_CHECKING:
    from ...tests.test.interface import ExecutableTestInterface

from ..common.assignment import AssignmentSummary, BuilderOutput, PreprocessorOutput
from .types import AssignmentMetadata


class PreprocessorResults:
    def __init__(self, output: PreprocessorOutput):
        # The reason why this is a class is in case we want to "expand" later.
        self._output = output

    def get_output(self) -> PreprocessorOutput:
        return self._output


class BuildResults:
    def __init__(self, output: BuilderOutput):
        self._output = output

    def get_output(self) -> BuilderOutput:
        return self._output


class ExecutableBuildResults(BuildResults):
    def __init__(self, executable: FilePath, output: BuilderOutput):
        super().__init__(output)
        self._executable = Path(executable)

    def get_executable(self) -> Path:
        return self._executable


class RuntimePrepResults:  # dummy class to allow distinguishing between pre- and post-run.
    def __init__(
        self,
        results: (
            RuntimePrepResults | RuntimeResults | Sequence[ExecutableTestInterface]
        ),
    ):
        if isinstance(results, RuntimePrepResults):
            self._results = results.get_test_cases()
        else:
            self._results = list(results)

    def get_test_cases(self) -> List[ExecutableTestInterface]:
        return self._results


class RuntimeResults(RuntimePrepResults):
    def get_test_cases(self) -> List[ExecutableTestInterface]:
        for result in self._results:
            if not result.is_executed():
                raise TestNotRunError(result.get_name())
        return self._results


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
            if builder.is_build_error():
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
        return id(self) == id(
            other
        )  # default "is" comparison, but it's here in case it changes.

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

    def get_individual_validation_multiplier(self) -> float:
        return 1.0 - min(max(self.get_validation_penalty(), 0.0), 1.0)

    def check(self):
        if self.validate():
            return
        self.set_validation_penalty(1.0)

    @abstractmethod
    def validate(self) -> bool:
        pass

    @abstractmethod
    def preprocess(self) -> PreprocessorResults:
        pass


class BuilderInterface(ProcessInterface, ABC):
    def __init__(self):
        super().__init__()
        ProcessInterface.register_builder(self)
        self._build_error: bool = False

    def set_build_error(self, build_error: bool):
        self._build_error = build_error

    def is_build_error(self) -> bool:
        return self._build_error

    @abstractmethod
    def build(self) -> BuildResults:
        pass


class ExecutableBuilderInterface(BuilderInterface, ABC):
    @abstractmethod
    def build(self) -> ExecutableBuildResults:
        pass


class RunnerInterface(ProcessInterface, ABC):
    def __init__(self):
        super().__init__()
        ProcessInterface.register_runner(self)
        self._wrap_args: bool = False
        self._cwd: Optional[Path] = None

    def set_cwd(self, cwd: Path):
        self._cwd = cwd

    def set_wrap_args(self, wrap_args: bool = True):
        self._wrap_args = wrap_args

    def run_tests_auto(self) -> RuntimeResults:
        results: RuntimePrepResults = self.prep_tests()
        for test_case in results.get_test_cases():
            if not self.is_build_successful():
                test_case.force_unsuccessful()
                test_case.override_output(
                    LograderMessageConfig.DEFAULT_BUILD_ERROR_OVERRIDE_MESSAGE,
                    LograderMessageConfig.DEFAULT_BUILD_ERROR_OVERRIDE_MESSAGE,
                )
            else:
                test_case.run(wrap_args=self._wrap_args, working_directory=self._cwd)
        return RuntimeResults(results)

    @abstractmethod
    def prep_tests(self) -> RuntimePrepResults:
        pass


class DispatcherInterface(ABC):
    def run(
        self, out_path: Path = LograderBasicConfig.DEFAULT_RESULT_PATH
    ) -> AssignmentSummary:
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
        out_path.write_text(json.dumps(summary.get_raw().model_dump()))
        return summary

    @abstractmethod
    def metadata(self) -> AssignmentMetadata:
        pass

    @abstractmethod
    def preprocess(self) -> PreprocessorResults:
        pass

    @abstractmethod
    def build(self) -> ExecutableBuildResults:
        pass

    @abstractmethod
    def run_tests(self) -> RuntimeResults:
        pass
