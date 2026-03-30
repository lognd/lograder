# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.nasm import (
    NasmArgs,
    NasmExecutable,
    NasmFormat,
)


def test_basic_assembly(tmp_path) -> None:
    a = tmp_path / "a.asm"
    a.touch()
    args = NasmArgs(input=[a])
    assert str(a) in args.emit()


def test_output_and_format(tmp_path) -> None:
    a = tmp_path / "a.asm"
    a.touch()
    args = NasmArgs(
        input=[a],
        output=Path("a.o"),
        format=NasmFormat.ELF64,
    )
    emitted = args.emit()
    assert "-o" in emitted and "a.o" in emitted
    assert "-f" in emitted and "elf64" in emitted


def test_debug_and_preproc(tmp_path) -> None:
    a = tmp_path / "a.asm"
    a.touch()
    args = NasmArgs(
        input=[a],
        debug=True,
        preproc_only=True,
    )
    emitted = args.emit()
    assert "-g" in emitted
    assert "-E" in emitted


def test_include_and_defines(tmp_path) -> None:
    a = tmp_path / "a.asm"
    a.touch()
    args = NasmArgs(
        input=[a],
        include_dirs=[Path("include")],
        defines={"FOO": 1, "BAR": None},
    )
    emitted = args.emit()
    assert "-Iinclude" in emitted
    assert "-DFOO=1" in emitted
    assert "-DBAR" in emitted


def test_warnings(tmp_path) -> None:
    a = tmp_path / "a.asm"
    a.touch()
    args = NasmArgs(
        input=[a],
        warnings=["all"],
        disable_warnings=["macro"],
    )
    emitted = args.emit()
    assert "-w+all" in emitted
    assert "-w-macro" in emitted


def test_list_file(tmp_path) -> None:
    a = tmp_path / "a.asm"
    a.touch()
    args = NasmArgs(
        input=[a],
        list_file=Path("out.lst"),
    )
    emitted = args.emit()
    assert "-l" in emitted
    assert "out.lst" in emitted


def test_add_opts_passthrough(tmp_path) -> None:
    a = tmp_path / "a.asm"
    a.touch()
    args = NasmArgs(
        input=[a],
        add_opts=["--reproducible"],
    )
    assert "--reproducible" in args.emit()


def test_reject_empty_input(tmp_path) -> None:
    a = tmp_path / "a.asm"
    a.touch()
    with pytest.raises(ValidationError):
        NasmArgs(input=[])


def test_reject_blank_input(tmp_path) -> None:
    a = tmp_path / "a.asm"
    a.touch()
    with pytest.raises(ValidationError):
        NasmArgs(input=[Path("")])


def test_registered(tmp_path) -> None:
    a = tmp_path / "a.asm"
    a.touch()
    assert NasmExecutable.executable is not None
    assert NasmExecutable.executable.command == ["nasm"]
