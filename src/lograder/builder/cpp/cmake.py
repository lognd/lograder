import re
import sys
from pathlib import Path
from typing import List, Optional

from ...common.types import FilePath
from ...common.utils import random_name
from ..common.assignment import BuilderOutput, PreprocessorOutput
from ..common.builder_interface import (
    BuilderInterface,
    BuilderResults,
    CxxTestRunner,
    PreprocessorResults,
)
from ..common.exceptions import (
    CMakeListsNotFoundError,
)
from ..common.file_operations import bfs_walk, is_cmake_file, is_valid_target, run_cmd


class CMakeBuilder(CxxTestRunner, BuilderInterface):
    TARGET_PATTERN = re.compile(r"^\.\.\.\s+([a-zA-Z0-9_\-.]+)", re.MULTILINE)

    def __init__(self, project_root: FilePath):
        super().__init__()
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

    def get_project_root(self) -> Path:
        return self._project_root

    def get_build_directory(self) -> Path:
        return self._build_directory

    def get_cmake_file(self) -> Path:
        if self._cmake_file is None:
            raise CMakeListsNotFoundError
        return self._cmake_file

    def get_working_directory(self) -> Path:
        return self._working_directory

    def get_executable_path(self) -> Path:
        if self._executable_path is None:
            self.set_build_code(1)
            # raise CMakeExecutableNotFoundError(
            #     self.get_working_directory() / "CMakeLists.txt"
            # )
            return Path("/")
        return self._executable_path

    def preprocess(self) -> PreprocessorResults:
        return PreprocessorResults(
            PreprocessorOutput(
                commands=[],
                stdout=[],
                stderr=[],
            )
        )

    def find_executable(self, target: str) -> Optional[Path]:
        build_dir = Path(self.get_build_directory())
        candidates = [
            build_dir / "Debug" / f"{target}.exe",
            build_dir / "Release" / f"{target}.exe",
            build_dir / "Debug" / target,
            build_dir / "Release" / target,
            build_dir / f"{target}.exe",
            build_dir / target,
        ]

        # 1. Check common defaults first
        for path in candidates:
            if path.is_file():
                return path

        # 2. Fallback: scan build dir recursively for matching file
        for path in build_dir.rglob("*"):
            if path.is_file():
                if path.name == target or path.name == f"{target}.exe":
                    return path

        return None

    def build(self) -> BuilderResults:
        commands: List[List[str | Path]] = []
        stdout: List[str] = []
        stderr: List[str] = []

        cmd: List[str | Path] = [
            "cmake",
            "-S",
            self.get_working_directory(),
            "-B",
            self.get_build_directory(),
        ]
        if sys.platform.startswith("win"):
            cmd += ["-G", "MinGW Makefiles"]

        result = run_cmd(cmd, commands=commands, stdout=stdout, stderr=stderr)
        if result.returncode != 0:
            self.set_build_code(1)
            return BuilderResults(
                executable="Build failed...",
                output=BuilderOutput(
                    commands=commands, stdout=stdout, stderr=stderr, build_type="cmake"
                ),
            )

        cmd = [
            "cmake",
            "--build",
            self.get_build_directory(),
            "--target",
            "help",
        ]
        result = run_cmd(cmd, commands=commands, stdout=stdout, stderr=stderr)
        if result.returncode != 0:
            self.set_build_code(1)
            return BuilderResults(
                executable="Build failed...",
                output=BuilderOutput(
                    commands=commands, stdout=stdout, stderr=stderr, build_type="cmake"
                ),
            )
        targets = self.TARGET_PATTERN.findall(stdout[-1])
        if "main" in targets:
            target = "main"
        elif "build" in targets:
            target = "build"
        elif "demo" in targets:
            target = "demo"
        else:
            valid_targets = [target for target in targets if is_valid_target(target)]
            if not valid_targets:
                self.set_build_code(1)
                return BuilderResults(
                    executable="Build failed...",
                    output=BuilderOutput(
                        commands=commands,
                        stdout=stdout,
                        stderr=stderr,
                        build_type="cmake",
                    ),
                )
                # raise CMakeTargetNotFoundError(
                #     targets, self.get_working_directory() / "CMakeLists.txt"
                # )
            target = valid_targets[0]

        cmd = [
            "cmake",
            "--build",
            self.get_build_directory(),
            "--target",
            target,
            "--", "-s", "--no-print-directory"
        ]
        result = run_cmd(cmd, commands=commands, stdout=stdout, stderr=stderr)
        if result.returncode != 0:
            self.set_build_code(1)
            return BuilderResults(
                executable="Build failed...",
                output=BuilderOutput(
                    commands=commands, stdout=stdout, stderr=stderr, build_type="cmake"
                ),
            )

        self._executable_path = self.find_executable(target)
        if self._executable_path is None:
            self.set_build_code(1)
            return BuilderResults(
                executable="Build failed...",
                output=BuilderOutput(
                    commands=commands, stdout=stdout, stderr=stderr, build_type="cmake"
                ),
            )

        return BuilderResults(
            executable=self.get_executable_path(),
            output=BuilderOutput(
                commands=commands, stdout=stdout, stderr=stderr, build_type="cmake"
            ),
        )
