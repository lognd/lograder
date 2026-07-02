"""ty static type checker registry entry."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

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


class TyArgs(CLIArgs):
    """Arguments for ``ty check``.

    ``files`` is required; all other fields are optional overrides.
    """

    subcommand: Literal["check"] = CLIOption(default="check", position=0, emit=["{}"])

    files: list[Path] = CLIMultiOption(default_factory=list)

    # -- Rule selection ----------------------------------------------------------
    error: list[str] = CLIMultiOption(default_factory=list, token_emit=["--error={}"])
    warn: list[str] = CLIMultiOption(default_factory=list, token_emit=["--warn={}"])
    ignore: list[str] = CLIMultiOption(default_factory=list, token_emit=["--ignore={}"])

    # -- Environment ---------------------------------------------------------------
    python_version: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--python-version={}"]
    )
    config_file: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--config-file={}"]
    )

    # -- Output ----------------------------------------------------------------
    # "full" (default), "concise", "gitlab", "github", "junit"
    output_format: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--output-format={}"]
    )
    color: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--color={}"]
    )
    exit_zero: bool = CLIPresenceFlag(["--exit-zero"], default=False)


@register_typed_executable(["ty"])
class TyExecutable(TypedExecutable[TyArgs]):
    install_executable = InstallScript(
        {is_posix: simple_bash_install_script(__file__, "install_ty.sh")}
    )
