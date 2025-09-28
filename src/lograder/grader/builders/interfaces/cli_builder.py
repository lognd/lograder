from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from ...submission_handler import SubmissionHandler

if TYPE_CHECKING:
    from ....os.cmd import run_cmd
    from ....types import Command, CommandOutput, StreamOutput
    from ..interfaces.builder import BuilderInterface


class CLIBuilderInterface(BuilderInterface, ABC):
    def __init__(self):
        super().__init__()

        self._commands: List[List[str | Path]] = []
        self._stdout: List[str] = []
        self._stderr: List[str] = []

    def get_commands(self) -> List[List[str | Path]]:
        return self._commands

    def get_stdout(self) -> List[str]:
        return self._stdout

    def get_stderr(self) -> List[str]:
        return self._stderr

    def run_cmd(self, cmd: Command, working_directory: Optional[Path] = None) -> None:
        result = run_cmd(
            cmd,
            commands=self._commands,
            stdout=self._stdout,
            stderr=self._stderr,
            working_directory=working_directory,
        )
        SubmissionHandler.add_output(
            "command",
            CommandOutput(
                command=self._commands[-1],
                exit_code=result.returncode,
            ),
        )
        SubmissionHandler.add_output(
            "stdout", StreamOutput(stream_contents=self._stdout[-1])
        )
        SubmissionHandler.add_output(
            "stderr", StreamOutput(stream_contents=self._stderr[-1])
        )
        if result.returncode != 0:
            self.set_build_error(True)
