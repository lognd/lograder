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
        self.set_project_root(PathConfig.DEFAULT_SUBMISSION_PATH)

        self._build_directory: Optional[Path] = None
        self._built: bool = False

    def build_project(self) -> None:
        if self._built:
            return
        self._built = True
        source_files: List[Path] = []
        for file in bfs_walk(self.get_project_root()):
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
        if self._build_directory is None:
            build_directory: Path = self.get_project_root() / "build"
            if not build_directory.exists():
                build_directory = self.get_project_root()
            self.set_build_directory(build_directory)
        assert self._build_directory is not None
        return self._build_directory

    def get_start_command(self) -> Command:
        if self._executable_path is None:
            self.build_project()
        assert self._executable_path is not None
        return [self._executable_path]
