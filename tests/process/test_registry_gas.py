# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.gas import GasArgs, GasExecutable


def test_basic_assembly(tmp_path: Path) -> None:
    src = tmp_path / "a.s"
    src.write_text("")

    args = GasArgs(input=[src])

    assert args.emit() == [str(src)]


def test_output_and_arch(tmp_path: Path) -> None:
    src = tmp_path / "a.s"
    src.write_text("")

    args = GasArgs(
        input=[src],
        output=tmp_path / "a.o",
        architecture="x86-64",
    )

    emitted = args.emit()
    assert str(src) in emitted
    assert "-o" in emitted
    assert str(tmp_path / "a.o") in emitted
    assert "-march=x86-64" in emitted


def test_debug_and_warnings(tmp_path: Path) -> None:
    src = tmp_path / "a.s"
    src.write_text("")

    args = GasArgs(
        input=[src],
        debug=True,
        warnings=True,
        fatal_warnings=True,
    )

    emitted = args.emit()
    assert str(src) in emitted
    assert "-g" in emitted
    assert "--warn" in emitted
    assert "--fatal-warnings" in emitted


def test_include_and_defines(tmp_path: Path) -> None:
    src = tmp_path / "a.s"
    src.write_text("")

    include_dir = tmp_path / "include"
    include_dir.mkdir()

    args = GasArgs(
        input=[src],
        include_dirs=[include_dir],
        defines={"FOO": 1, "BAR": None},
    )

    emitted = args.emit()
    assert str(src) in emitted
    assert f"-I{include_dir}" in emitted
    assert "-DFOO=1" in emitted
    assert "-DBAR" in emitted


def test_listing(tmp_path: Path) -> None:
    src = tmp_path / "a.s"
    src.write_text("")

    listing = tmp_path / "out.lst"

    args = GasArgs(
        input=[src],
        listing=listing,
    )

    emitted = args.emit()
    assert str(src) in emitted
    assert f"-al={listing}" in emitted


def test_add_opts_passthrough(tmp_path: Path) -> None:
    src = tmp_path / "a.s"
    src.write_text("")

    args = GasArgs(
        input=[src],
        add_opts=["--gdwarf-5"],
    )

    emitted = args.emit()
    assert str(src) in emitted
    assert "--gdwarf-5" in emitted


def test_reject_empty_input() -> None:
    with pytest.raises(ValidationError):
        GasArgs(input=[])


def test_reject_blank_input_string() -> None:
    with pytest.raises(ValidationError):
        GasArgs(input=["   "])


def test_reject_nonexistent_input_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.s"

    with pytest.raises(ValidationError):
        GasArgs(input=[missing])


def test_registered() -> None:
    assert GasExecutable.executable is not None
    assert GasExecutable.executable.command == ["as"]
