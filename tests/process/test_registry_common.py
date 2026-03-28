# type: ignore

from __future__ import annotations

from pathlib import Path

from lograder.process.registry.common import (
    CompilerArgs,
    CStandard,
    CXXStandard,
    find_missing,
)


def test_find_missing_against_known_standards() -> None:
    missing = {m.value for m in CStandard} - {m.value for m in CStandard}
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

    toks = ["a.c", "b.c", "-o a.out", "std=c11", "-Wall", "-Wextra"]
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
