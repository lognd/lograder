from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Union

from pydantic import field_validator
from typing_extensions import Self

from lograder.process.cli_args import (
    CLIArgs,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable


class PerfRecordArgs(CLIArgs):
    subcommand: Literal["record"] = CLIOption(default="record", position=0, emit=["{}"])

    output: Path | None = CLIOption(default=None, emit=["-o", "{}"])
    frequency: int | None = CLIOption(default=None, emit=["-F", "{}"])
    call_graph: str | None = CLIOption(default=None, emit=["-g", "{}"])

    system_wide: bool = CLIPresenceFlag(["-a"], default=False)
    inherit: bool = CLIPresenceFlag(["-i"], default=False)

    pid: int | None = CLIOption(default=None, emit=["-p", "{}"])
    cpu: str | None = CLIOption(default=None, emit=["-C", "{}"])

    event: list[str] = CLIMultiOption(default_factory=list, token_emit=["-e{}"])

    add_opts: list[str] = CLIMultiOption(default_factory=list)

    command: list[str] = CLIMultiOption(default_factory=list, position=-1)

    @field_validator("command", mode="after")
    @classmethod
    def validate_command(cls, v: list[str]) -> list[str]:
        if not v and cls is PerfRecordArgs:
            raise ValueError("`command` must be provided for perf record.")
        return v


class PerfStatArgs(CLIArgs):
    subcommand: Literal["stat"] = CLIOption(default="stat", position=0, emit=["{}"])

    event: list[str] = CLIMultiOption(default_factory=list, token_emit=["-e{}"])

    system_wide: bool = CLIPresenceFlag(["-a"], default=False)
    verbose: bool = CLIPresenceFlag(["-v"], default=False)

    repeat: int | None = CLIOption(default=None, emit=["-r", "{}"])

    output: Path | None = CLIOption(default=None, emit=["-o", "{}"])

    command: list[str] = CLIMultiOption(default_factory=list, position=-1)

    @field_validator("command", mode="after")
    @classmethod
    def validate_command(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("`command` must be provided for perf stat.")
        return v


class PerfReportArgs(CLIArgs):
    subcommand: Literal["report"] = CLIOption(default="report", position=0, emit=["{}"])

    input_file: Path | None = CLIOption(default=None, emit=["-i", "{}"])

    stdio: bool = CLIPresenceFlag(["--stdio"], default=False)
    call_graph: str | None = CLIOption(default=None, emit=["-g", "{}"])

    sort: str | None = CLIOption(default=None, emit=["--sort", "{}"])

    add_opts: list[str] = CLIMultiOption(default_factory=list)


class PerfScriptArgs(CLIArgs):
    subcommand: Literal["script"] = CLIOption(default="script", position=0, emit=["{}"])

    input_file: Path | None = CLIOption(default=None, emit=["-i", "{}"])

    fields: str | None = CLIOption(default=None, emit=["-F", "{}"])

    add_opts: list[str] = CLIMultiOption(default_factory=list)


PerfArgs = Union[
    PerfRecordArgs,
    PerfStatArgs,
    PerfReportArgs,
    PerfScriptArgs,
]


@register_typed_executable(["perf"])
class PerfExecutable(TypedExecutable[PerfArgs]):
    pass
