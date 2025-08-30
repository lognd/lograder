from pathlib import Path
import subprocess
from typing import Optional

from ...constants import Constants
from ...common.utils import random_name
from ..common.file_operations import bfs_walk, is_cxx_source_file
from ...common.types import FilePath
from ..common.builder_interface import BuilderInterface, BuilderResults, RuntimeResults, PreprocessorResults
from ..common.assignment import PreprocessorOutput, BuilderOutput
from ...tests.registry import TestRegistry

class CxxSourceBuilder(BuilderInterface):
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

        cmd = [
            "g++",
            *Constants.DEFAULT_CXX_COMPILATION_FLAGS,
            f"-std={Constants.DEFAULT_CXX_STANDARD}",
            f"-o", executable_name,
            *source_files,
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=Constants.DEFAULT_EXECUTABLE_TIMEOUT
        )

        return BuilderResults(
            executable=executable_name,
            output=BuilderOutput(
                commands=[cmd],
                stdout=[result.stdout],
                stderr=[result.stderr],
                build_type="cxx-source"
            ),
        )

    def run_tests(self) -> RuntimeResults:
        finished_tests = []
        for test in TestRegistry.iterate():
            test.set_target(self.get_executable_path())
            test.run()
            finished_tests.append(test)
        return RuntimeResults(
            results=finished_tests,
        )