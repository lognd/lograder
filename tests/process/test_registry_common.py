# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.common import (
    CompilerArgs,
    CStandard,
    CXXStandard,
    find_missing,
)


def test_find_missing_against_known_standards() -> None:
    missing = find_missing(CStandard, CStandard)
    assert missing == set()


class ConcreteCArgs(CompilerArgs[CStandard]):
    pass


class ConcreteCXXArgs(CompilerArgs[CXXStandard]):
    pass


def test_compiler_args_emit_basic_c_case() -> None:
    args = ConcreteCArgs(
        input=[Path("a.c"), Path("b.c")],
        output=Path("a.out"),
        standard=CStandard.C11,
    )

    toks = ["a.c", "b.c", "-o a.out", "-std=c11", "-Wall", "-Wextra"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    assert set(args.emit()) == {
        "a.c",
        "b.c",
        "-o",
        "a.out",
        "-std=c11",
        "-Wall",
        "-Wextra",
    }


def test_compiler_args_emit_many_optional_flags() -> None:
    args = ConcreteCArgs(
        input=[Path("main.c")],
        output=Path("main.o"),
        standard=CStandard.C17,
        compile_only=True,
        debug_symbols=True,
        sanitizers=["address", "undefined"],
        include_dirs=[Path("include"), Path("vendor/include")],
        library_dirs=[Path("lib")],
        libraries=["m", "pthread"],
        warnings_all=False,
        warnings_extra=False,
        warnings_pedantic=True,
        warnings_error=True,
    )

    assert args.emit() == [
        "main.c",
        "-o",
        "main.o",
        "-std=c17",
        "-c",
        "-g",
        "-fsanitize=address,undefined",
        "-Iinclude",
        "-Ivendor/include",
        "-Llib",
        "-lm",
        "-lpthread",
        "-pedantic",
        "-Werror",
    ]


def test_compiler_args_emit_with_defines_compile_and_linker_options() -> None:
    args = ConcreteCArgs(
        input=[Path("main.c")],
        output=Path("main.o"),
        standard=CStandard.C23,
        defines={
            "NDEBUG": None,
            "LOG_LEVEL": 3,
            "FEATURE_X": True,
            "FEATURE_Y": False,
        },
        compile_options=["-fPIC", "-pthread"],
        linker_options=["-z,relro", "--as-needed"],
    )

    toks = [
        "main.c",
        "-o main.o",
        "-std=c23",
        "-DNDEBUG",
        "-DLOG_LEVEL=3",
        "-DFEATURE_X=1",
        "-DFEATURE_Y=0",
        "-fPIC",
        "-pthread",
        "-Wl,-z,relro",
        "-Wl,--as-needed",
        "-Wall",
        "-Wextra",
    ]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    emitted = set(args.emit())

    assert "-DNDEBUG" in emitted
    assert "-DLOG_LEVEL=3" in emitted
    assert "-DFEATURE_X=1" in emitted
    assert "-DFEATURE_Y=0" in emitted
    assert "-fPIC" in emitted
    assert "-pthread" in emitted
    assert "-Wl,-z,relro" in emitted
    assert "-Wl,--as-needed" in emitted


def test_compiler_args_emit_cxx_case() -> None:
    args = ConcreteCXXArgs(
        input=[Path("main.cpp")],
        output=Path("prog"),
        standard=CXXStandard.CXX20,
        warnings_pedantic=True,
    )

    toks = ["main.cpp", "-o prog", "-std=c++20", "-Wall", "-Wextra", "-pedantic"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    assert set(args.emit()) == {
        "main.cpp",
        "-o",
        "prog",
        "-std=c++20",
        "-Wall",
        "-Wextra",
        "-pedantic",
    }


def test_compiler_args_rejects_empty_input() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[],
            output=Path("a.out"),
            standard=CStandard.C11,
        )


def test_compiler_args_rejects_blank_input_string() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=["", Path("b.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
        )


def test_compiler_args_rejects_blank_output_string() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output="",
            standard=CStandard.C11,
        )


def test_compiler_args_rejects_output_directory(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=out_dir,
            standard=CStandard.C11,
        )


def test_compiler_args_rejects_mutually_exclusive_pipeline_flags() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            preprocess_only=True,
            compile_only=True,
        )


def test_compiler_args_rejects_blank_include_dir_string() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            include_dirs=[""],
        )


def test_compiler_args_rejects_blank_library_dir_string() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            library_dirs=[" "],
        )


def test_compiler_args_rejects_blank_library_name() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            libraries=["m", ""],
        )


def test_compiler_args_rejects_blank_compile_option() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            compile_options=["-fPIC", ""],
        )


def test_compiler_args_rejects_blank_linker_option() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            linker_options=["--as-needed", " "],
        )


def test_compiler_args_rejects_blank_sanitizer() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            sanitizers=["address", ""],
        )


def test_compiler_args_rejects_duplicate_sanitizer() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            sanitizers=["address", "address"],
        )


def test_compiler_args_rejects_comma_expanded_sanitizer() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            sanitizers=["address,undefined"],
        )


def test_compiler_args_rejects_blank_define_key() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            defines={"": 1},
        )


def test_compiler_args_rejects_define_key_with_equals() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            defines={"BAD=KEY": 1},
        )


def test_compiler_args_rejects_link_inputs_during_preprocess_only_libraries() -> None:
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            preprocess_only=True,
            libraries=["m"],
        )


def test_compiler_args_rejects_link_inputs_during_preprocess_only_library_dirs() -> (
    None
):
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            preprocess_only=True,
            library_dirs=[Path("lib")],
        )


def test_compiler_args_rejects_link_inputs_during_preprocess_only_linker_options() -> (
    None
):
    with pytest.raises(ValidationError):
        ConcreteCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=CStandard.C11,
            preprocess_only=True,
            linker_options=["--as-needed"],
        )
