from pathlib import Path
from typing import List, Optional

from datetime import datetime

from ..common.interface import BuildResults
from ...common.types import FilePath
from ...tests.registry import TestRegistry
from ..common.assignment import BuilderOutput, PreprocessorOutput, AssignmentMetadata
from ...static import LograderBasicConfig
from ..common import (
    DispatcherInterface,
    ExecutableBuildResults,
    PreprocessorResults,
    RuntimeResults,
    CLIBuilder,
    ExecutableRunner,
    PreprocessorInterface,
    TrivialPreprocessor
)
from ..common.exceptions import MakefileNotFoundError
from ..common.file_operations import (
    bfs_walk,
    is_makefile_file,
    is_makefile_target,
    run_cmd
)


class MakefileDispatcher(ExecutableRunner, CLIBuilder, DispatcherInterface):
    def get_executable(self) -> List[str | Path]:
        return ["make", "-s", "run"]

    def build(self) -> BuildResults:
        cmd: List[str | Path] = ["make", "-s"]
        output = self.run_cmd(cmd, working_directory=self.get_working_directory())
        if self.is_build_error():
            return self.get_build_error_output()

        return ExecutableBuildResults(
            executable=self.get_makefile(),
            output=output
        )

    def metadata(self) -> AssignmentMetadata:
        return self._metadata

    def preprocess(self) -> PreprocessorResults:
        return self._preprocessor.preprocess()

    def run_tests(self) -> RuntimeResults:
        return super(ExecutableRunner, self).run()

    def __init__(
            self, *,
            assignment_name: str,
            assignment_authors: List[str],
            assignment_description: str,
            assignment_due_date: datetime,
            project_root: Path = LograderBasicConfig.DEFAULT_SUBMISSION_PATH,
            preprocessor: PreprocessorInterface = TrivialPreprocessor()
    ):
        super().__init__()

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
