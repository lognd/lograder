from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Union

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


class LldElfArgs(CLIArgs):
    flavor: Literal["-flavor", "gnu"] | None = None

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

    gc_sections: bool = CLIPresenceFlag(["--gc-sections"], default=False)
    icf: str | None = CLIOption(default=None, emit=["--icf={}"])

    build_id: bool = CLIPresenceFlag(["--build-id"], default=False)

    threads: int | None = CLIOption(default=None, emit=["--threads={}"])

    undefined: list[str] = CLIMultiOption(default_factory=list, token_emit=["-u{}"])

    defines: dict[str, str | int | bool | None] = CLIKVOption(
        default_factory=dict,
        token_emitter=lambda k, v: (
            [f"-defsym={k}"] if v is None else [f"-defsym={k}={_lld_value(v)}"]
        ),
    )

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
    def validate_nonempty_input(cls, v: list[Path]) -> list[Path]:
        if not v:
            raise ValueError("`input` must contain at least one object.")
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
    def validate_dirs(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(f"Blank dir at index {i}.")
        return v

    @field_validator("libraries", "rpath", "undefined", "add_opts", mode="before")
    @classmethod
    def validate_strings(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(f"Blank string at index {i}.")
        return v

    @model_validator(mode="after")
    def validate_modes(self) -> Self:
        active = sum([self.shared, self.static, self.pie])
        if active > 1:
            raise ValueError("`shared`, `static`, and `pie` are mutually exclusive.")
        return self


class LldLinkArgs(CLIArgs):
    subcommand: Literal["link"] = CLIOption(default="link", position=0, emit=["{}"])

    input: list[Path] = CLIMultiOption()
    output: Path | None = CLIOption(
        default=None,
        emit=[
            "/OUT:{}",
        ],
    )

    debug: bool = CLIPresenceFlag(["/DEBUG"], default=False)

    dll: bool = CLIPresenceFlag(["/DLL"], default=False)

    libpath: list[Path] = CLIMultiOption(
        default_factory=list, token_emit=["/LIBPATH:{}"]
    )

    entry: str | None = CLIOption(
        default=None,
        emit=[
            "/ENTRY:{}",
        ],
    )

    subsystem: str | None = CLIOption(
        default=None,
        emit=[
            "/SUBSYSTEM:{}",
        ],
    )

    add_opts: list[str] = CLIMultiOption(default_factory=list)

    @field_validator("input", mode="after")
    @classmethod
    def validate_nonempty(cls, v: list[Path]) -> list[Path]:
        if not v:
            raise ValueError("`input` must contain at least one object.")
        return v


LldArgs = Union[LldElfArgs, LldLinkArgs]


def _lld_value(v: str | int | bool) -> str:
    if isinstance(v, bool):
        return "1" if v else "0"
    return str(v)


@register_typed_executable(["ld.lld"])
class LldExecutable(TypedExecutable[LldArgs]):
    pass
