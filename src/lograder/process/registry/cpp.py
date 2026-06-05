"""Standalone C preprocessor (cpp)."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    CLIArgs,
    CLIKVOption,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable

if TYPE_CHECKING:
    from _strenum_compat import StrEnum
else:
    try:
        from enum import StrEnum
    except ImportError:
        from strenum import StrEnum


class CPPLanguage(StrEnum):
    C = "c"
    CXX = "c++"
    ASSEMBLER = "assembler"
    ASSEMBLER_WITH_CPP = "assembler-with-cpp"
    NONE = "none"


def _define_emitter(k: str, v: str | None) -> list[str]:
    return [f"-D{k}"] if v is None else [f"-D{k}={v}"]


class CPPArgs(CLIArgs):
    # Input/output
    input: Path = CLIOption(position=-1)
    output: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["-o", "{}"]
    )

    # Language selection
    language: CPPLanguage | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["-x", "{}"]
    )
    standard: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["-std={}"]
    )

    # Line markers
    suppress_line_markers: bool = CLIPresenceFlag(["-P"], default=False)

    # Include path
    include_dirs: list[Path] = CLIMultiOption(default=(), token_emit=["-I{}"])
    quote_include_dirs: list[Path] = CLIMultiOption(default=(), token_emit=["-iquote{}"])
    system_include_dirs: list[Path] = CLIMultiOption(
        default=(), token_emit=["-isystem{}"]
    )
    no_standard_includes: bool = CLIPresenceFlag(["-nostdinc"], default=False)
    no_standard_cxx_includes: bool = CLIPresenceFlag(["-nostdinc++"], default=False)

    # Macros
    defines: dict[str, str | None] = CLIKVOption(
        default={}, token_emitter=_define_emitter
    )
    undefines: list[str] = CLIMultiOption(default=(), token_emit=["-U{}"])
    undef: bool = CLIPresenceFlag(["-undef"], default=False)

    # Force-includes
    include_files: list[Path] = CLIMultiOption(default=(), token_emit=["-include", "{}"])
    imacros_files: list[Path] = CLIMultiOption(default=(), token_emit=["-imacros", "{}"])

    # Dependency generation
    dependency_only: bool = CLIPresenceFlag(["-M"], default=False)
    dependency_no_system: bool = CLIPresenceFlag(["-MM"], default=False)
    dependency_file: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["-MF", "{}"]
    )
    dependency_phony_targets: bool = CLIPresenceFlag(["-MP"], default=False)

    # Diagnostics
    suppress_warnings: bool = CLIPresenceFlag(["-w"], default=False)
    warnings_as_errors: bool = CLIPresenceFlag(["-Werror"], default=False)

    # Misc
    traditional: bool = CLIPresenceFlag(["-traditional-cpp"], default=False)
    trigraphs: bool = CLIPresenceFlag(["-trigraphs"], default=False)
    verbose: bool = CLIPresenceFlag(["-v"], default=False)


@register_typed_executable(["cpp"])
class CPPExecutable(TypedExecutable[CPPArgs]):
    pass
