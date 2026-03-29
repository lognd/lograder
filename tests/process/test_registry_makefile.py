# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.cli_args import CLI_ARG_MISSING
from lograder.process.registry.makefile import MakefileArgs, MakefileExecutable


def test_makefile_args_defaults() -> None:
    args = MakefileArgs()
    assert args.emit() == []


def test_makefile_args_with_target_only() -> None:
    args = MakefileArgs(target="all")
    assert args.emit() == ["all"]


def test_makefile_args_with_jobs_only() -> None:
    args = MakefileArgs(jobs=8)
    assert args.emit() == ["-j8"]


def test_makefile_args_with_target_and_jobs() -> None:
    args = MakefileArgs(target="install", jobs=4)

    toks = ["-j4", "install"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    assert args.emit() == ["-j4", "install"]


def test_makefile_args_full_emit() -> None:
    args = MakefileArgs(
        directory=Path("project"),
        makefile=Path("GNUmakefile"),
        jobs=16,
        always_make=True,
        keep_going=True,
        silent=False,
        just_print=True,
        print_directory=True,
        variables={
            "CC": "clang",
            "CFLAGS": "-O2 -Wall",
            "MODE": "release",
        },
        target="build",
    )

    toks = [
        "-C project",
        "-f GNUmakefile",
        "-j16",
        "-B",
        "-k",
        "-n",
        "-w",
        "CC=clang",
        "CFLAGS=-O2 -Wall",
        "MODE=release",
        "build",
    ]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    emitted = args.emit()
    assert emitted[-1] == "build"
    assert "-C" in emitted
    assert "project" in emitted
    assert "-f" in emitted
    assert "GNUmakefile" in emitted
    assert "-j16" in emitted
    assert "-B" in emitted
    assert "-k" in emitted
    assert "-n" in emitted
    assert "-w" in emitted
    assert "CC=clang" in emitted
    assert "CFLAGS=-O2 -Wall" in emitted
    assert "MODE=release" in emitted


def test_makefile_args_omits_missing_optional_fields() -> None:
    args = MakefileArgs(
        directory=CLI_ARG_MISSING(),
        makefile=CLI_ARG_MISSING(),
        jobs=CLI_ARG_MISSING(),
        target=CLI_ARG_MISSING(),
        always_make=False,
        keep_going=False,
        silent=False,
        just_print=False,
        print_directory=False,
    )
    assert args.emit() == []


def test_makefile_args_with_only_variables() -> None:
    args = MakefileArgs(
        variables={
            "CC": "gcc",
            "DEBUG": 1,
        }
    )

    toks = ["CC=gcc", "DEBUG=1"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    assert len(args.emit()) == 2


def test_makefile_executable_registered_command() -> None:
    assert MakefileExecutable.executable is not None
    assert MakefileExecutable.executable.command == ["make"]


def test_makefile_rejects_blank_target() -> None:
    with pytest.raises(ValidationError):
        MakefileArgs(target="   ")


def test_makefile_rejects_blank_directory_path() -> None:
    with pytest.raises(ValidationError):
        MakefileArgs(directory=" ")


def test_makefile_rejects_blank_makefile_path() -> None:
    with pytest.raises(ValidationError):
        MakefileArgs(makefile=" ")


def test_makefile_rejects_nonpositive_jobs_zero() -> None:
    with pytest.raises(ValidationError):
        MakefileArgs(jobs=0)


def test_makefile_rejects_nonpositive_jobs_negative() -> None:
    with pytest.raises(ValidationError):
        MakefileArgs(jobs=-3)


def test_makefile_rejects_directory_that_is_a_file(tmp_path: Path) -> None:
    bad_dir = tmp_path / "project"
    bad_dir.write_text("not a directory\n")

    with pytest.raises(ValidationError):
        MakefileArgs(directory=bad_dir)


def test_makefile_rejects_makefile_that_is_directory(tmp_path: Path) -> None:
    bad_makefile = tmp_path / "mk"
    bad_makefile.mkdir()

    with pytest.raises(ValidationError):
        MakefileArgs(makefile=bad_makefile)


def test_makefile_rejects_blank_variable_key() -> None:
    with pytest.raises(ValidationError):
        MakefileArgs(variables={"": "clang"})


def test_makefile_rejects_variable_key_containing_equals() -> None:
    with pytest.raises(ValidationError):
        MakefileArgs(variables={"CC=BAD": "clang"})


def test_makefile_rejects_silent_with_print_directory() -> None:
    with pytest.raises(ValidationError):
        MakefileArgs(silent=True, print_directory=True)
