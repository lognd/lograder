import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ...common.utils import random_name
from ...static import LograderBasicConfig
from ..common.exceptions import (
    CMakeListsNotFoundError,
)
from ..common.file_operations import bfs_walk, is_cmake_file, is_valid_target
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


class CMakeDispatcher(CLIBuilder, ExecutableRunner, DispatcherInterface):

    # For finding student project target in `cmake --build <...> --target help`
    TARGET_PATTERN = re.compile(r"^\.\.\.\s+([a-zA-Z0-9_\-.]+)", re.MULTILINE)

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
        self._build_directory: Path = self._project_root / f"build-{random_name()}"

        self._cmake_file: Optional[Path] = None
        for file in bfs_walk(self._project_root):
            if is_cmake_file(file):
                self._cmake_file = file
                break
        if self._cmake_file is None:
            raise CMakeListsNotFoundError

        self._working_directory: Path = self._cmake_file.parent
        self._cmake_target: Optional[str] = None
        self._executable_path: Optional[Path] = None

        self._preprocessor = preprocessor
        self._target: Optional[str] = None

    def get_project_root(self) -> Path:
        return self._project_root

    def get_build_directory(self) -> Path:
        return self._build_directory

    def get_working_directory(self) -> Path:
        return self._working_directory

    def get_executable(self) -> List[str | Path]:
        assert self._target is not None  # mypy
        try:
            return [self.find_executable(self._target)]
        except FileNotFoundError:
            return []

    def find_executable(self, target: str) -> Path:
        build_dir = self.get_build_directory()
        candidates = [
            build_dir / "Debug" / f"{target}.exe",
            build_dir / "Release" / f"{target}.exe",
            build_dir / "Debug" / target,
            build_dir / "Release" / target,
            build_dir / f"{target}.exe",
            build_dir / target,
        ]

        for path in candidates:
            if path.is_file():
                return path

        for path in build_dir.rglob("*"):
            if path.is_file():
                if path.name == target or path.name == f"{target}.exe":
                    return path

        raise FileNotFoundError

    def build(self) -> ExecutableBuildResults:
        cmd: List[str | Path] = [
            "cmake",
            "-S",
            self.get_working_directory(),
            "-B",
            self.get_build_directory(),
        ]
        if sys.platform.startswith("win"):
            cmd += ["-G", "MinGW Makefiles"]

        self.run_cmd(cmd)
        if self.is_build_error():
            return self.get_build_error_output()

        cmd = ["cmake", "--build", self.get_build_directory(), "--target", "help"]
        output = self.run_cmd(cmd)
        if self.is_build_error():
            return self.get_build_error_output()

        targets = self.TARGET_PATTERN.findall(output.stdout or "")
        if "main" in targets:
            self._target = "main"
        elif "build" in targets:
            self._target = "build"
        elif "demo" in targets:
            self._target = "demo"
        else:
            valid_targets = [target for target in targets if is_valid_target(target)]
            if not valid_targets:
                self.set_build_error(True)
                return self.get_build_error_output()
            self._target = valid_targets[0]

        cmd = [
            "cmake",
            *LograderBasicConfig.DEFAULT_CMAKE_COMPILATION_FLAGS,
            "--build",
            self.get_build_directory(),
            "--target",
            self._target,
            "--",
            "-s",
            "--no-print-directory",
        ]
        output = self.run_cmd(cmd)
        if self.is_build_error():
            return self.get_build_error_output()

        try:
            self._executable_path = self.find_executable(self._target)
        except FileNotFoundError:
            self.set_build_error(True)
            return self.get_build_error_output()

        assert self._executable_path is not None  # mypy
        return ExecutableBuildResults(
            executable=self._executable_path.resolve(), output=output
        )

    def metadata(self) -> AssignmentMetadata:
        return self._metadata

    def preprocess(self) -> PreprocessorResults:
        return self._preprocessor.preprocess()

    def run_tests(self) -> RuntimeResults:
        return self.run_tests_auto()
