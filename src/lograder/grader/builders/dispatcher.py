from pathlib import Path
from typing import List, Optional

from ...os.file import detect_project_type
from ...types import Command, ProjectType
from .cpp.cmake import CMakeBuilder
from .cpp.cxx_source import CxxSourceBuilder
from .interfaces.cli_builder import CLIBuilderInterface


class ProjectDispatcher(CLIBuilderInterface):
    def __init__(self):
        super().__init__()
        self._builder: Optional[CLIBuilderInterface] = None
        self._allowed_project_types: List[ProjectType] = [
            "cmake",
            "cxx-source",
            "makefile",
            "py-source",
            "pyproject",
        ]

    def set_allowed_project_types(self, allowed_project_types: List[ProjectType]):
        self._allowed_project_types = allowed_project_types

    def load_builder(self):
        project_type = detect_project_type(self.get_project_root())
        if project_type not in self._allowed_project_types:
            self.set_build_error(True)
            return

        if project_type == "cmake":
            self._builder = CMakeBuilder()
        else:
            self._builder = CxxSourceBuilder()

    def get_builder(self) -> CLIBuilderInterface:
        assert self._builder is not None
        return self._builder

    def get_build_directory(self) -> Path:
        return self.get_builder().get_build_directory()

    def get_start_command(self) -> Command:
        return self.get_builder().get_start_command()

    def build_project(self) -> None:
        self.get_builder().build_project()
