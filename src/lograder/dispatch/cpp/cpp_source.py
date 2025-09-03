import sys
from pathlib import Path
from typing import List, Optional

from ...common.types import FilePath
from ...common.utils import random_name
from static.basicconfig import LograderBasicConfig
from ..common.assignment import BuilderOutput, PreprocessorOutput
from ..common.interface import (
    DispatcherInterface,
    BuilderResults,
    CxxTestRunner,
    PreprocessorResults,
)
from ..common.file_operations import bfs_walk, is_cxx_source_file, run_cmd


class CxxSourceDispatcher(CxxTestRunner, DispatcherInterface):
    def __init__(self, project_root: FilePath):
        super().__init__()
        self._project_root: Path = Path(project_root)
        self._build_path: Path = self._project_root / "build"
        self._executable_path: Optional[Path] = None

        if not self._build_path.exists():
            self._build_path = self._project_root

        self._source_files: List[Path] = []
        for file in bfs_walk(self._project_root):
            if is_cxx_source_file(file):
                self._source_files.append(file)

    def get_executable_path(self) -> Path:
        if self._executable_path is None:
            executable_name = (
                self.get_build_path() / (random_name() + ".exe")
                if sys.platform.startswith("win")
                else self.get_build_path() / random_name()
            )
            if executable_name.exists():
                self.set_build_code(1)
                return Path("/")
                # raise CxxSourceBuildError(self._source_files)
            self._executable_path = executable_name
        return self._executable_path

    def get_build_path(self) -> Path:
        return self._build_path

    def get_project_root(self) -> Path:
        return self._project_root

    def preprocess(self) -> PreprocessorResults:
        return PreprocessorResults(
            PreprocessorOutput(commands=[], stdout=[], stderr=[])
        )

    def build(self) -> BuilderResults:

        commands: List[List[str | Path]] = []
        stdout: List[str] = []
        stderr: List[str] = []

        cmd: List[str | Path] = [
            "g++",
            *LograderBasicConfig.DEFAULT_CXX_COMPILATION_FLAGS,
            f"-std={LograderBasicConfig.DEFAULT_CXX_STANDARD}",
            "-o",
            self.get_executable_path(),
            *self._source_files,
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

        return BuilderResults(
            executable=self.get_executable_path(),
            output=BuilderOutput(
                commands=commands, stdout=stdout, stderr=stderr, build_type="cxx-source"
            ),
        )
