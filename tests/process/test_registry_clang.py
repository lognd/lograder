# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.clang import (
    ClangArgs,
    ClangCStandard,
    ClangExecutable,
)


def test_basic_compile() -> None:
    args = ClangArgs(input=[Path("a.c")])
    emitted = args.emit()
    assert "a.c" in emitted


def test_output_and_standard() -> None:
    args = ClangArgs(
        input=[Path("a.c")],
        output=Path("a.out"),
        standard=ClangCStandard.C11,
    )
    emitted = args.emit()
    assert "-o" in emitted and "a.out" in emitted
    assert "-std=c11" in emitted


def test_compile_only_flag() -> None:
    args = ClangArgs(
        input=[Path("a.c")],
        compile_only=True,
    )
    assert "-c" in args.emit()


def test_include_and_libraries() -> None:
    args = ClangArgs(
        input=[Path("a.c")],
        include_dirs=[Path("include")],
        libraries=["m"],
    )
    emitted = args.emit()
    assert "-Iinclude" in emitted
    assert "-lm" in emitted


def test_defines() -> None:
    args = ClangArgs(
        input=[Path("a.c")],
        defines={"FOO": 1, "BAR": None},
    )
    emitted = args.emit()
    assert "-DFOO=1" in emitted
    assert "-DBAR" in emitted


def test_pipeline_conflict() -> None:
    with pytest.raises(ValidationError):
        ClangArgs(
            input=[Path("a.c")],
            preprocess_only=True,
            compile_only=True,
        )


def test_reject_empty_input() -> None:
    with pytest.raises(ValidationError):
        ClangArgs(input=[])


def test_registered() -> None:
    assert ClangExecutable.executable is not None
    assert ClangExecutable.executable.command == ["clang"]
