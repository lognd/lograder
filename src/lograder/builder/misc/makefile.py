from typing import Optional
from pathlib import Path

from ..common.builder_interface import BuilderInterface, BuilderResults, PreprocessorResults, RuntimeResults
from ..common.file_operations import bfs_walk, is_makefile_file, run_cmd
from ..common.exceptions import MakefileNotFoundError, MakefileRunNotFoundError
from ..common.assignment import PreprocessorOutput, BuilderOutput
from ...common.types import FilePath
from ...tests.registry import TestRegistry

class MakefileBuilder(BuilderInterface):
    def __init__(self, project_root: FilePath):
        self._project_root: Path = Path(project_root)

        self._makefile: Optional[Path] = None
        for file in bfs_walk(self._project_root):
            if is_makefile_file(file):
                self._makefile = file
                break
        if self._makefile is None:
            raise MakefileNotFoundError
        self._working_directory: Path = self._makefile.parent

    def get_project_root(self) -> FilePath:
        return self._project_root

    def get_working_directory(self) -> FilePath:
        return self._working_directory

    def preprocess(self) -> PreprocessorResults:
        return PreprocessorResults(
            PreprocessorOutput(
                commands=[],
                stdout=[],
                stderr=[]
            )
        )

    def build(self) -> BuilderResults:
        commands = []
        stdout = []
        stderr = []

        cmd = [
            "make"
        ]
        run_cmd(cmd, commands=commands, stdout=stdout, stderr=stderr, working_directory=self.get_working_directory())

        return BuilderResults(
            executable=self._makefile,
            output=BuilderOutput(
                commands=commands,
                stdout=stdout,
                stderr=stderr,
                build_type="makefile"
            )
        )

    def run_tests(self) -> RuntimeResults:
        finished_tests = []
        for test in TestRegistry.iterate():
            test.set_target(["make", "run"])
            test.run(wrap_args=True, working_directory=self.get_working_directory())
            finished_tests.append(test)
        return RuntimeResults(
            results=finished_tests
        )
