import subprocess
from pathlib import Path
from typing import List, Union

from ...common.types import FilePath
from ...tests.test import ComparisonTest
from ..common import BuilderInterface, bfs_walk, is_cxx_source_file
from ..common.exceptions import GxxCompilationError
from ..constants import (
    DEFAULT_CXX_COMPILATION_FLAGS,
    DEFAULT_CXX_STANDARD,
    DEFAULT_EXECUTABLE_NAME,
)


class CxxSourceBuilder(BuilderInterface):
    def __init__(self, project_root: FilePath):
        self._sources: List[Path] = []
        self._executable_path: Path = Path(project_root) / DEFAULT_EXECUTABLE_NAME
        for file in bfs_walk(Path(project_root)):
            if is_cxx_source_file(file):
                self._sources.append(file)

    def get_executable_path(self) -> Path:
        return self._executable_path.resolve()

    def preprocess(self):
        pass

    def build(self):
        source_files: List[str] = [str(Path(path).resolve()) for path in self._sources]
        cmd: List[Union[str, Path]] = [
            "g++",
            f"-std={DEFAULT_CXX_STANDARD}",
            *DEFAULT_CXX_COMPILATION_FLAGS,
            "-o",
            self.get_executable_path(),
            *source_files,
        ]

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise GxxCompilationError(proc)

        return Path(self.get_executable_path())

    def run(self, test: ComparisonTest):
        pass
