from __future__ import annotations

from pathlib import Path
from typing import Literal, Union

from lograder.process.cli_args import (
    CLIArgs,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import (
    TypedExecutable,
    register_typed_executable,
)
from lograder.process.install_script import InstallScript, simple_bash_install_script
from lograder.process.os_helpers import is_posix


class GprofngCollectArgs(CLIArgs):
    subcommand: Literal["collect"] = CLIOption(
        default="collect", position=0, emit=["{}"]
    )

    output: Path | None = CLIOption(default=None, emit=["-o", "{}"])
    experiment: Path | None = CLIOption(default=None, emit=["-O", "{}"])

    follow_children: bool = CLIPresenceFlag(["-F"], default=False)
    trace_children: bool = CLIPresenceFlag(["-f"], default=False)

    sample: bool = CLIPresenceFlag(["-S"], default=False)
    heap: bool = CLIPresenceFlag(["-H"], default=False)

    duration: int | None = CLIOption(default=None, emit=["-t", "{}"])

    add_opts: list[str] = CLIMultiOption(default_factory=list)
    command: list[str] = CLIMultiOption(default_factory=list, position=-1)


class GprofngDisplayArgs(CLIArgs):
    subcommand: Literal["display"] = CLIOption(
        default="display", position=0, emit=["{}"]
    )

    experiment: Path = CLIOption(position=1, emit=["{}"])

    functions: bool = CLIPresenceFlag(["-functions"], default=False)
    call_tree: bool = CLIPresenceFlag(["-calltree"], default=False)
    source: bool = CLIPresenceFlag(["-source"], default=False)

    metrics: str | None = CLIOption(default=None, emit=["-metrics", "{}"])

    add_opts: list[str] = CLIMultiOption(default_factory=list)


GprofngArgs = Union[GprofngCollectArgs, GprofngDisplayArgs]


@register_typed_executable(["gprofng"])
class GprofngExecutable(TypedExecutable[GprofngArgs]):
    install_executable = InstallScript(
        {
            is_posix: simple_bash_install_script(
                __file__,
                "install_gprofng.sh",
                install_location=Path.cwd() / ".gprofng/bin/gprofng",
            )
        }
    )
