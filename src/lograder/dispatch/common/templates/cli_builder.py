from abc import ABC
from pathlib import Path
from typing import List, Optional

from ....static import LograderMessageConfig
from ..file_operations import run_cmd
from ..interface import BuilderInterface, BuilderOutput, ExecutableBuildResults
from ..types import ProjectType


class CLIBuilder(BuilderInterface, ABC):
    def __init__(self, build_type: ProjectType):
        super().__init__()
        self._commands: List[List[str | Path]] = []
        self._stdout: List[str] = []
        self._stderr: List[str] = []
        self._build_type = build_type

    def get_commands(self) -> List[List[str | Path]]:
        return self._commands

    def get_build_type(self) -> ProjectType:
        return self._build_type

    def get_stdout(self) -> List[str]:
        return self._stdout

    def get_stderr(self) -> List[str]:
        return self._stderr

    def get_build_error_output(self) -> ExecutableBuildResults:
        return ExecutableBuildResults(
            executable=LograderMessageConfig.DEFAULT_BUILD_ERROR_EXECUTABLE_NAME,
            output=BuilderOutput(
                commands=self.get_commands(),
                stdout=self.get_stdout(),
                stderr=self.get_stderr(),
                project_type=self.get_build_type(),
            ),
        )

    def run_cmd(
        self, cmd: List[str | Path], working_directory: Optional[Path] = None
    ) -> BuilderOutput:
        result = run_cmd(
            cmd,
            commands=self._commands,
            stdout=self._stdout,
            stderr=self._stderr,
            working_directory=working_directory,
        )
        if result.returncode != 0:
            self.set_build_error(True)
        return BuilderOutput(
            commands=self._commands,
            stdout=self._stdout,
            stderr=self._stderr,
            project_type=self._build_type,
        )
