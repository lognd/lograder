import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import shutil
import xml.etree.ElementTree as ET

from ..common.exceptions import Catch2MainNotFoundError
from ...common.types import FilePath
from ...common.utils import random_name
from ...static import LograderBasicConfig
from ..common import (
    CLIBuilder,
    DispatcherInterface,
    ExecutableBuildResults,
    ExecutableRunner,
    PreprocessorInterface,
    PreprocessorResults,
    RuntimeResults,
    TrivialPreprocessor,
)
from ..common.file_operations import bfs_walk, is_cxx_source_file, is_catch2_file
from ..common.types import AssignmentMetadata


class Catch2Dispatcher(CLIBuilder, ExecutableRunner, DispatcherInterface):
    def __init__(
        self,
        *,
        assignment_name: str,
        assignment_authors: List[str],
        assignment_description: str,
        assignment_due_date: datetime,
        catch2_directory: FilePath,
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

        self._catch2_root: Path = Path(catch2_directory).resolve()
        self._catch2_mains: List[Path] = []
        self._catch2_parent_directories: List[Path] = []
        self._catch2_files: List[Path] = []

        for file in bfs_walk(self._catch2_root):
            if is_catch2_file(file):
                self._catch2_mains.append(file.resolve())
                self._catch2_parent_directories.append(file.parent)
                continue
            if is_cxx_source_file(file):
                for directory in file.resolve().parents:
                    if directory == self._catch2_root:
                        break
                    if directory in self._catch2_parent_directories:
                        continue
                self._catch2_files.append(file)
        if not self._catch2_mains:
            raise Catch2MainNotFoundError(catch2_directory)

        self._project_root: Path = Path(project_root)
        self._build_directory: Optional[Path] = None

        self._executables: List[Path] = []
        self._preprocessor = preprocessor

    def build(self) -> ExecutableBuildResults:
        output = self.get_build_error_output()
        for catch2_main, catch2_project in zip(self._catch2_mains, self._catch2_parent_directories):
            self._build_directory = self._project_root.parent / random_name()

            for file in self._catch2_files:  # Copy all files detected to be non-specific
                rel_path = file.relative_to(self._catch2_root)
                dest_path = self._build_directory / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, dest_path)

            for file in bfs_walk(self._project_root):  # Copy all student files
                rel_path = file.relative_to(self._project_root)
                des_path = self._build_directory / rel_path
                des_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, des_path)

            for file in bfs_walk(catch2_project):
                if file.resolve() in self._catch2_mains:  # Don't copy if it's another main
                    continue
                rel_path = file.relative_to(self._catch2_root)
                des_path = self._build_directory / rel_path
                des_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, des_path)

            source_files = []
            for file in bfs_walk(self._build_directory):
                if is_cxx_source_file(file):
                    source_files.append(file)

            executable_path: Path = self.get_executable_path()
            cmd: List[str | Path] = [
                "g++",
                *LograderBasicConfig.DEFAULT_CXX_COMPILATION_FLAGS,
                f"-std={LograderBasicConfig.DEFAULT_CXX_STANDARD}",
                "-o",
                executable_path,
                *source_files,
            ]
            output = self.run_cmd(cmd)
            if self.is_build_error():
                return self.get_build_error_output()
            self._executables.append(executable_path)

        return ExecutableBuildResults(
            executable=self.get_executable_path(), output=output
        )

    def get_build_directory(self) -> Path:
        return self._build_directory

    def get_project_root(self) -> Path:
        return self._project_root

    def get_executable_path(self) -> Path:
        executable_name = (
            self.get_build_directory() / (random_name() + ".exe")
            if sys.platform.startswith("win")
            else self.get_build_directory() / random_name()
        )
        return executable_name

    def metadata(self) -> AssignmentMetadata:
        return self._metadata

    def preprocess(self) -> PreprocessorResults:
        return self._preprocessor.preprocess()

    def get_executable(self) -> List[str | Path]:
        return [self.get_executable_path()]
