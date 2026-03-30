from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import field_validator, model_validator
from typing_extensions import Self

from lograder.process.cli_args import (
    CLIArgs,
    CLIKVOption,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable


class LdArgs(CLIArgs):
    input: list[Path] = CLIMultiOption()

    output: Path | None = CLIOption(default=None, emit=["-o", "{}"])

    entry: str | None = CLIOption(default=None, emit=["-e", "{}"])

    shared: bool = CLIPresenceFlag(["-shared"], default=False)
    static: bool = CLIPresenceFlag(["-static"], default=False)
    pie: bool = CLIPresenceFlag(["-pie"], default=False)

    library_dirs: list[Path] = CLIMultiOption(default_factory=list, token_emit=["-L{}"])
    libraries: list[str] = CLIMultiOption(default_factory=list, token_emit=["-l{}"])

    rpath: list[str] = CLIMultiOption(default_factory=list, token_emit=["-rpath={}"])

    script: Path | None = CLIOption(default=None, emit=["-T", "{}"])

    map_file: Path | None = CLIOption(
        default=None,
        emit=[
            "-Map={}",
        ],
    )

    strip_all: bool = CLIPresenceFlag(["-s"], default=False)

    build_id: bool = CLIPresenceFlag(["--build-id"], default=False)

    gc_sections: bool = CLIPresenceFlag(["--gc-sections"], default=False)

    export_dynamic: bool = CLIPresenceFlag(["--export-dynamic"], default=False)

    undefined: list[str] = CLIMultiOption(default_factory=list, token_emit=["-u{}"])

    defines: dict[str, str | int | bool | None] = CLIKVOption(
        default_factory=dict,
        token_emitter=lambda k, v: (
            [f"-defsym={k}"] if v is None else [f"-defsym={k}={_ld_value(v)}"]
        ),
    )

    add_opts: list[str] = CLIMultiOption(default_factory=list)

    @field_validator("input", mode="before")
    @classmethod
    def validate_nonempty_inputs(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(f"Blank input at index {i}.")
        return v

    @field_validator("input", mode="after")
    @classmethod
    def validate_at_least_one_input(cls, v: list[Path]) -> list[Path]:
        if not v:
            raise ValueError("`input` must contain at least one object file.")
        return v

    @field_validator("output", mode="before")
    @classmethod
    def validate_output(cls, v: Any) -> Any:
        if v is None:
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError("Output cannot be blank.")
        return v

    @field_validator("library_dirs", mode="before")
    @classmethod
    def validate_library_dirs(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(f"Blank library dir at index {i}.")
        return v

    @field_validator("libraries", "undefined", "rpath", "add_opts", mode="before")
    @classmethod
    def validate_string_sequences(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(f"Blank string at index {i}.")
        return v

    @model_validator(mode="after")
    def validate_link_modes(self) -> Self:
        active = sum([self.shared, self.static, self.pie])
        if active > 1:
            raise ValueError("`shared`, `static`, and `pie` are mutually exclusive.")
        return self


def _ld_value(v: str | int | bool) -> str:
    if isinstance(v, bool):
        return "1" if v else "0"
    return str(v)


@register_typed_executable(["ld"])
class LdExecutable(TypedExecutable[LdArgs]):
    pass
