from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from .test import TestInterface

if TYPE_CHECKING:
    from ....types import StreamOutput

class OutputTestInterface(TestInterface, ABC):

    def __init__(self):
        super().__init__()
        self._run: bool = False
        self._stdin: str = ""

    def set_stdin(self, stdin: str) -> None:
        self._stdin = stdin

    def get_input(self) -> str:
        return self._stdin

    @abstractmethod
    def get_expected_output(self) -> str:
        pass

    @abstractmethod
    def get_actual_output(self) -> str:
        pass

    @abstractmethod
    def get_error(self) -> str:
        pass

    def get_score(self) -> float:
        input: StreamOutput = {"stream_contents": self.get_input()}
        expected: StreamOutput = {"stream_contents": self.get_expected_output()}
        actual: StreamOutput = {"stream_contents": self.get_actual_output()}
        error: StreamOutput = {"stream_contents": self.get_error()}

        if not self._run:  # stop duplicate appending
            self.add_to_output("stdin", input)
            self.add_to_output("expected-stdout", expected)
            self.add_to_output("actual-stdout", actual)
            self.add_to_output("stderr", error)
            self._run = True

        return (expected["stream_contents"] == actual["stream_contents"]) * self.get_max_score() * self.get_weight()
