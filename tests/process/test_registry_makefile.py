# type: ignore

from __future__ import annotations

from lograder.process.cli_args import CLI_ARG_MISSING
from lograder.process.registry.makefile import MakefileArgs, MakefileExecutable


def test_makefile_args_defaults() -> None:
    args = MakefileArgs()
    assert args.emit() == ["-j8"]


def test_makefile_args_with_target() -> None:
    args = MakefileArgs(target="all", jobs=4)
    assert args.emit() == ["all", "-j4"]


def test_makefile_args_omits_missing_target() -> None:
    args = MakefileArgs(target=CLI_ARG_MISSING(), jobs=2)
    assert args.emit() == ["-j2"]


def test_makefile_executable_registered_command() -> None:
    assert MakefileExecutable.executable is not None
    assert MakefileExecutable.executable.command == ["make"]
