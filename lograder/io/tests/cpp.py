from pathlib import Path
import subprocess

from colorama import Fore
from typing import List, Optional
from pydantic import BaseModel, model_validator

from ...constants import (
    DEFAULT_SUBMISSION_PATH,
    DEFAULT_CXX_STANDARD,
    DEFAULT_CXX_COMPILATION_FLAGS,
    DEFAULT_EXECUTABLE_NAME,
    DEFAULT_EXECUTION_TIMEOUT,
    DEFAULT_BIN_DIRECTORY,
    DEFAULT_BUILD_DIRECTORY
)
from ..file_operations import bfs_walk, is_cxx_source_file, is_executable
from ..parser.cmake import get_student_targets
from .interface import TestInterface, Visibility
from ...exceptions import LograderError
from .exceptions import (
    LograderCompilationError,
    LograderRuntimeError,
    LograderTimeoutError,
    LograderAmbiguousTargetError,
    LograderNoTargetsError
)

class CxxExecutableConfig(BaseModel):
    name: str
    visibility: Visibility
    expected_output_str: Optional[str] = None
    expected_output_file: Optional[Path] = None
    input_str: Optional[str] = None
    input_file: Optional[Path] = None

    @model_validator(mode="after")
    def validate_only_one_output(self):
        if self.expected_output_str is None == self.expected_output_file is None:
            raise ValueError("Must specify exactly one of 'expected_output_str' or 'expected_output_file'.")
        return self

    @model_validator(mode="after")
    def validate_at_most_one_input(self):
        if self.input_str is not None and self.input_file is not None:
            raise ValueError("Must specify at most one of 'input_str' or 'input_file'.")
        return self

    @property
    def expected_output(self) -> Path | str:
        if self.expected_output_str is None:
            return Path(self.expected_output_file)
        return self.expected_output_str

    @property
    def program_input(self) -> Path | str | None:
        if self.input_file is not None:
            return Path(self.input_file)
        elif self.input_str is not None:
            return self.input_str
        return None


class CxxExecutableTest(TestInterface):

    def __init__(self,
                 name: str,
                 visibility: Visibility,
                 executable_path: Path | str,
                 expected_output: Path | str,
                 program_input: Optional[Path | str] = None):
        super().__init__()
        self.name = name
        self.visibility = visibility

        self.executable_path = Path(executable_path)

        if program_input is None:
            self.stdin = ''
        else:
            if isinstance(program_input, str):
                self.stdin = program_input
            else:
                with open(program_input, 'r') as f:
                    self.stdin = f.read()

        if isinstance(expected_output, str):
            self.expected_stdout = expected_output
        else:
            with open(expected_output, 'r') as f:
                self.expected_stdout = f.read()

        self.actual_stdout: Optional[str] = None

    def get_successful(self) -> bool:
        if self.actual_stdout is None:
            try:
                self.run()
            except LograderError as e:
                self.actual_stdout = str(e)
        return self.actual_stdout.strip() == self.expected_stdout.strip()

    def get_max_score(self) -> float:
        return 1.0

    def get_name(self) -> str:
        return self.name

    def get_output(self) -> str:
        if self.get_successful():
            return (
                f"{Fore.GREEN}Test passed successfully!{Fore.RESET}\n"
                "Expected stdout: \n"
                "<BEGIN STDOUT>\n"
                f"{self.expected_stdout}\n"
                "<END STDOUT>\n\n"
                "Actual stdout: \n"
                "<BEGIN STDOUT>\n"
                f"{self.actual_stdout}\n"
                "<END STDOUT>\n"
            )
        else:
            output = (
                "<BEGIN STDOUT>\n"
                f"{self.actual_stdout}\n"
                "<END STDOUT>"
            ) if "<BEGIN STDOUT>" not in self.actual_stdout else self.actual_stdout
            return (
                f"{Fore.RED}Test failed!{Fore.RESET}\n"
                "Expected stdout: \n"
                "<BEGIN STDOUT>\n"
                f"{self.expected_stdout}\n"
                "<END STDOUT>\n\n"
                "Actual stdout: \n"
                f"{output}\n\n"
                "(To help with debugging, you may also see the escaped strings.)\n"
                f"Expected: {repr(self.expected_stdout)}\n"
                f"Actual:   {repr(self.actual_stdout)}\n"
            )

    def get_visibility(self) -> Visibility:
        return self.visibility

    def run(self) -> str:
        with self.evaluate_time():
            try:
                proc = subprocess.run([self.executable_path], input=self.stdin, capture_output=True, text=True, timeout=DEFAULT_EXECUTION_TIMEOUT)
            except subprocess.TimeoutExpired as e:
                raise LograderTimeoutError() from e

            if proc.returncode != 0:
                raise LograderRuntimeError(proc)

        self.actual_stdout = proc.stdout
        return self.actual_stdout



class CxxProjectBuilder:

    def __init__(self, project_root: Path | str = DEFAULT_SUBMISSION_PATH):

        self.project_root: Path = Path(project_root)
        self.entry_point: Path = Path(project_root)
        source_files: List[Path] = []

        project_root = Path(project_root)
        for file in bfs_walk(project_root):
            if file.name == 'CMakeLists.txt':
                executable_file = self.build_from_cmake(file)
                self.executable_path = executable_file.resolve().as_posix()
                return
            elif is_cxx_source_file(file):
                source_files.append(file)
                with open(file, 'r') as f:
                    if 'int main()' in f.read():
                        self.entry_point = file.resolve().parent

        self.executable_path = (self.entry_point / DEFAULT_EXECUTABLE_NAME).resolve().as_posix()
        self.build_from_source(source_files)

    def build_from_cmake(self, cmake_path: Path | str):
        cmake_path = Path(cmake_path)
        working_directory = cmake_path.resolve().parent

        cmd = [
            'cmake',
            '--build',
            DEFAULT_BUILD_DIRECTORY,
            '--target',
            'help'
        ]
        proc = subprocess.run(cmd, capture_output=True, cwd=str(working_directory), text=True)
        if proc.returncode != 0:
            raise LograderCompilationError(proc)

        targets = get_student_targets(proc.stdout)
        if len(targets) > 1:
            raise LograderAmbiguousTargetError(targets)
        elif not targets:
            raise LograderNoTargetsError()

        target = targets[0]
        cmd = [
            'cmake',
            '--build',
            DEFAULT_BUILD_DIRECTORY,
            '--target',
            target
        ]
        proc = subprocess.run(cmd, capture_output=True, cwd=str(working_directory), text=True)
        if proc.returncode != 0:
            raise LograderCompilationError(proc)

        cmd = [
            'cmake',
            '--install',
            DEFAULT_BUILD_DIRECTORY,
            '--prefix',
            DEFAULT_BIN_DIRECTORY
        ]
        proc = subprocess.run(cmd, capture_output=True, cwd=str(working_directory), text=True)
        if proc.returncode != 0:
            raise LograderCompilationError(proc)

        for file in bfs_walk(self.project_root / DEFAULT_BIN_DIRECTORY):
            if is_executable(file.resolve()):
                return file

        raise LograderNoTargetsError()

    def build_from_source(self, source_files: List[Path | str]) -> Path:
        source_files = [str(Path(path).resolve()) for path in source_files]
        cmd = ["g++",
               f"-std={DEFAULT_CXX_STANDARD}",
               *DEFAULT_CXX_COMPILATION_FLAGS,
               '-o',
               self.executable_path,
               *source_files
               ]

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise LograderCompilationError(proc)

        return Path(self.executable_path)

    def get_executable_path(self):
        return self.executable_path
