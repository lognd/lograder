from __future__ import annotations

import shlex
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

from ...os.cmd import run_cmd
from .interfaces.output_test import OutputTestInterface

if TYPE_CHECKING:
    from ...types import Command
    from ..builders.interfaces.builder import BuilderInterface


class CLIOutputTest(OutputTestInterface):
    def __init__(self):
        super().__init__()
        self._name: Optional[str] = None
        self._builder: Optional[BuilderInterface] = None

        self._args: Command = []
        self._wrap_args: bool = False
        self._working_dir: Optional[Path] = None

        self._expected_stdout: Optional[str] = None
        self._actual_stdout: Optional[str] = None
        self._stderr: Optional[str] = None

    @classmethod
    def make(
        cls,
        name: str,
        builder: BuilderInterface,
        stdin: str,
        expected_stdout: str,
        args: Optional[Command] = None,
        working_dir: Optional[Path] = None,
        wrap_args: bool = False,
    ) -> CLIOutputTest:
        test = cls()

        test.set_name(name)
        test.set_builder(builder)
        test.set_stdin(stdin)
        test.set_expected_stdout(expected_stdout)

        test.set_wrap_args(wrap_args)
        if working_dir is not None:
            test.set_working_dir(working_dir)
        if args is not None:
            test.set_args(args)

        return test

    def set_working_dir(self, path: Path):
        self._working_dir = path

    def get_working_dir(self) -> Optional[Path]:
        return self._working_dir

    def set_wrap_args(self, wrap: bool = True) -> None:
        self._wrap_args = wrap

    def get_wrap_args(self) -> bool:
        return self._wrap_args

    def set_args(self, args: Command) -> None:
        self._args = args

    def get_args(self) -> Command:
        return self._args

    def set_builder(self, builder: BuilderInterface) -> None:
        self._builder = builder

    def get_builder(self) -> BuilderInterface:
        assert self._builder is not None
        return self._builder

    def set_name(self, name: str):
        self._name = name

    def _run_test(self) -> Tuple[int, Command]:
        builder = self.get_builder()
        builder.build()

        args = self.get_args()
        if self.get_wrap_args():
            args = [
                f'ARGS="{shlex.join([str(arg.resolve()) if isinstance(arg, Path) else arg for arg in self.get_args()])}"'
            ]
        command = builder.get_start_command() + args

        _tmp_stdout: List[str] = []
        _tmp_stderr: List[str] = []
        result = run_cmd(command, [], _tmp_stdout, _tmp_stderr, self.get_working_dir())

        self._actual_stdout = _tmp_stdout.pop()
        self._stderr = _tmp_stderr.pop()

        return result.returncode, command

    def set_expected_stdout(self, expected_stdout: str):
        self._expected_stdout = expected_stdout

    def get_expected_output(self) -> str:
        assert self._expected_stdout is not None
        return self._expected_stdout

    def get_actual_output(self) -> str:
        if self._actual_stdout is None:
            _, _ = self._run_test()
        assert self._actual_stdout is not None
        return self._actual_stdout

    def get_error(self) -> str:
        if self._stderr is None:
            _, _ = self._run_test()
        assert self._stderr is not None
        return self._stderr

    def get_score(self) -> float:
        if self.get_builder().get_build_error():
            if not self._run:
                self.add_to_output("build-fail", {})
                self._run = True
            return 0.0
        return OutputTestInterface.get_score(self)

    def get_name(self) -> str:
        assert self._name is not None
        return self._name
