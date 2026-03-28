from typing import TYPE_CHECKING

from lograder.exception import DeveloperException
from lograder.process.cli_args import CLIOption
from lograder.process.executable import TypedExecutable, register_typed_executable
from lograder.process.registry.common import (
    CompilerArgs,
    CStandard,
    CXXStandard,
    find_missing,
)

if TYPE_CHECKING:
    from _strenum_compat import StrEnum
else:
    try:
        from enum import StrEnum
    except ImportError:
        from strenum import StrEnum


class GNUStandard(StrEnum):
    C23 = "c23"
    C17 = "c17"
    C11 = "c11"
    C99 = "c99"
    C90 = "c90"
    GNU23 = "gnu23"
    GNU17 = "gnu17"
    GNU11 = "gnu11"
    GNU99 = "gnu99"
    GNU90 = "gnu90"


if find_missing(CStandard, GNUStandard):
    raise DeveloperException(
        f"`GNUStandard` string enum. class should be a superset of `CStandard`. The following was found missing: `{'`, `'.join(find_missing(CStandard, GNUStandard))}`"
    )


class GNUXXStandard(StrEnum):
    CXX23 = "c++23"
    CXX20 = "c++20"
    CXX17 = "c++17"
    CXX14 = "c++14"
    CXX11 = "c++11"
    CXX03 = "c++03"
    CXX98 = "c++98"
    GNUXX23 = "gnu++23"
    GNUXX20 = "gnu++20"
    GNUXX17 = "gnu++17"
    GNUXX14 = "gnu++14"
    GNUXX11 = "gnu++11"
    GNUXX03 = "gnu++03"
    GNUXX98 = "gnu++98"


if find_missing(CXXStandard, GNUXXStandard):
    raise DeveloperException(
        f"`GNUXXStandard` string enum. class should be a superset of `CXXStandard`. The following was found missing: `{'`, `'.join(find_missing(CXXStandard, GNUXXStandard))}`"
    )


class GNUOptimizationLevel(StrEnum):
    NONE = "0"
    BASIC = "1"
    BALANCED = "2"
    AGGRESSIVE = "3"
    FAST = "fast"
    SIZE = "s"


class GCCArgs(CompilerArgs[GNUStandard]):
    optimization_level: GNUOptimizationLevel = CLIOption(
        default=GNUOptimizationLevel.NONE, emit=["-O{}"]
    )


class GXXArgs(CompilerArgs[GNUXXStandard]):
    optimization_level: GNUOptimizationLevel = CLIOption(
        default=GNUOptimizationLevel.NONE, emit=["-O{}"]
    )


@register_typed_executable(["gcc"])
class GCCExecutable(TypedExecutable[GCCArgs]): ...


@register_typed_executable(["g++"])
class GXXExecutable(TypedExecutable[GXXArgs]): ...
