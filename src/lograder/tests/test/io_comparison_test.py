import shlex
import subprocess
from pathlib import Path
from typing import Callable, List, Optional, Sequence

from ...constants import Constants
from ..common.exceptions import TestNotRunError, TestTargetNotSpecifiedError
from .analytics import (
    CallgrindSummary,
    ExecutionTimeSummary,
    ValgrindLeakSummary,
    ValgrindWarningSummary,
    callgrind,
    usr_time,
    valgrind,
)
from .interface import TestInterface


class ComparisonTest(TestInterface):
    def __init__(
        self,
        name: str,
        input: str,
        expected_output: str,
        flags: Optional[Sequence[str | Path]] = None,
        weight: float = 1.0,
    ):
        if flags is None:
            flags = []

        self._name: str = name
        self._saved_executable: Optional[List[str | Path]] = None
        self._saved_flags: List[str | Path] = list(flags)

        self._cached_warnings: Optional[ValgrindWarningSummary] = None
        self._cached_leaks: Optional[ValgrindLeakSummary] = None
        self._cached_calls: Optional[List[CallgrindSummary]] = None
        self._cached_times: Optional[ExecutionTimeSummary] = None

        self._input: str = input
        self._expected_output: str = expected_output
        self._actual_output: Optional[str] = None
        self._error: Optional[str] = None

        self._weight: float = weight

    def set_target(self, executable: List[str | Path]):
        self._saved_executable = executable

    def set_flags(self, flags: List[str | Path]):
        self._saved_flags = flags

    def is_correct(self) -> bool:
        return self.get_actual_output().strip() == self.get_expected_output().strip()

    def run(
        self, wrap_args: bool = False, working_directory: Optional[Path] = None
    ) -> None:
        cmd = self.get_cmd(wrap_args=wrap_args, working_directory=working_directory)
        if cmd is None:
            raise TestTargetNotSpecifiedError(self.get_name())
        self.is_correct_cmd(cmd)

    def is_correct_cmd(self, cmd: List[str | Path]) -> bool:
        self.set_target([cmd[0]])
        self.set_flags(cmd[1:])
        result = subprocess.run(
            cmd,
            input=self.get_input(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=Constants.DEFAULT_EXECUTABLE_TIMEOUT,
        )
        self._actual_output = result.stdout
        self._error = result.stderr
        return self.is_correct()

    def get_error(self) -> str:
        if self._error is None:
            raise TestNotRunError(self.get_name())
        return self._error

    def is_correct_str(self, actual_output: str) -> bool:
        self._actual_output = actual_output
        return self.is_correct()

    def is_correct_func(self, func: Callable[[str], str]):
        self._actual_output = func(self.get_input())
        return self.is_correct()

    def get_warnings(self) -> Optional[ValgrindWarningSummary]:
        cmd = self.get_cmd()
        if cmd is None:
            raise TestNotRunError(self.get_name())
        if self._cached_warnings is None:
            self._cached_leaks, self._cached_warnings = valgrind(cmd, self.get_input())
        return self._cached_warnings

    def get_cmd(
        self, wrap_args: bool = False, working_directory: Optional[Path] = None
    ) -> Optional[List[Path | str]]:
        if self._saved_executable is None:
            return None

        cd: List[str | Path] = []
        if working_directory is not None:
            cd = ["cd", working_directory, "&&"]

        flags: Sequence[str | Path] = self._saved_flags
        if wrap_args:
            flags = [
                f'ARGS="{shlex.join([str(arg.resolve()) if isinstance(arg, Path) else arg for arg in self._saved_flags])}"'
            ]
        return cd + self._saved_executable + list(flags)

    def get_execution_time(self) -> Optional[ExecutionTimeSummary]:
        cmd = self.get_cmd()
        if cmd is None:
            raise TestNotRunError(self.get_name())
        if self._cached_times is None:
            self._cached_times = usr_time(cmd, self.get_input())
        return self._cached_times

    def get_calls(self) -> Optional[List[CallgrindSummary]]:
        cmd = self.get_cmd()
        if cmd is None:
            raise TestNotRunError(self.get_name())
        if self._cached_calls is None:
            self._cached_calls = callgrind(cmd, self.get_input())
        return self._cached_calls

    def get_leaks(self) -> Optional[ValgrindLeakSummary]:
        cmd = self.get_cmd()
        if cmd is None:
            raise TestNotRunError(self.get_name())
        if self._cached_warnings is None:
            self._cached_leaks, self._cached_warnings = valgrind(cmd, self.get_input())
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
