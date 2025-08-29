from typing import Callable

from .interface import TestInterface


class ComparisonTest(TestInterface):
    def __init__(
        self, name: str, input: str, expected_output: str, weight: float = 1.0
    ):
        self._name: str = name
        self._input: str = input
        self._expected_output: str = expected_output
        self._weight: float = weight

    def is_correct_str(self, actual_output: str) -> bool:
        return actual_output.strip() == self.get_expected_output().strip()

    def is_correct_func(self, func: Callable[[str], str]):
        return self.is_correct_str(func(self.get_input()))

    def get_name(self) -> str:
        return self._name

    def get_input(self) -> str:
        return self._input

    def get_expected_output(self) -> str:
        return self._expected_output

    def get_weight(self) -> float:
        return self._weight
