from lograder.process.registry.cmake import (
    CMakeBuildArgs,
    CMakeConfigureArgs,
    CMakeExecutable,
)
from lograder.process.registry.makefile import MakefileArgs, MakefileExecutable
from lograder.process.registry.gcc import GCCArgs, GXXArgs, GCCExecutable, GXXExecutable

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
