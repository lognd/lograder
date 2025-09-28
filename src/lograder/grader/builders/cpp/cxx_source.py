from pathlib import Path
from typing import List, Optional

from ....data.cxx import CxxConfig
from ....data.paths import PathConfig
from ....os.file import bfs_walk, is_cxx_source_file
from ....random_utils import random_executable
from ....types import Command
from ..interfaces.cli_builder import CLIBuilderInterface


class CxxSourceBuilder(CLIBuilderInterface):

    def __init__(self):
        super().__init__()
        self._executable_path: Optional[Path] = None
        self._project_root: Path = PathConfig.DEFAULT_SUBMISSION_PATH

        self._build_directory: Path = self._project_root / "build"
        if not self._build_directory.exists():
            self._build_directory = self._project_root

    def build_project(self) -> None:
        source_files: List[Path] = []
        for file in bfs_walk(self._project_root):
            if is_cxx_source_file(file):
                source_files.append(file)

        cmd: List[str | Path] = [
            "g++",
            *CxxConfig.DEFAULT_CXX_COMPILATION_FLAGS,
            f"-std={CxxConfig.DEFAULT_CXX_STANDARD}",
            "-o",
            self.get_executable_path(),
            *source_files,
        ]
        self.run_cmd(cmd)

    def get_executable_path(self) -> Path:
        if self._executable_path is not None:
            return self._executable_path
        while True:
            executable_name = self.get_build_directory() / random_executable()
            if not executable_name.exists():
                self._executable_path = executable_name
                return self._executable_path

    def set_build_directory(self, build_directory: Path) -> None:
        self._build_directory = build_directory

    def get_build_directory(self) -> Path:
        return self._build_directory

    def get_start_command(self) -> Command:
        if self._executable_path is None:
            self.build()
        assert self._executable_path is not None
        return [self._executable_path]
