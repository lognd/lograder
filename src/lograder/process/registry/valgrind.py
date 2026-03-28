from pathlib import Path
from typing import Generic, TypeVar

from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    CLIArgs,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable

T = TypeVar("T", bound=CLIArgs)


class ValgrindArgs(CLIArgs, Generic[T]):
    exec: T = CLIOption(emitter=lambda x: x.emit(), position=-1)
    xml_file: Path | CLI_ARG_MISSING = CLIOption(
        emit=["--xml-file={}"], default=CLI_ARG_MISSING()
    )

    leak_check: bool = CLIPresenceFlag(emit=["--leak-check=full"], default=True)
    xml: bool = CLIPresenceFlag(emit=["--xml=yes"], default=True)
    quiet: bool = CLIPresenceFlag(emit=["-q"], default=True)
    child_silent_after_fork: bool = CLIPresenceFlag(
        emit=["--child-silent-after-fork=yes"], default=True
    )


@register_typed_executable(["valgrind"])
class ValgrindExecutable(TypedExecutable[ValgrindArgs]): ...
