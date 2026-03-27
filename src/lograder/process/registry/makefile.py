from lograder.process.cli_args import CLI_ARG_MISSING, CLIArgs, CLIOption
from lograder.process.executable import TypedExecutable, register_typed_executable


class MakefileArgs(CLIArgs):
    target: str | CLI_ARG_MISSING = CLIOption(default=CLI_ARG_MISSING(), emit=["{}"])
    jobs: int = CLIOption(default=8, emit=["-j{}"])


@register_typed_executable(["make"])
class MakefileExecutable(TypedExecutable[MakefileArgs]): ...
