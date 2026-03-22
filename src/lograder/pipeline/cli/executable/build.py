from __future__ import annotations

from lograder.pipeline.types.executable.base_executable import Executable


class CMakeExecutable(Executable):
    command: list[str] = ["cmake"]


class MakeExecutable(Executable):
    command: list[str] = ["make"]


class PythonExecutable(Executable):
    command: list[str] = ["python"]


class PyProjectBuildExecutable(Executable):
    """
    Equivalent to: python -m build
    """

    command: list[str] = ["python", "-m", "build"]


class PipExecutable(Executable):
    """
    Equivalent to: python -m pip
    """

    command: list[str] = ["python", "-m", "pip"]
