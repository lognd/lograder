from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import field_validator
from typing_extensions import Self

from lograder.process.cli_args import (
    CLIArgs,
    CLIKVOption,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable


class GasArgs(CLIArgs):
    input: list[Path] = CLIMultiOption()
    output: Path | None = CLIOption(default=None, emit=["-o", "{}"])

    architecture: str | None = CLIOption(default=None, emit=["-march={}"])
    cpu: str | None = CLIOption(default=None, emit=["-mcpu={}"])

    debug: bool = CLIPresenceFlag(["-g"], default=False)

    include_dirs: list[Path] = CLIMultiOption(default_factory=list, token_emit=["-I{}"])

    defines: dict[str, str | int | bool | None] = CLIKVOption(
        default_factory=dict,
        token_emitter=lambda k, v: (
            [f"-D{k}"] if v is None else [f"-D{k}={_gas_value(v)}"]
        ),
    )

    undefines: list[str] = CLIMultiOption(default_factory=list, token_emit=["-U{}"])

    warnings: bool = CLIPresenceFlag(["--warn"], default=False)
    fatal_warnings: bool = CLIPresenceFlag(["--fatal-warnings"], default=False)

    listing: Path | None = CLIOption(
        default=None,
        emit=[
            "-al={}",
        ],
    )

    compress_debug: bool = CLIPresenceFlag(["--compress-debug-sections"], default=False)

    add_opts: list[str] = CLIMultiOption(default_factory=list)

    @field_validator("input", mode="before")
    @classmethod
    def validate_inputs(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(f"Blank input at index {i}.")
        return v

    @field_validator("input", mode="after")
    @classmethod
    def validate_paths_exist(cls, v: list[Path]) -> list[Path]:
        for i, item in enumerate(v):
            if not item.is_file():
                raise ValueError(f"File, `{item}`, at index {i} does not exist.")
        return v

    @field_validator("input", mode="after")
    @classmethod
    def validate_nonempty(cls, v: list[Path]) -> list[Path]:
        if not v:
            raise ValueError("`input` must contain at least one source file.")
        return v

    @field_validator("output", "listing", mode="before")
    @classmethod
    def validate_paths(cls, v: Any) -> Any:
        if v is None:
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError("Path cannot be blank.")
        return v

    @field_validator("include_dirs", mode="before")
    @classmethod
    def validate_include_dirs(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(f"Blank include dir at index {i}.")
        return v

    @field_validator("undefines", "add_opts", mode="before")
    @classmethod
    def validate_strings(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(f"Blank string at index {i}.")
        return v


def _gas_value(v: str | int | bool) -> str:
    if isinstance(v, bool):
        return "1" if v else "0"
    return str(v)


@register_typed_executable(["as"])
class GasExecutable(TypedExecutable[GasArgs]):
    pass
