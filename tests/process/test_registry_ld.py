# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.ld import LdArgs, LdExecutable


def test_basic_link() -> None:
    args = LdArgs(input=[Path("a.o"), Path("b.o")])
    emitted = args.emit()
    assert "a.o" in emitted
    assert "b.o" in emitted


def test_output_and_entry() -> None:
    args = LdArgs(
        input=[Path("a.o")],
        output=Path("a.out"),
        entry="main",
    )
    emitted = args.emit()
    assert "-o" in emitted and "a.out" in emitted
    assert "-e" in emitted and "main" in emitted


def test_library_linking() -> None:
    args = LdArgs(
        input=[Path("a.o")],
        library_dirs=[Path("/usr/lib")],
        libraries=["m", "pthread"],
    )
    emitted = args.emit()
    assert "-L/usr/lib" in emitted
    assert "-lm" in emitted
    assert "-lpthread" in emitted


def test_map_and_script() -> None:
    args = LdArgs(
        input=[Path("a.o")],
        map_file=Path("map.txt"),
        script=Path("link.ld"),
    )
    emitted = args.emit()
    assert "-Map=map.txt" in emitted
    assert "-T" in emitted and "link.ld" in emitted


def test_flags() -> None:
    args = LdArgs(
        input=[Path("a.o")],
        shared=True,
        gc_sections=True,
        build_id=True,
    )
    emitted = set(args.emit())
    assert "-shared" in emitted
    assert "--gc-sections" in emitted
    assert "--build-id" in emitted


def test_defines() -> None:
    args = LdArgs(
        input=[Path("a.o")],
        defines={"foo": 1, "bar": None},
    )
    emitted = args.emit()
    assert "-defsym=foo=1" in emitted
    assert "-defsym=bar" in emitted


def test_mutually_exclusive_modes() -> None:
    with pytest.raises(ValidationError):
        LdArgs(
            input=[Path("a.o")],
            shared=True,
            static=True,
        )


def test_reject_empty_input() -> None:
    with pytest.raises(ValidationError):
        LdArgs(input=[])


def test_registered() -> None:
    assert LdExecutable.executable is not None
    assert LdExecutable.executable.command == ["ld"]
