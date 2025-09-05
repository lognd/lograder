from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ...static import LograderBasicConfig
from ..common.assignment import AssignmentMetadata
from ..common.exceptions import MakefileNotFoundError
from ..common.file_operations import (
    bfs_walk,
    is_makefile_file,
)
from ..common.interface import (
    DispatcherInterface,
    ExecutableBuildResults,
    PreprocessorInterface,
    PreprocessorResults,
    RuntimeResults,
)
from ..common.templates.cli_builder import CLIBuilder
from ..common.templates.executable_runner import ExecutableRunner
from ..common.templates.trivial import TrivialPreprocessor


class MakefileDispatcher(CLIBuilder, ExecutableRunner, DispatcherInterface):
    def get_executable(self) -> List[str | Path]:
        return ["make", "-s", "run"]

    def build(self) -> ExecutableBuildResults:
        cmd: List[str | Path] = ["make", "-s"]
        output = self.run_cmd(cmd, working_directory=self.get_working_directory())
        if self.is_build_error():
            return self.get_build_error_output()

        return ExecutableBuildResults(executable=self.get_makefile(), output=output)

    def metadata(self) -> AssignmentMetadata:
        return self._metadata

    def preprocess(self) -> PreprocessorResults:
        return self._preprocessor.preprocess()

    def run_tests(self) -> RuntimeResults:
        return self.run_tests_auto()

    def __init__(
        self,
        *,
        assignment_name: str,
        assignment_authors: List[str],
        assignment_description: str,
        assignment_due_date: datetime,
        project_root: Path = LograderBasicConfig.DEFAULT_SUBMISSION_PATH,
        preprocessor: PreprocessorInterface = TrivialPreprocessor(),
    ):
        super().__init__(build_type="makefile")

        self._metadata = AssignmentMetadata(
            assignment_name=assignment_name,
            assignment_authors=assignment_authors,
            assignment_description=assignment_description,
            assignment_due_date=assignment_due_date,
        )

        self._project_root: Path = Path(project_root)

        self._makefile: Optional[Path] = None
        for file in bfs_walk(self._project_root):
            if is_makefile_file(file):
                self._makefile = file
                break
        if self._makefile is None:
            raise MakefileNotFoundError
        self._working_directory: Path = self._makefile.parent

        self._preprocessor = preprocessor

        self.set_wrap_args()
        self.set_cwd(Path(self.get_working_directory()))

    def get_makefile(self):
        if self._makefile is None:
            raise MakefileNotFoundError
        return self._makefile

    def get_project_root(self) -> Path:
        return self._project_root

    def get_working_directory(self) -> Path:
        return self._working_directory
