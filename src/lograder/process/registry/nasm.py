from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

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

if TYPE_CHECKING:
    from _strenum_compat import StrEnum
else:
    try:
        from enum import StrEnum
    except ImportError:
        from strenum import StrEnum


class NasmFormat(StrEnum):
    ELF32 = "elf32"
    ELF64 = "elf64"
    WIN32 = "win32"
    WIN64 = "win64"
    MACHO64 = "macho64"
    BIN = "bin"


class NasmArgs(CLIArgs):
    input: list[Path] = CLIMultiOption()
    output: Path | None = CLIOption(default=None, emit=["-o", "{}"])

    format: NasmFormat | None = CLIOption(default=None, emit=["-f", "{}"])

    debug: bool = CLIPresenceFlag(["-g"], default=False)

    include_dirs: list[Path] = CLIMultiOption(default_factory=list, token_emit=["-I{}"])

    defines: dict[str, str | int | bool | None] = CLIKVOption(
        default_factory=dict,
        token_emitter=lambda k, v: (
            [f"-D{k}"] if v is None else [f"-D{k}={_nasm_value(v)}"]
        ),
    )

    undefines: list[str] = CLIMultiOption(default_factory=list, token_emit=["-U{}"])

    warnings: list[str] = CLIMultiOption(default_factory=list, token_emit=["-w+{}"])
    disable_warnings: list[str] = CLIMultiOption(
        default_factory=list, token_emit=["-w-{}"]
    )

    list_file: Path | None = CLIOption(default=None, emit=["-l", "{}"])

    optimize: str | None = CLIOption(default=None, emit=["-O{}"])

    preproc_only: bool = CLIPresenceFlag(["-E"], default=False)

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

    @field_validator("output", "list_file", mode="before")
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

    @field_validator(
        "undefines", "warnings", "disable_warnings", "add_opts", mode="before"
    )
    @classmethod
    def validate_strings(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(f"Blank string at index {i}.")
        return v


def _nasm_value(v: str | int | bool) -> str:
    if isinstance(v, bool):
        return "1" if v else "0"
    return str(v)


@register_typed_executable(["nasm"])
class NasmExecutable(TypedExecutable[NasmArgs]):
    pass
