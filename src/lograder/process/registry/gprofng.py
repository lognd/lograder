from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Union, Generic, TypeVar

from pydantic import field_validator
from typing_extensions import Self

from lograder.process.cli_args import (
    CLIArgs,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable, nested_cli_emit

T = TypeVar("T", bound=CLIArgs)

class GprofngCollectArgs(CLIArgs, Generic[T]):
    command: T = CLIOption(
        emitter=nested_cli_emit,
        position=-1,
    )

    output: Path | None = CLIOption(default=None, emit=["-o", "{}"])
    experiment: Path | None = CLIOption(default=None, emit=["-O", "{}"])

    follow_children: bool = CLIPresenceFlag(["-F"], default=False)
    trace_children: bool = CLIPresenceFlag(["-f"], default=False)

    sample: bool = CLIPresenceFlag(["-S"], default=False)
    heap: bool = CLIPresenceFlag(["-H"], default=False)

    duration: int | None = CLIOption(default=None, emit=["-t", "{}"])

    add_opts: list[str] = CLIMultiOption(default_factory=list)

    subcommand: Literal["collect"] = CLIOption(
        default="collect", position=0, emit=["{}"]
    )

    @field_validator("command", mode="after")
    @classmethod
    def validate_command(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("`command` must contain at least one element.")
        return v


class GprofngDisplayArgs(CLIArgs, Generic[T]):
    command: T = CLIOption(
        emitter=nested_cli_emit,
        position=-1,
    )

    experiment: Path = CLIOption(position=1, emit=["{}"])

    functions: bool = CLIPresenceFlag(["-functions"], default=False)
    call_tree: bool = CLIPresenceFlag(["-calltree"], default=False)
    source: bool = CLIPresenceFlag(["-source"], default=False)

    metrics: str | None = CLIOption(default=None, emit=["-metrics", "{}"])

    add_opts: list[str] = CLIMultiOption(default_factory=list)
    subcommand: Literal["display"] = CLIOption(
        default="display", position=0, emit=["{}"]
    )


@register_typed_executable(["gprofng"])
class GprofngExecutable(TypedExecutable[GprofngCollectArgs | GprofngDisplayArgs]):
    pass
