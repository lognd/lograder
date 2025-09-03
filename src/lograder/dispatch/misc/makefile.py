from pathlib import Path
from typing import List, Optional

from ...common.types import FilePath
from ...tests.registry import TestRegistry
from ..common.assignment import BuilderOutput, PreprocessorOutput
from ..common.builder_interface import (
    BuilderInterface,
    BuilderResults,
    PreprocessorResults,
    RuntimeResults,
)
from ..common.exceptions import MakefileNotFoundError
from ..common.file_operations import (
    bfs_walk,
    is_makefile_file,
    is_makefile_target,
    run_cmd,
)


class MakefileBuilder(BuilderInterface):
    def __init__(self, project_root: FilePath):
        self._project_root: Path = Path(project_root)
        self._built: bool = False
        self._build_code: int = 0

        self._makefile: Optional[Path] = None
        for file in bfs_walk(self._project_root):
            if is_makefile_file(file):
                self._makefile = file
                break
        if self._makefile is None:
            raise MakefileNotFoundError
        self._working_directory: Path = self._makefile.parent

    def get_makefile(self):
        if self._makefile is None:
            raise MakefileNotFoundError
        return self._makefile

    def get_project_root(self) -> Path:
        return self._project_root

    def get_working_directory(self) -> Path:
        return self._working_directory

    def preprocess(self) -> PreprocessorResults:
        return PreprocessorResults(
            PreprocessorOutput(commands=[], stdout=[], stderr=[])
        )

    def build(self) -> BuilderResults:
        commands: List[List[str | Path]] = []
        stdout: List[str] = []
        stderr: List[str] = []

        cmd: List[str | Path] = ["make", "-s"]
        result = run_cmd(
            cmd,
            commands=commands,
            stdout=stdout,
            stderr=stderr,
            working_directory=self.get_working_directory(),
        )
        if result.returncode != 0:
            self._build_code = 1
            return BuilderResults(
                executable="Build failed...",
                output=BuilderOutput(
                    commands=commands, stdout=stdout, stderr=stderr, build_type="cmake"
                ),
            )

        return BuilderResults(
            executable=self.get_makefile(),
            output=BuilderOutput(
                commands=commands, stdout=stdout, stderr=stderr, build_type="makefile"
            ),
        )

    def run_tests(self) -> RuntimeResults:
        if not self._built:
            self.build()
        self._built = True

        finished_tests = []
        if not is_makefile_target(self.get_makefile(), target="run"):
            self._build_code = 1
            # raise MakefileRunNotFoundError(self.get_makefile())
        for test in TestRegistry.iterate():
            test.set_target(["make", "-s", "run"])
            if self._build_code != 0:
                test.set_invalid()
            else:
                test.run(
                    wrap_args=True, working_directory=Path(self.get_working_directory())
                )
            finished_tests.append(test)
        return RuntimeResults(results=finished_tests)
