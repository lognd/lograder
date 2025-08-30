import subprocess
from typing import Callable, List, Optional

from ...constants import DEFAULT_PROJECT_TIMEOUT
from ..common.exceptions import TestNotRunError
from .analytics import CallgrindSummary, ValgrindLeakSummary, ExecutionTimeSummary, ValgrindWarningSummary, usr_time, valgrind, callgrind
from .interface import TestInterface


class ComparisonTest(TestInterface):
    def __init__(
        self, name: str, input: str, expected_output: str, weight: float = 1.0
    ):
        self._name: str = name
        self._saved_cmd: Optional[List[str]] = None

        self._cached_warnings: Optional[ValgrindWarningSummary] = None
        self._cached_leaks: Optional[ValgrindLeakSummary] = None
        self._cached_calls: Optional[List[CallgrindSummary]] = None
        self._cached_times: Optional[ExecutionTimeSummary] = None

        self._input: str = input
        self._expected_output: str = expected_output
        self._actual_output: Optional[str] = None
        self._error: Optional[str] = None

        self._weight: float = weight

    def set_cmd(self, cmd: List[str]):
        self._saved_cmd: List[str] = cmd

    def is_correct(self) -> bool:
        return self.get_actual_output().strip() == self._expected_output.strip()

    def is_correct_cmd(self, cmd: List[str]) -> bool:
        self.set_cmd(cmd)
        result = subprocess.run(
            cmd,
            input=self.get_input(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=DEFAULT_PROJECT_TIMEOUT
        )
        self._actual_output = result.stdout.decode()
        self._error = result.stderr.decode()
        return self.is_correct()

    def get_error(self) -> str:
        return self._error

    def is_correct_str(self, actual_output: str) -> bool:
        self._actual_output = actual_output
        return self.is_correct()

    def is_correct_func(self, func: Callable[[str], str]):
        self._actual_output = func(self.get_input())
        return self.is_correct()

    def get_warnings(self) -> Optional[ValgrindWarningSummary]:
        if self.get_cmd() is None:
            return None
        if self._cached_warnings is None:
            self._cached_leaks, self._cached_warnings = valgrind(self.get_cmd(), self.get_input())
        return self._cached_warnings

    def get_cmd(self) -> Optional[List[str]]:
        return self._saved_cmd

    def get_execution_time(self) -> Optional[ExecutionTimeSummary]:
        if self.get_cmd() is None:
            return None
        if self._cached_times is None:
            self._cached_times = usr_time(self.get_cmd(), self.get_input())
        return self._cached_times

    def get_calls(self) -> Optional[List[CallgrindSummary]]:
        if self.get_cmd() is None:
            return None
        if self._cached_calls is None:
            self._cached_calls = callgrind(self.get_cmd(), self.get_input())
        return self._cached_calls

    def get_leaks(self) -> Optional[ValgrindLeakSummary]:
        if self.get_cmd() is None:
            return None
        if self._cached_warnings is None:
            self._cached_leaks, self._cached_warnings = valgrind(self.get_cmd(), self.get_input())
        return self._cached_leaks

    def get_name(self) -> str:
        return self._name

    def get_successful(self) -> bool:
        return self.is_correct()

    def get_input(self) -> str:
        return self._input

    def get_expected_output(self) -> str:
        return self._expected_output

    def get_actual_output(self) -> str:
        if self._actual_output is None:
            raise TestNotRunError(self.get_name())
        return self._actual_output

    def get_penalty(self) -> float:
        leaks = self.get_leaks()
        multiplier = 1.0
        if leaks is not None:
            if not leaks.is_safe:
                multiplier *= 0.8
        return multiplier

    def get_weight(self) -> float:
        return self._weight
