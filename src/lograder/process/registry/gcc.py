from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from lograder.exception import DeveloperException
from lograder.process.cli_args import CLI_ARG_MISSING, CLIOption, CLIPresenceFlag
from lograder.process.executable import TypedExecutable, register_typed_executable
from lograder.process.registry.common import (
    CompilerArgs,
    CStandard,
    CXXStandard,
    Standard,
    find_missing,
)

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from _strenum_compat import StrEnum
else:
    try:
        # noinspection PyUnresolvedReferences
        from enum import StrEnum
    except ImportError:
        # noinspection PyUnresolvedReferences
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


_missing_c = find_missing(CStandard, GNUStandard)
if _missing_c:
    raise DeveloperException(
        f"`GNUStandard` should be a superset of `CStandard`. Missing: `{'`, `'.join(sorted(_missing_c))}`."
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


_missing_cxx = find_missing(CXXStandard, GNUXXStandard)
if _missing_cxx:
    raise DeveloperException(
        f"`GNUXXStandard` should be a superset of `CXXStandard`. Missing: `{'`, `'.join(sorted(_missing_cxx))}`."
    )


class GNUOptimizationLevel(StrEnum):
    NONE = "0"
    BASIC = "1"
    BALANCED = "2"
    AGGRESSIVE = "3"
    FAST = "fast"
    SIZE = "s"
    SIZE_AGGRESSIVE = "z"
    DEBUG = "g"


class GNUCompilerArgs(CompilerArgs, Generic[Standard]):
    optimization_level: GNUOptimizationLevel | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-O{}"],
    )

    position_independent_code: bool = CLIPresenceFlag(["-fPIC"], default=False)
    shared: bool = CLIPresenceFlag(["-shared"], default=False)

    # Helpful GNU front-end behavior toggles
    pipe: bool = CLIPresenceFlag(["-pipe"], default=False)
    pthread: bool = CLIPresenceFlag(["-pthread"], default=False)


class GCCArgs(GNUCompilerArgs[GNUStandard]):
    pass


class GXXArgs(GNUCompilerArgs[GNUXXStandard]):
    permissive: bool = CLIPresenceFlag(["-fpermissive"], default=False)


@register_typed_executable(["gcc"])
class GCCExecutable(TypedExecutable[GCCArgs]):
    pass


@register_typed_executable(["g++"])
class GXXExecutable(TypedExecutable[GXXArgs]):
    pass
