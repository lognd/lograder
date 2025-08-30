from typing import Callable, Optional, List
import subprocess

from ..common.exceptions import TestNotRunError
from .analytics import MemoryLossSummary, WarningSummary, TimeSummary, CallSummary
from .interface import TestInterface


class ComparisonTest(TestInterface):
    def __init__(
        self, name: str, input: str, expected_output: str, weight: float = 1.0
    ):
        self._name: str = name
        self._saved_cmd: Optional[List[str]] = None
        self._input: str = input
        self._expected_output: str = expected_output
        self._actual_output: Optional[str] = None
        self._weight: float = weight

    def set_cmd(self, cmd: List[str]):
        self._saved_cmd: List[str] = cmd

    def is_correct(self) -> bool:
        return self.get_actual_output() == self._expected_output

    def is_correct_cmd(self, cmd: List[str]) -> bool:
        self.set_cmd(cmd)
        self._actual_output = subprocess.run(
            cmd,
            stdin=self.get_input(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def is_correct_str(self, actual_output: str) -> bool:
        self._actual_output = actual_output
        return self.is_correct()

    def is_correct_func(self, func: Callable[[str], str]):
        self._actual_output = func(self.get_input())
        return self.is_correct()

    def get_warnings(self) -> Optional[WarningSummary]:
        return None

    def get_execution_time(self) -> Optional[TimeSummary]:
        return None

    def get_calls(self) -> Optional[List[CallSummary]]:
        return None

    def get_leaks(self) -> Optional[MemoryLossSummary]:
        return None

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

    def get_weight(self) -> float:
        return self._weight
