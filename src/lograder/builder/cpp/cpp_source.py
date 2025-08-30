from pathlib import Path
import subprocess
from typing import Optional

from ...constants import Constants
from ...common.utils import random_name
from ..common.file_operations import bfs_walk, is_cxx_source_file, run_cmd
from ...common.types import FilePath
from ..common.builder_interface import BuilderInterface, CxxTestRunner, BuilderResults, PreprocessorResults
from ..common.assignment import PreprocessorOutput, BuilderOutput

class CxxSourceBuilder(CxxTestRunner, BuilderInterface):
    def __init__(self, project_root: FilePath):
        self._project_root: Path = Path(project_root)
        self._build_path: Path = self._project_root / "build"
        self._executable_path: Optional[Path] = None
        if not self._build_path.exists():
            self._build_path = self._project_root

    def get_executable_path(self) -> Optional[Path]:
        return self._executable_path

    def get_build_path(self) -> Path:
        return self._build_path

    def get_project_root(self) -> Path:
        return self._project_root

    def preprocess(self) -> PreprocessorResults:
        return PreprocessorResults(
            PreprocessorOutput(
                commands = [],
                stdout = [],
                stderr = []
            )
        )

    def build(self) -> BuilderResults:
        source_files = []
        for file in bfs_walk(self._project_root):
            if is_cxx_source_file(file):
                source_files.append(file)

        executable_name = self.get_build_path() / random_name()
        self._executable_path = executable_name

        commands = []
        stdout = []
        stderr = []

        cmd = [
            "g++",
            *Constants.DEFAULT_CXX_COMPILATION_FLAGS,
            f"-std={Constants.DEFAULT_CXX_STANDARD}",
            f"-o", executable_name,
            *source_files,
        ]
        run_cmd(cmd, commands=commands, stdout=stdout, stderr=stderr)

        return BuilderResults(
            executable=executable_name,
            output=BuilderOutput(
                commands=commands,
                stdout=stdout,
                stderr=stderr,
                build_type="cxx-source"
            ),
        )