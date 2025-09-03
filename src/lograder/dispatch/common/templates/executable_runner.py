from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from ....tests.registry import TestRegistry
from ....tests.test.interface import ExecutableTestInterface
from ..interface import RunnerInterface, RuntimePrepResults


class ExecutableRunner(RunnerInterface, ABC):
    @abstractmethod
    def get_executable(self) -> List[str | Path]:
        pass

    def prep_tests(self) -> RuntimePrepResults:
        tests: List[ExecutableTestInterface] = []
        for test in TestRegistry.iterate():
            if isinstance(test, ExecutableTestInterface):
                test.set_target(self.get_executable())
                tests.append(test)
            else:
                raise TypeError
        return RuntimePrepResults(tests)
