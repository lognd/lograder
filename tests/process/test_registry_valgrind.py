# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.cli_args import CLI_ARG_MISSING, CLIArgs, CLIOption
from lograder.process.registry.valgrind import (
    ValgrindArgs,
    ValgrindExecutable,
    ValgrindLeakCheck,
)


class EchoArgs(CLIArgs):
    program: str = CLIOption(emit=["{}"], position=0)
    arg: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["{}"],
        position=1,
    )


def test_valgrind_args_defaults() -> None:
    args = ValgrindArgs[EchoArgs](
        command=EchoArgs(program="./a.out"),
    )

    emitted = args.emit()
    assert "--leak-check=full" in emitted
    assert emitted[-1] == "./a.out"


def test_valgrind_args_full_emit() -> None:
    args = ValgrindArgs[EchoArgs](
        command=EchoArgs(program="./app", arg="input.txt"),
        xml=True,
        xml_file=Path("valgrind.xml"),
        leak_check=ValgrindLeakCheck.FULL,
        quiet=True,
        child_silent_after_fork=True,
        track_origins=True,
        error_exitcode=99,
    )

    toks = [
        "--xml=yes",
        "--xml-file=valgrind.xml",
        "--leak-check=full",
        "-q",
        "--child-silent-after-fork=yes",
        "--track-origins=yes",
        "--error-exitcode=99",
        "./app",
        "input.txt",
    ]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    emitted = args.emit()
    assert emitted[-2:] == ["./app", "input.txt"]


def test_valgrind_args_with_xml_disabled_omits_xml_tokens() -> None:
    args = ValgrindArgs[EchoArgs](
        command=EchoArgs(program="./a.out"),
        xml=False,
        xml_file=CLI_ARG_MISSING(),
    )

    emitted = args.emit()
    assert "--xml=yes" not in emitted
    assert not any(tok.startswith("--xml-file=") for tok in emitted)


def test_valgrind_args_supports_leak_check_summary() -> None:
    args = ValgrindArgs[EchoArgs](
        command=EchoArgs(program="./a.out"),
        leak_check=ValgrindLeakCheck.SUMMARY,
    )
    assert "--leak-check=summary" in args.emit()


def test_valgrind_args_supports_leak_check_no() -> None:
    args = ValgrindArgs[EchoArgs](
        command=EchoArgs(program="./a.out"),
        leak_check=ValgrindLeakCheck.NO,
    )
    assert "--leak-check=no" in args.emit()


def test_valgrind_args_omits_missing_optional_fields() -> None:
    args = ValgrindArgs[EchoArgs](
        command=EchoArgs(program="./a.out"),
        xml=False,
        xml_file=CLI_ARG_MISSING(),
        error_exitcode=CLI_ARG_MISSING(),
    )

    emitted = args.emit()
    assert "--xml=yes" not in emitted
    assert not any(tok.startswith("--xml-file=") for tok in emitted)
    assert not any(tok.startswith("--error-exitcode=") for tok in emitted)


def test_valgrind_executable_registered_command() -> None:
    assert ValgrindExecutable.executable is not None
    assert ValgrindExecutable.executable.command == ["valgrind"]


def test_valgrind_rejects_blank_xml_path() -> None:
    with pytest.raises(ValidationError):
        ValgrindArgs[EchoArgs](
            command=EchoArgs(program="./a.out"),
            xml=True,
            xml_file=" ",
        )


def test_valgrind_rejects_nonpositive_error_exitcode_zero() -> None:
    with pytest.raises(ValidationError):
        ValgrindArgs[EchoArgs](
            command=EchoArgs(program="./a.out"),
            error_exitcode=0,
        )


def test_valgrind_rejects_nonpositive_error_exitcode_negative() -> None:
    with pytest.raises(ValidationError):
        ValgrindArgs[EchoArgs](
            command=EchoArgs(program="./a.out"),
            error_exitcode=-7,
        )


def test_valgrind_rejects_xml_file_without_xml_enabled() -> None:
    with pytest.raises(ValidationError):
        ValgrindArgs[EchoArgs](
            command=EchoArgs(program="./a.out"),
            xml=False,
            xml_file=Path("valgrind.xml"),
        )


def test_valgrind_rejects_empty_nested_command() -> None:
    class EmptyArgs(CLIArgs):
        nothing: str | CLI_ARG_MISSING = CLIOption(
            default=CLI_ARG_MISSING(),
            emit=["{}"],
        )

    with pytest.raises(ValidationError):
        ValgrindArgs[EmptyArgs](
            command=EmptyArgs(),
        )
