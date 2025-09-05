import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ...common.utils import random_name
from ...static import LograderBasicConfig
from ..common.file_operations import bfs_walk, is_cxx_source_file
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
from ..common.types import AssignmentMetadata


class CxxSourceDispatcher(CLIBuilder, ExecutableRunner, DispatcherInterface):

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
        super().__init__(build_type="cmake")
        self._metadata = AssignmentMetadata(
            assignment_name=assignment_name,
            assignment_authors=assignment_authors,
            assignment_description=assignment_description,
            assignment_due_date=assignment_due_date,
        )

        self._project_root: Path = Path(project_root)
        self._build_directory: Path = self._project_root / "build"
        if not self._build_directory.exists():
            self._build_directory = self._project_root

        self._executable_path: Optional[Path] = None
        self._preprocessor = preprocessor

    def build(self) -> ExecutableBuildResults:
        source_files: List[Path] = []
        for file in bfs_walk(self._project_root):
            if is_cxx_source_file(file):
                source_files.append(file)

        cmd: List[str | Path] = [
            "g++",
            *LograderBasicConfig.DEFAULT_CXX_COMPILATION_FLAGS,
            f"-std={LograderBasicConfig.DEFAULT_CXX_STANDARD}",
            "-o",
            self.get_executable_path(),
            *source_files,
        ]
        output = self.run_cmd(cmd)
        if self.is_build_error():
            return self.get_build_error_output()

        return ExecutableBuildResults(
            executable=self.get_executable_path(), output=output
        )

    def get_build_directory(self) -> Path:
        return self._build_directory

    def get_project_root(self) -> Path:
        return self._project_root

    def get_executable_path(self) -> Path:
        if self._executable_path is not None:
            return self._executable_path
        while True:
            executable_name = (
                self.get_build_directory() / (random_name() + ".exe")
                if sys.platform.startswith("win")
                else self.get_build_directory() / random_name()
            )
            if not executable_name.exists():
                self._executable_path = executable_name
                return self._executable_path

    def metadata(self) -> AssignmentMetadata:
        return self._metadata

    def preprocess(self) -> PreprocessorResults:
        return self._preprocessor.preprocess()

    def run_tests(self) -> RuntimeResults:
        return self.run_tests_auto()

    def get_executable(self) -> List[str | Path]:
        return [self.get_executable_path()]
