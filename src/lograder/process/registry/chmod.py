from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic import field_validator, model_validator
from typing_extensions import Self

from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    CLIArgs,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable

_OCTAL_RE = re.compile(r"^[0-7]{3,4}$")
_SYMBOLIC_CLAUSE_RE = re.compile(r"^[ugoa]*[+\-=][rwxXstugo]+$")
_SYMBOLIC_RE = re.compile(r"^[^,]+(?:,[^,]+)*$")


class CHModArgs(CLIArgs):
    """
    Intentionally narrow, high-value chmod interface.

    Supported:
    - mode or reference file
    - one or more target paths
    - recursive
    - force / verbose / changes
    - symlink behavior via -h
    """

    mode: str | None = CLIOption(default=None, position=0)
    reference: Path | None = CLIOption(
        default=None, emitter=lambda p: [] if p is None else [f"--reference={p}"]
    )

    recursive: bool = CLIPresenceFlag(["-R"], default=False)
    force: bool = CLIPresenceFlag(["-f"], default=False)
    verbose: bool = CLIPresenceFlag(["-v"], default=False)
    changes: bool = CLIPresenceFlag(["-c"], default=False)

    # GNU/coreutils and common POSIX environments use -h for "affect symlink itself"
    # where supported. Leave it as a simple opt-in flag.
    no_dereference: bool = CLIPresenceFlag(["-h"], default=False)

    paths: list[Path] = CLIMultiOption(position=-1)

    @field_validator("mode", mode="before")
    @classmethod
    def validate_mode_not_blank(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"`mode` in `{cls.__name__}` cannot be blank.")
        return v

    @field_validator("mode", mode="after")
    @classmethod
    def validate_mode_format(cls, v: str | None) -> str | None:
        if v is None:
            return None

        mode = v.strip()

        if _OCTAL_RE.fullmatch(mode):
            return mode

        if not _SYMBOLIC_RE.fullmatch(mode):
            raise ValueError(
                f"`mode` in `{cls.__name__}` must be octal like `755`/`0644` "
                f"or symbolic like `u+rwx`, `go-w`, `u=rw,go=r`, but got `{v}`."
            )

        for clause in mode.split(","):
            if not _SYMBOLIC_CLAUSE_RE.fullmatch(clause):
                raise ValueError(
                    f"`mode` clause `{clause}` in `{cls.__name__}` is invalid."
                )

        return mode

    @field_validator("reference", mode="after")
    @classmethod
    def validate_reference_not_directory(cls, v: Path | None) -> Path | None:
        if v is not None and v.is_dir():
            raise ValueError(
                f"`reference` in `{cls.__name__}` must be a file, not directory `{v}`."
            )
        return v

    @field_validator("paths", mode="after")
    @classmethod
    def validate_paths_nonempty(cls, v: list[Path]) -> list[Path]:
        if not v:
            raise ValueError(
                f"`paths` in `{cls.__name__}` must contain at least one target path."
            )
        return v

    @model_validator(mode="after")
    def validate_mode_xor_reference(self) -> Self:
        if (self.mode is None) == (self.reference is None):
            raise ValueError(
                f"`{self.__class__.__name__}` requires exactly one of `mode` or `reference`."
            )
        return self

    @model_validator(mode="after")
    def validate_verbose_and_changes_not_both(self) -> Self:
        # Not invalid for chmod itself, but usually redundant and noisy.
        # Remove this validator if you want to permit both.
        if self.verbose and self.changes:
            raise ValueError(
                f"In `{self.__class__.__name__}`, `verbose` and `changes` should not both be enabled."
            )
        return self


@register_typed_executable(["chmod"])
class CHModExecutable(TypedExecutable[CHModArgs]): ...
