from pathlib import Path
from typing import Optional

from ...os.file import bfs_walk, is_cmake_file
from ...types import Command
from ..builders.cpp.cmake import CMakeBuilder
from ..builders.cpp.cxx_source import CxxSourceBuilder
from ..builders.interfaces.builder import BuilderInterface
from .unit_tester import UnitTesterInterface


class Catch2UnitTester(UnitTesterInterface):
    def __init__(self):
        super().__init__()
        self._builder: Optional[BuilderInterface] = None

    def get_builder(self) -> BuilderInterface:
        assert self._builder is not None
        return self._builder

    def get_build_directory(self) -> Path:
        return self.get_instance_root()

    def get_start_command(self) -> Command:
        return self.get_builder().get_start_command()

    def build_test(self) -> None:
        cmake: bool = False
        for file in bfs_walk(self.get_project_root()):
            if is_cmake_file(file):
                cmake = True
                break
        if cmake:
            self._builder = CMakeBuilder()
        else:
            self._builder = CxxSourceBuilder()

        self._builder.set_project_root(self.get_instance_root())
