from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import field_validator, model_validator
from typing_extensions import Self

from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    CLIArgs,
    CLIKVOption,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable


class MakefileArgs(CLIArgs):
    directory: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-C", "{}"],
    )
    makefile: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-f", "{}"],
    )

    jobs: int | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-j{}"],
    )

    always_make: bool = CLIPresenceFlag(["-B"], default=False)
    keep_going: bool = CLIPresenceFlag(["-k"], default=False)
    silent: bool = CLIPresenceFlag(["-s"], default=False)
    just_print: bool = CLIPresenceFlag(["-n"], default=False)
    print_directory: bool = CLIPresenceFlag(["-w"], default=False)

    variables: dict[str, Any] = CLIKVOption(
        default_factory=dict,
        token_emitter=lambda k, v: [f"{k}={v}"],
    )

    target: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["{}"],
        position=-1,
    )

    @field_validator("target", mode="before")
    @classmethod
    def validate_nonempty_target(cls, v: Any) -> Any:
        if v is CLI_ARG_MISSING():
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank string is not valid in `{cls.__name__}`.")
        return v

    @field_validator("directory", "makefile", mode="before")
    @classmethod
    def validate_nonempty_paths(cls, v: Any) -> Any:
        if v is CLI_ARG_MISSING():
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank path is not valid in `{cls.__name__}`.")
        return v

    @field_validator("directory", mode="after")
    @classmethod
    def validate_directory_not_file(
        cls, v: Path | CLI_ARG_MISSING
    ) -> Path | CLI_ARG_MISSING:
        if isinstance(v, CLI_ARG_MISSING):
            return v
        if v.exists() and not v.is_dir():
            raise ValueError(
                f"`directory` for `{cls.__name__}` must be a directory if it exists, but got file `{v}`."
            )
        return v

    @field_validator("makefile", mode="after")
    @classmethod
    def validate_makefile_not_directory(
        cls, v: Path | CLI_ARG_MISSING
    ) -> Path | CLI_ARG_MISSING:
        if isinstance(v, CLI_ARG_MISSING):
            return v
        if v.exists() and v.is_dir():
            raise ValueError(
                f"`makefile` for `{cls.__name__}` must be a file, not directory `{v}`."
            )
        return v

    @field_validator("jobs", mode="after")
    @classmethod
    def validate_jobs_positive(cls, v: int | CLI_ARG_MISSING) -> int | CLI_ARG_MISSING:
        if isinstance(v, CLI_ARG_MISSING):
            return v
        if v <= 0:
            raise ValueError(f"`jobs` in `{cls.__name__}` must be > 0, but got `{v}`.")
        return v

    @field_validator("variables", mode="after")
    @classmethod
    def validate_variables(cls, v: dict[str, Any]) -> dict[str, Any]:
        for key in v:
            if not str(key).strip():
                raise ValueError(
                    f"`variables` in `{cls.__name__}` cannot contain blank keys."
                )
            if "=" in str(key):
                raise ValueError(
                    f"`variables` key `{key}` in `{cls.__name__}` cannot contain `=`."
                )
        return v

    @model_validator(mode="after")
    def validate_sane_combinations(self) -> Self:
        if self.silent and self.print_directory:
            raise ValueError(
                f"In `{self.__class__.__name__}`, `silent=True` conflicts with `print_directory=True`."
            )
        return self


@register_typed_executable(["make"])
class MakefileExecutable(TypedExecutable[MakefileArgs]):
    pass
