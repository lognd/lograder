from pathlib import Path
from typing import Optional, List
import re
import subprocess

from ...common.utils import random_name
from ...common.types import FilePath
from ...constants import Constants
from ..common.file_operations import bfs_walk, is_cmake_file, run_cmd, is_valid_target
from ..common.builder_interface import BuilderInterface, CxxTestRunner, BuilderResults, RuntimeResults, PreprocessorResults
from ..common.assignment import PreprocessorOutput, BuilderOutput
from ..common.exceptions import CMakeListsNotFoundError, CMakeTargetNotFoundError, CMakeExecutableNotFoundError


class CMakeBuilder(CxxTestRunner, BuilderInterface):
    TARGET_PATTERN = re.compile(r'^\.\.\.\s+([a-zA-Z0-9_\-.]+)', re.MULTILINE)

    def __init__(self, project_root: FilePath):
        self._project_root: Path = Path(project_root)
        self._build_directory: Path = self._project_root / f"build-{random_name()}"
        self._cmake_file: Optional[Path] = None
        for file in bfs_walk(self._project_root):
            if is_cmake_file(file):
                self._cmake_file = file
                break
        if self._cmake_file is None:
            raise CMakeListsNotFoundError
        self._working_directory: Path = self._cmake_file.parent
        self._cmake_target: Optional[str] = None
        self._executable_path: Optional[Path] = None

    def get_project_root(self) -> Path:
        return self._project_root

    def get_build_directory(self) -> Path:
        return self._build_directory

    def get_cmake_file(self) -> Path:
        return self._cmake_file

    def get_working_directory(self) -> Path:
        return self._working_directory

    def get_executable_path(self) -> Path:
        if self._executable_path is None:
            raise CMakeExecutableNotFoundError(self.get_working_directory() / "CMakeLists.txt")
        return self._executable_path

    def preprocess(self) -> PreprocessorResults:
        return PreprocessorResults(
            PreprocessorOutput(
                commands = [],
                stdout = [],
                stderr = [],
            )
        )

    def build(self) -> BuilderResults:
        commands = []
        stdout = []
        stderr = []

        cmd = [
            "cmake",
            "-S", self.get_working_directory(),
            "-B", self.get_build_directory()
        ]
        run_cmd(cmd, commands=commands, stdout=stdout, stderr=stderr)

        cmd = [
            "cmake",
            "-S", self.get_working_directory(),
            "-B", self.get_build_directory(),
            "--target", "help"
        ]
        run_cmd(cmd, commands=commands, stdout=stdout, stderr=stderr)
        targets = self.TARGET_PATTERN.findall(stdout[-1])
        if "main" in targets:
            target = "main"
        elif "build" in targets:
            target = "build"
        elif "demo" in targets:
            target = "demo"
        else:
            valid_targets = [target for target in targets if is_valid_target(target)]
            if not valid_targets:
                raise CMakeTargetNotFoundError(targets, self.get_working_directory() / "CMakeLists.txt")
            target = valid_targets[0]

        cmd = [
            "cmake",
            "-S", self.get_working_directory(),
            "-B", self.get_build_directory(),
            "--target", target
        ]
        run_cmd(cmd, commands=commands, stdout=stdout, stderr=stderr)

        cmd = [
            "cmake",
            "-P", "-",
        ]
        script = f"get_target_property(path {target} LOCATION)\nmessage(STATUS \"${{path}}\")\n"
        result = subprocess.run(cmd, input=script.encode(), capture_output=True, text=True)
        commands.append(cmd)
        stdout.append(result.stdout)
        stderr.append(result.stderr)
        for line in result.stdout.splitlines():
            if line.startswith("-- "):  # cmake -P prefixes STATUS with --
                self._executable_path = line[3:].strip()
        if self._executable_path is None:
            raise CMakeExecutableNotFoundError(self.get_working_directory() / "CMakeLists.txt")

        return BuilderResults(
            executable=self.get_executable_path(),
            output = BuilderOutput(
                commands = commands,
                stdout = stdout,
                stderr = stderr,
                build_type = "cmake"
            )
        )

