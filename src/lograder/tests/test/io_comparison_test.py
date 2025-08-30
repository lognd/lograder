from time import perf_counter
from typing import Callable, Optional

from ..common.exceptions import TestNotRunError
from .interface import TestInterface


class ComparisonTest(TestInterface):
    def __init__(
        self, name: str, input: str, expected_output: str, weight: float = 1.0
    ):
        self._name: str = name
        self._input: str = input
        self._expected_output: str = expected_output
        self._actual_output: Optional[str] = None
        self._weight: float = weight

        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    def is_correct(self) -> bool:
        return self.get_actual_output() == self._expected_output

    def is_correct_str(self, actual_output: str) -> bool:
        self._actual_output = actual_output
        return self.is_correct()

    def is_correct_func(self, func: Callable[[str], str]):
        self._start_time = perf_counter()
        self._actual_output = func(self.get_input())
        self._end_time = perf_counter()
        return self.is_correct()

    def get_name(self) -> str:
        return self._name

    def get_execution_time(self) -> Optional[float]:
        if self._start_time is None or self._end_time is None:
            return None
        return self._end_time - self._start_time

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
