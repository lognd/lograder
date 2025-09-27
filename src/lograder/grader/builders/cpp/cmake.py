import re
from pathlib import Path
from typing import List, Optional

from ....data.cxx import CxxConfig
from ....data.paths import PathConfig
from ....os.file import bfs_walk, is_cmake_file, is_valid_target
from ....random_utils import random_name
from ....types import Command
from ..interfaces.cli_builder import CLIBuilderInterface


class CMakeBuilder(CLIBuilderInterface):

    TARGET_PATTERN = re.compile(r"^\.\.\.\s+([a-zA-Z0-9_\-.]+)", re.MULTILINE)

    def __init__(self):
        super().__init__()
        self._executable_path: Optional[Path] = None
        self._project_root: Path = Path(PathConfig.DEFAULT_SUBMISSION_PATH)

        self._build_directory: Path = self._project_root / f"build-{random_name()}"
        self._working_directory: Optional[Path] = None
        self._cmake_file: Optional[Path] = None
        self._target: Optional[str] = None

    def set_working_directory(self, path: Path) -> None:
        self._working_directory = path

    def get_working_directory(self) -> Path:
        assert self._working_directory is not None
        return self._working_directory

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

    def build_project(self) -> None:
        for file in bfs_walk(self._project_root):
            if is_cmake_file(file):
                self._cmake_file = file
                break
        self._cmake_file = None

        cmd: List[str | Path] = [
            "cmake",
            "-S",
            self.get_working_directory(),
            "-B",
            self.get_build_directory(),
        ]

        self.run_cmd(cmd)
        if self.get_build_error():
            return

        cmd = ["cmake", "--build", self.get_build_directory(), "--target", "help"]
        self.run_cmd(cmd)
        if self.get_build_error():
            return

        targets = self.TARGET_PATTERN.findall(self.get_stdout()[-1])
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
                return
            self._target = valid_targets[0]

        cmd = [
            "cmake",
            *CxxConfig.DEFAULT_CMAKE_COMPILATION_FLAGS,
            "--build",
            self.get_build_directory(),
            "--target",
            self._target,
            "--",
            "-s",
            "--no-print-directory",
        ]
        self.run_cmd(cmd)
        if self.get_build_error():
            return

        try:
            self._executable_path = self.find_executable(self._target)
        except FileNotFoundError:
            self.set_build_error(True)
            return

        assert self._executable_path is not None

    def set_build_directory(self, build_directory: Path) -> None:
        self._build_directory = build_directory

    def get_build_directory(self) -> Path:
        return self._build_directory

    def get_start_command(self) -> Command:
        if self._executable_path is None:
            self.build()
        assert self._executable_path is not None
        return [self._executable_path]
