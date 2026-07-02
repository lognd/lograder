"""nm  -  list symbols from object files / libraries / executables."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    CLIArgs,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable
from lograder.process.install_script import InstallScript, simple_bash_install_script
from lograder.process.os_helpers import is_posix

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from _strenum_compat import StrEnum
else:
    try:
        from enum import StrEnum
    except ImportError:
        from strenum import StrEnum


class NmFormat(StrEnum):
    BSD = "bsd"
    SYSV = "sysv"
    POSIX = "posix"


class NmArgs(CLIArgs):
    files: list[Path] = CLIMultiOption(position=-1)

    # Symbol filtering
    dynamic: bool = CLIPresenceFlag(["-D"], default=False)
    extern_only: bool = CLIPresenceFlag(["-g"], default=False)
    undefined_only: bool = CLIPresenceFlag(["-u"], default=False)
    defined_only: bool = CLIPresenceFlag(["--defined-only"], default=False)

    # Output format
    format: NmFormat | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--format={}"]
    )
    portability: bool = CLIPresenceFlag(["-P"], default=False)
    print_file_name: bool = CLIPresenceFlag(["-A"], default=False)
    print_size: bool = CLIPresenceFlag(["-S"], default=False)
    line_numbers: bool = CLIPresenceFlag(["-l"], default=False)

    # Sorting
    numeric_sort: bool = CLIPresenceFlag(["-n"], default=False)
    reverse_sort: bool = CLIPresenceFlag(["-r"], default=False)
    no_sort: bool = CLIPresenceFlag(["-p"], default=False)
    size_sort: bool = CLIPresenceFlag(["--size-sort"], default=False)

    # Demangle
    demangle: bool = CLIPresenceFlag(["-C"], default=False)

    # Misc
    radix: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["-t", "{}"]
    )


@register_typed_executable(["nm"])
class NmExecutable(TypedExecutable[NmArgs]):
    install_executable = InstallScript(
        {is_posix: simple_bash_install_script(__file__, "install_binutils.sh")}
    )
