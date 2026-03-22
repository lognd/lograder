from __future__ import annotations

from lograder.pipeline.types.executable.base_executable import Executable


class GCCExecutable(Executable):
    command: list[str] = ["gcc"]


class GXXExecutable(Executable):
    command: list[str] = ["g++"]


class ClangExecutable(Executable):
    command: list[str] = ["clang"]


class ClangXXExecutable(Executable):
    command: list[str] = ["clang++"]


class MSVCExecutable(Executable):
    """
    Usually invokes cl.exe from a Developer Command Prompt
    or an environment initialized by vcvarsall.bat.
    """

    command: list[str] = ["cl"]
