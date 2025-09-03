from pathlib import Path

from ...common.types import FilePath
from .. import CxxSourceBuilder
from ..common.builder_interface import (
    BuilderInterface,
    BuilderResults,
    PreprocessorResults,
    RuntimeResults,
)
from ..common.file_operations import bfs_walk, is_cmake_file, is_makefile_file
from ..common.types import ProjectType
from ..cpp import CMakeBuilder
from .makefile import MakefileBuilder


def detect_project_type(project_root: Path) -> ProjectType:
    for file in bfs_walk(project_root):
        if is_cmake_file(file):
            return "cmake"
        if is_makefile_file(file):
            return "makefile"
    return "cxx-source"


class ProjectBuilder(BuilderInterface):
    def __init__(self, project_root: FilePath):
        project_root = Path(project_root)
        project_type: ProjectType = detect_project_type(project_root)
        self._internal_project: BuilderInterface

        if project_type == "cmake":
            self._internal_project = CMakeBuilder(project_root)
        elif project_type == "makefile":
            self._internal_project = MakefileBuilder(project_root)
        else:
            self._internal_project = CxxSourceBuilder(project_root)

    def preprocess(self) -> PreprocessorResults:
        return self._internal_project.preprocess()

    def build(self) -> BuilderResults:
        return self._internal_project.build()

    def run_tests(self) -> RuntimeResults:
        return self._internal_project.run_tests()
