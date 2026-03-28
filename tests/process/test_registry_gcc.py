# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.common import CStandard, CXXStandard, find_missing
from lograder.process.registry.gcc import (
    GCCArgs,
    GCCExecutable,
    GNUOptimizationLevel,
    GNUStandard,
    GNUXXStandard,
    GXXArgs,
    GXXExecutable,
)


def test_gnu_standard_is_superset_of_c_standard() -> None:
    assert find_missing(CStandard, GNUStandard) == set()


def test_gnuxx_standard_is_superset_of_cxx_standard() -> None:
    assert find_missing(CXXStandard, GNUXXStandard) == set()


def test_gcc_args_defaults_emit() -> None:
    args = GCCArgs(
        input=[Path("main.c")],
        output=Path("main.o"),
        standard=GNUStandard.C11,
    )

    toks = ["main.c", "-o main.o", "-std=c11", "-Wall", "-Wextra", "-O0"]
    args = " ".join(args.emit())
    for tok in toks:
        assert tok in args


def test_gcc_args_full_emit() -> None:
    args = GCCArgs(
        input=[Path("main.c"), Path("util.c")],
        output=Path("prog"),
        standard=GNUStandard.GNU17,
        optimization_level=GNUOptimizationLevel.AGGRESSIVE,
        preprocess_only=True,
        assemble_only=False,
        compile_only=False,
        debug_symbols=True,
        sanitizers=["address", "undefined"],
        include_dirs=[Path("include")],
        library_dirs=[Path("lib")],
        libraries=["m"],
        warnings_all=False,
        warnings_extra=False,
        warnings_pedantic=True,
        warnings_error=True,
    )
    assert args.emit() == [
        "main.c",
        "util.c",
        "-o",
        "prog",
        "-std=gnu17",
        "-E",
        "-g",
        "-fsanitize=address,undefined",
        "-Iinclude",
        "-Llib",
        "-lm",
        "-pedantic",
        "-Werror",
        "-O3",
    ]


def test_gxx_args_defaults_emit() -> None:
    args = GXXArgs(
        input=[Path("main.cpp")],
        output=Path("main.o"),
        standard=GNUXXStandard.CXX20,
    )
    assert args.emit() == [
        "main.cpp",
        "-o",
        "main.o",
        "-std=c++20",
        "-Wall",
        "-Wextra",
        "-O0",
    ]


def test_gxx_args_custom_optimization_emit() -> None:
    args = GXXArgs(
        input=[Path("main.cpp")],
        output=Path("prog"),
        standard=GNUXXStandard.GNUXX23,
        optimization_level=GNUOptimizationLevel.FAST,
    )
    assert args.emit() == [
        "main.cpp",
        "-o",
        "prog",
        "-std=gnu++23",
        "-Wall",
        "-Wextra",
        "-Ofast",
    ]


def test_gcc_executable_registered_command() -> None:
    assert GCCExecutable.executable is not None
    assert GCCExecutable.executable.command == ["gcc"]


def test_gxx_executable_registered_command() -> None:
    assert GXXExecutable.executable is not None
    assert GXXExecutable.executable.command == ["g++"]


def test_gcc_requires_at_least_one_input() -> None:
    with pytest.raises(ValidationError):
        GCCArgs(
            input=[],
            output=Path("prog"),
            standard=GNUStandard.C11,
        )


def test_gcc_output_should_not_be_empty_path() -> None:
    with pytest.raises(ValidationError):
        GCCArgs(
            input=[Path("main.c")],
            output=Path(""),
            standard=GNUStandard.C11,
        )


def test_gcc_preprocess_and_compile_only_should_be_mutually_exclusive() -> None:
    with pytest.raises(ValidationError):
        GCCArgs(
            input=[Path("main.c")],
            output=Path("prog"),
            standard=GNUStandard.C11,
            preprocess_only=True,
            compile_only=True,
        )


def test_gcc_assemble_only_and_preprocess_only_should_be_mutually_exclusive() -> None:
    with pytest.raises(ValidationError):
        GCCArgs(
            input=[Path("main.c")],
            output=Path("prog"),
            standard=GNUStandard.C11,
            preprocess_only=True,
            assemble_only=True,
        )
