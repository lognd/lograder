# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.cli_args import CLI_ARG_MISSING, CLIArgs, CLIOption
from lograder.process.registry.bash import (
    BashCommandArgs,
    BashExecutable,
    BashScriptArgs,
)


class EchoArgs(CLIArgs):
    program: str = CLIOption(emit=["{}"], position=0)
    text: str = CLIOption(emit=["{}"], position=1)


class ScriptInvocationArgs(CLIArgs):
    script_path: Path = CLIOption(emit=["{}"], position=0)
    arg1: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["{}"],
        position=1,
    )
    arg2: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["{}"],
        position=2,
    )


class EmptyArgs(CLIArgs):
    missing: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["{}"],
    )


class BadEmptyTokenArgs(CLIArgs):
    bad: str = CLIOption(emitter=lambda _: [""])


def test_bash_command_args_minimal_emit() -> None:
    args = BashCommandArgs[EchoArgs](
        command=EchoArgs(program="echo", text="hello"),
    )
    assert args.emit() == ["-c", "echo hello"]


def test_bash_command_args_quotes_shell_sensitive_tokens() -> None:
    args = BashCommandArgs[EchoArgs](
        command=EchoArgs(program="echo", text="hello world"),
    )
    emitted = args.emit()
    assert emitted[0] == "-c"
    assert emitted[1] == "echo 'hello world'"


def test_bash_command_args_full_emit() -> None:
    args = BashCommandArgs[EchoArgs](
        command=EchoArgs(program="echo", text="hello world"),
        login=True,
        interactive=False,
        no_profile=True,
        no_rc=False,
        restricted=True,
        posix=True,
        errexit=True,
        nounset=True,
        xtrace=True,
    )

    toks = [
        "--login",
        "--noprofile",
        "-r",
        "--posix",
        "-e",
        "-u",
        "-x",
        "-c",
        "echo 'hello world'",
    ]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str


def test_bash_script_args_minimal_emit(tmp_path) -> None:
    file = tmp_path / "run.sh"
    file.touch()
    args = BashScriptArgs(
        script=file,
    )
    assert args.emit() == [str(file.resolve())]


def test_bash_script_args_full_emit(tmp_path) -> None:
    file = tmp_path / "run.sh"
    file.touch()
    args = BashScriptArgs(
        script=file,
        posix=True,
        errexit=True,
        nounset=True,
        xtrace=True,
    )

    toks = ["--posix", "-e", "-u", "-x", str(file.resolve())]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    assert args.emit() == [
        "--posix",
        "-e",
        "-u",
        "-x",
        str(file.resolve()),
    ]


def test_bash_executable_registered_command() -> None:
    assert BashExecutable.executable is not None
    assert BashExecutable.executable.command == ["bash"]


def test_bash_command_rejects_nested_args_that_emit_nothing() -> None:
    with pytest.raises(ValidationError):
        BashCommandArgs[EmptyArgs](command=EmptyArgs())


def test_bash_script_rejects_nested_args_that_emit_nothing() -> None:
    with pytest.raises(ValidationError):
        BashScriptArgs(script="")


def test_bash_command_rejects_nested_args_with_empty_token() -> None:
    with pytest.raises(ValidationError):
        BashCommandArgs[BadEmptyTokenArgs](command=BadEmptyTokenArgs(bad="x"))


def test_bash_script_rejects_invalid_file() -> None:
    with pytest.raises(ValidationError):
        BashScriptArgs(script=Path("does_not_exist.sh"))


def test_bash_common_rejects_no_profile_without_login_command_mode() -> None:
    with pytest.raises(ValidationError):
        BashCommandArgs[EchoArgs](
            command=EchoArgs(program="echo", text="hi"),
            no_profile=True,
        )


def test_bash_common_rejects_no_profile_without_login_script_mode() -> None:
    with pytest.raises(ValidationError):
        BashScriptArgs(
            script=Path("run.sh"),
            no_profile=True,
        )


def test_bash_common_rejects_no_rc_with_interactive_command_mode() -> None:
    with pytest.raises(ValidationError):
        BashCommandArgs[EchoArgs](
            command=EchoArgs(program="echo", text="hi"),
            interactive=True,
            no_rc=True,
        )


def test_bash_common_rejects_no_rc_with_interactive_script_mode() -> None:
    with pytest.raises(ValidationError):
        BashScriptArgs(
            script=Path("run.sh"),
            interactive=True,
            no_rc=True,
        )


def test_bash_command_accepts_login_with_no_profile() -> None:
    args = BashCommandArgs[EchoArgs](
        command=EchoArgs(program="echo", text="hi"),
        login=True,
        no_profile=True,
    )
    emitted = args.emit()
    assert "--login" in emitted
    assert "--noprofile" in emitted


def test_bash_script_accepts_login_with_no_profile(tmp_path) -> None:
    file = tmp_path / "run.sh"
    file.touch()
    args = BashScriptArgs(
        script=file,
        login=True,
        no_profile=True,
    )
    emitted = args.emit()
    assert "--login" in emitted
    assert "--noprofile" in emitted


def test_bash_command_args_quotes_single_quotes_correctly() -> None:
    args = BashCommandArgs[EchoArgs](
        command=EchoArgs(program="echo", text="it's fine"),
    )
    emitted = args.emit()
    assert emitted[0] == "-c"
    assert emitted[1] == "echo 'it'\"'\"'s fine'"
