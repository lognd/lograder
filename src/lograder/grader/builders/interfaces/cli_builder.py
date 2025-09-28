from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ....os.cmd import run_cmd
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

    def run_cmd(
        self, cmd: List[str | Path], working_directory: Optional[Path] = None
    ) -> None:
        result = run_cmd(
            cmd,
            commands=self._commands,
            stdout=self._stdout,
            stderr=self._stderr,
            working_directory=working_directory,
        )
        if result.returncode != 0:
            self.set_build_error(True)
