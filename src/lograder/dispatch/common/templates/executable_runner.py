from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
from ..interface import RunnerInterface, RuntimePrepResults
from ....tests.test.interface import ExecutableTestInterface
from ....tests.registry import TestRegistry

class ExecutableRunner(RunnerInterface):
    @abstractmethod
    def get_executable(self) -> List[str | Path]:
        pass

    def prep_tests(self) -> RuntimePrepResults:
        tests: List[ExecutableTestInterface] = []
        for test in TestRegistry.iterate():
            if isinstance(test, ExecutableTestInterface):
                test.set_target(self.get_executable())
            else:
                tests.append(test)
        return RuntimePrepResults(tests)
