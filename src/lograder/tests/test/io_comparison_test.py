import shlex
import subprocess
from pathlib import Path
from typing import Callable, List, Optional, Sequence

from . import ExecutableTestInterface
from ...dispatch.common.file_operations import do_process
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


class ExecutableOutputComparisonTest(ExecutableTestInterface):
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
        self._force_success: Optional[bool] = None  # I <3 ternary "boolean"

    def set_target(self, executable: List[str | Path]):
        self._saved_executable = executable

    def set_flags(self, flags: List[str | Path]):
        self._saved_flags = flags

    def override_output(self, stderr: str, stdout: str = None):
        self._error = stderr
        self._actual_output = stdout

    def force_successful(self) -> None:
        self._force_success = True

    def force_unsuccessful(self) -> None:
        self._force_success = False

    def run(
        self, wrap_args: bool = False, working_directory: Optional[Path] = None
    ) -> None:
        if self._force_success is not None:
            return  # no need to run test if its been overridden.

        cmd = self.get_cmd(wrap_args=wrap_args)
        if cmd is None:
            raise TestTargetNotSpecifiedError(self.get_name())

        self.set_target([cmd[0]])
        self.set_flags(cmd[1:])
        result = do_process(
            cmd,
            input=self.get_input(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=Constants.DEFAULT_EXECUTABLE_TIMEOUT,
            cwd=working_directory,
        )
        self._actual_output = result.stdout
        self._error = result.stderr

    def _assert_executed(self):
        if self._error is None or self._actual_output is None:
            raise TestNotRunError(self.get_name())

    def get_error(self) -> str:
        self._assert_executed()
        return self._error

    def get_warnings(self) -> Optional[ValgrindWarningSummary]:
        cmd = self.get_cmd()
        if cmd is None:
            raise TestNotRunError(self.get_name())
        if self._cached_warnings is None:
            self._cached_leaks, self._cached_warnings = valgrind(cmd, self.get_input())
        return self._cached_warnings

    def get_cmd(self, wrap_args: bool = False) -> Optional[List[Path | str]]:
        if self._saved_executable is None:
            return None

        flags: Sequence[str | Path] = self._saved_flags
        if wrap_args:
            flags = [
                f'ARGS="{shlex.join([str(arg.resolve()) if isinstance(arg, Path) else arg for arg in self._saved_flags])}"'
            ]
        return self._saved_executable + list(flags)

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
        if self._force_success is not None:
            return self._force_success
        actual_output = self.get_actual_output()
        return actual_output.strip() == self.get_expected_output().strip()

    def get_input(self) -> str:
        return self._input

    def get_expected_output(self) -> str:
        return self._expected_output

    def get_actual_output(self) -> Optional[str]:
        self._assert_executed()
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
