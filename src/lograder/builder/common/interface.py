from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
import time
import subprocess

from .exceptions import CxxExecutableTimeoutError, CxxExecutableRuntimeError
from ...tests.test import ComparisonTest
from ..constants import DEFAULT_EXECUTION_TIMEOUT

class ResultInterface(ABC):
    @abstractmethod
    def get_successful(self) -> bool: ...

class ComparisonResult(ResultInterface):
    def __init__(self, successful: bool, time_elapsed: float):
        self._successful = successful  # Kind of stupid, but eh.
        self._time_elapsed = time_elapsed

    def get_successful(self) -> bool:
        return self._successful

class BuilderInterface(ABC):
    @abstractmethod
    def preprocess(self): ...
    @abstractmethod
    def build(self): ...
    @abstractmethod
    def run(self, test: ComparisonTest): ...

class CxxRuntimeInterface(ABC):
    @abstractmethod
    def get_arguments(self) -> List[str]:
        ...

    @abstractmethod
    def get_executable_path(self) -> Path:
        ...

    def run(self, test: ComparisonTest) -> ComparisonResult:
        start_time = time.perf_counter()
        try:
            proc = subprocess.run([self.get_executable(), *self.get_arguments()], input=test.get_input(), capture_output=True, timeout=DEFAULT_EXECUTION_TIMEOUT)
            duration = start_time - time.perf_counter()
        except subprocess.TimeoutExpired as e:
            raise CxxExecutableTimeoutError() from e

        if proc.returncode != 0:
            raise CxxExecutableRuntimeError(proc)

        return ComparisonResult(test.is_correct_str(proc.stdout), duration)


