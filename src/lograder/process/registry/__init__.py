from lograder.process.registry.cmake import (
    CMakeBuildArgs,
    CMakeConfigureArgs,
    CMakeExecutable,
)
from lograder.process.registry.gcc import GCCArgs, GCCExecutable, GXXArgs, GXXExecutable
from lograder.process.registry.makefile import MakefileArgs, MakefileExecutable

__all__ = [
    "CMakeConfigureArgs",
    "CMakeBuildArgs",
    "CMakeExecutable",
    "MakefileArgs",
    "MakefileExecutable",
    "GCCArgs",
    "GCCExecutable",
    "GXXArgs",
    "GXXExecutable",
]
