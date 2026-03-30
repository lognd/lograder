from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import field_validator
from typing_extensions import Self

from lograder.process.cli_args import (
    CLIArgs,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable


class GprofArgs(CLIArgs):
    executable: Path = CLIOption(position=0, emit=["{}"])
    gmon_file: Path | None = CLIOption(position=1, default=None, emit=["{}"])

    flat_profile: bool = CLIPresenceFlag(["-p"], default=False)
    call_graph: bool = CLIPresenceFlag(["-q"], default=False)

    annotate_source: list[str] = CLIMultiOption(
        default_factory=list,
        token_emit=["-A{}"],
    )

    no_static: bool = CLIPresenceFlag(["-a"], default=False)
    no_graph: bool = CLIPresenceFlag(["-b"], default=False)

    ignore_non_functions: bool = CLIPresenceFlag(["-c"], default=False)

    file_format: str | None = CLIOption(
        default=None,
        emit=["-O{}"],
    )

    demangle: bool = CLIPresenceFlag(["--demangle"], default=False)

    display_unused: bool = CLIPresenceFlag(["-z"], default=False)

    line: bool = CLIPresenceFlag(["-l"], default=False)

    function_ordering: bool = CLIPresenceFlag(["-r"], default=False)

    time: bool = CLIPresenceFlag(["-s"], default=False)

    suppress_call_graph: bool = CLIPresenceFlag(["-Q"], default=False)
    suppress_flat_profile: bool = CLIPresenceFlag(["-P"], default=False)

    add_opts: list[str] = CLIMultiOption(default_factory=list)

    @field_validator("executable", mode="before")
    @classmethod
    def validate_executable(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            raise ValueError("Executable cannot be blank.")
        return v

    @field_validator("gmon_file", mode="before")
    @classmethod
    def validate_gmon_file(cls, v: Any) -> Any:
        if v is None:
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError("gmon_file cannot be blank.")
        return v

    @field_validator("annotate_source", "add_opts", mode="before")
    @classmethod
    def validate_string_sequences(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(f"Blank string at index {i}.")
        return v


@register_typed_executable(["gprof"])
class GprofExecutable(TypedExecutable[GprofArgs]):
    pass
