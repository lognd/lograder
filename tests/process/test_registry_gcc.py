from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.cli_args import CLI_ARG_MISSING
from lograder.process.registry.gcc import (
    GCCArgs,
    GCCExecutable,
    GNUOptimizationLevel,
    GNUStandard,
    GNUXXStandard,
    GXXArgs,
    GXXExecutable,
)


def test_gcc_args_basic_emit() -> None:
    args = GCCArgs(
        input=[Path("a.c"), Path("b.c")],
        output=Path("a.out"),
        standard=GNUStandard.C11,
    )

    toks = ["a.c", "b.c", "-o a.out", "-std=c11", "-Wall", "-Wextra"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    emitted = set(args.emit())
    assert "a.c" in emitted
    assert "b.c" in emitted
    assert "-o" in emitted
    assert "a.out" in emitted
    assert "-std=c11" in emitted
    assert "-Wall" in emitted
    assert "-Wextra" in emitted


def test_gcc_args_full_emit() -> None:
    args = GCCArgs(
        input=[Path("main.c")],
        output=Path("main"),
        standard=GNUStandard.GNU17,
        optimization_level=GNUOptimizationLevel.AGGRESSIVE,
        debug_symbols=True,
        sanitizers=["address", "undefined"],
        include_dirs=[Path("include")],
        library_dirs=[Path("lib")],
        libraries=["m", "pthread"],
        defines={"NDEBUG": None, "LEVEL": 3, "TRACE": True},
        compile_options=["-fno-omit-frame-pointer"],
        linker_options=["z,defs"],
        warnings_pedantic=True,
        warnings_error=True,
        position_independent_code=True,
        shared=True,
        pipe=True,
        pthread=True,
    )

    toks = [
        "main.c",
        "-o main",
        "-std=gnu17",
        "-O3",
        "-g",
        "-fsanitize=address,undefined",
        "-Iinclude",
        "-Llib",
        "-lm",
        "-lpthread",
        "-DNDEBUG",
        "-DLEVEL=3",
        "-DTRACE=1",
        "-fno-omit-frame-pointer",
        "-Wl,z,defs",
        "-pedantic",
        "-Werror",
        "-fPIC",
        "-shared",
        "-pipe",
        "-pthread",
    ]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str


def test_gcc_args_omits_missing_optimization() -> None:
    args = GCCArgs(
        input=[Path("main.c")],
        output=Path("main"),
        standard=GNUStandard.C23,
        optimization_level=CLI_ARG_MISSING(),
    )
    assert not any(tok.startswith("-O") for tok in args.emit())


def test_gxx_args_basic_emit() -> None:
    args = GXXArgs(
        input=[Path("main.cpp")],
        output=Path("main"),
        standard=GNUXXStandard.CXX20,
    )

    toks = ["main.cpp", "-o main", "-std=c++20", "-Wall", "-Wextra"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str


def test_gxx_args_full_emit() -> None:
    args = GXXArgs(
        input=[Path("main.cpp")],
        output=Path("main"),
        standard=GNUXXStandard.GNUXX23,
        optimization_level=GNUOptimizationLevel.FAST,
        permissive=True,
        pthread=True,
    )

    toks = [
        "main.cpp",
        "-o main",
        "-std=gnu++23",
        "-Ofast",
        "-fpermissive",
        "-pthread",
    ]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str


def test_gcc_executable_registered_command() -> None:
    assert GCCExecutable.executable is not None
    assert GCCExecutable.executable.command == ["gcc"]


def test_gxx_executable_registered_command() -> None:
    assert GXXExecutable.executable is not None
    assert GXXExecutable.executable.command == ["g++"]


def test_gcc_rejects_empty_input_sequence() -> None:
    with pytest.raises(ValidationError):
        GCCArgs(
            input=[],
            output=Path("a.out"),
            standard=GNUStandard.C11,
        )


def test_gcc_rejects_blank_output_path() -> None:
    with pytest.raises(ValidationError):
        GCCArgs(
            input=[Path("a.c")],
            output=" ",
            standard=GNUStandard.C11,
        )


def test_gcc_rejects_duplicate_sanitizers() -> None:
    with pytest.raises(ValidationError):
        GCCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=GNUStandard.C11,
            sanitizers=["address", "address"],
        )


def test_gcc_rejects_conflicting_pipeline_flags() -> None:
    with pytest.raises(ValidationError):
        GCCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=GNUStandard.C11,
            preprocess_only=True,
            compile_only=True,
        )


def test_gcc_rejects_preprocess_with_link_inputs() -> None:
    with pytest.raises(ValidationError):
        GCCArgs(
            input=[Path("a.c")],
            output=Path("a.out"),
            standard=GNUStandard.C11,
            preprocess_only=True,
            libraries=["m"],
        )


# --- Real executable tests ---

import shutil as _shutil  # noqa: E402
import subprocess as _subprocess  # noqa: E402

_GCC_AVAILABLE = bool(_shutil.which("gcc"))
_GXX_AVAILABLE = bool(_shutil.which("g++"))

_HELLO_C = '#include <stdio.h>\nint main(void){puts("ok");return 0;}\n'
_HELLO_CPP = '#include <iostream>\nint main(){std::cout<<"ok"<<std::endl;}\n'


@pytest.mark.skipif(not _GCC_AVAILABLE, reason="gcc not available")
def test_gcc_real_compiles_and_runs_c_file(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "main.c"
    src.write_text(_HELLO_C, encoding="utf-8")
    out = tmp_path / "main"
    exe = GCCExecutable()
    args = GCCArgs(
        input=[src],
        output=out,
        standard=GNUStandard.C11,
        warnings_all=False,
        warnings_extra=False,
    )
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok, result
    assert result.danger_ok.return_code == 0
    assert out.exists()
    proc = _subprocess.run([str(out)], capture_output=True)
    assert proc.returncode == 0
    assert b"ok" in proc.stdout


@pytest.mark.skipif(not _GCC_AVAILABLE, reason="gcc not available")
def test_gcc_real_compile_only_produces_object(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "foo.c"
    src.write_text("int foo(void){return 1;}\n", encoding="utf-8")
    obj = tmp_path / "foo.o"
    exe = GCCExecutable()
    args = GCCArgs(
        input=[src],
        output=obj,
        standard=GNUStandard.C11,
        compile_only=True,
        warnings_all=False,
        warnings_extra=False,
    )
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
    assert obj.exists()


@pytest.mark.skipif(not _GXX_AVAILABLE, reason="g++ not available")
def test_gxx_real_compiles_cpp_file(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "main.cpp"
    src.write_text(_HELLO_CPP, encoding="utf-8")
    out = tmp_path / "main"
    exe = GXXExecutable()
    args = GXXArgs(
        input=[src],
        output=out,
        standard=GNUXXStandard.CXX17,
        warnings_all=False,
        warnings_extra=False,
    )
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
    assert out.exists()
