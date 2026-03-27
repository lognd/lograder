from pathlib import Path

from lograder.process.cli_args import CLI_ARG_MISSING, CLIArgs, CLIOption
from lograder.process.executable import TypedExecutable, register_typed_executable


class CMakeConfigureArgs(CLIArgs):
    source_dir: Path = CLIOption(default=".", emit=["-S", "{}"])
    build_dir: Path = CLIOption(default="build", emit=["-B", "{}"])


class CMakeBuildArgs(CLIArgs):
    build_dir: Path = CLIOption(default="build", emit=["--build", "{}"])
    target: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--target", "{}"]
    )


@register_typed_executable(["cmake"])
class CMakeExecutable(TypedExecutable[CMakeConfigureArgs | CMakeBuildArgs]): ...
