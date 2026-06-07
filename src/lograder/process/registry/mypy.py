"""mypy static type checker registry entry."""

from __future__ import annotations

from pathlib import Path

from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    CLIArgs,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable
from lograder.process.install_script import InstallScript, PlatformInstallScript
from lograder.process.os_helpers import is_posix
from lograder.process.registry.bash import BashExecutable, BashScriptArgs


class MypyArgs(CLIArgs):
    """Arguments for mypy.

    ``files`` is required; all other fields are optional overrides.
    """

    files: list[Path] = CLIMultiOption(default_factory=list)

    # -- Strictness ------------------------------------------------------------
    strict: bool = CLIPresenceFlag(["--strict"], default=False)
    disallow_untyped_defs: bool = CLIPresenceFlag(
        ["--disallow-untyped-defs"], default=False
    )
    disallow_incomplete_defs: bool = CLIPresenceFlag(
        ["--disallow-incomplete-defs"], default=False
    )
    check_untyped_defs: bool = CLIPresenceFlag(["--check-untyped-defs"], default=False)
    warn_return_any: bool = CLIPresenceFlag(["--warn-return-any"], default=False)
    no_implicit_optional: bool = CLIPresenceFlag(
        ["--no-implicit-optional"], default=False
    )

    # -- Import discovery ------------------------------------------------------
    ignore_missing_imports: bool = CLIPresenceFlag(
        ["--ignore-missing-imports"], default=False
    )
    python_version: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--python-version", "{}"]
    )
    config_file: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--config-file", "{}"]
    )

    # -- Output ----------------------------------------------------------------
    # "text" (default), "json", "xml"
    output: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--output", "{}"]
    )
    show_error_codes: bool = CLIPresenceFlag(["--show-error-codes"], default=False)
    show_column_numbers: bool = CLIPresenceFlag(
        ["--show-column-numbers"], default=False
    )
    no_color_output: bool = CLIPresenceFlag(["--no-color-output"], default=False)
    no_error_summary: bool = CLIPresenceFlag(["--no-error-summary"], default=False)


@register_typed_executable(["mypy"])
class MypyExecutable(TypedExecutable[MypyArgs]):
    install_executable = InstallScript(
        {
            is_posix: PlatformInstallScript(
                executable=BashExecutable(),
                args=BashScriptArgs(
                    script=Path(__file__).parents[2]
                    / "data/install_scripts/install_mypy.sh"
                ),
            )
        }
    )
