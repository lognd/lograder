# mypy: ignore-errors
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


# --- Real executable tests ---

import shutil as _shutil  # noqa: E402
import subprocess as _subprocess  # noqa: E402

_CLANG_AVAILABLE = bool(_shutil.which("clang"))
_CLANGXX_AVAILABLE = bool(_shutil.which("clang++"))

_HELLO_C = '#include <stdio.h>\nint main(void){puts("ok");return 0;}\n'
_HELLO_CPP = '#include <iostream>\nint main(){std::cout<<"ok"<<std::endl;}\n'


@pytest.mark.skipif(not _CLANG_AVAILABLE, reason="clang not available")
def test_clang_real_compiles_c_file(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "main.c"
    src.write_text(_HELLO_C, encoding="utf-8")
    out = tmp_path / "main"
    exe = ClangExecutable()
    args = ClangArgs(
        input=[src],
        output=out,
        standard=ClangCStandard.C11,
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


@pytest.mark.skipif(not _CLANG_AVAILABLE, reason="clang not available")
def test_clang_real_compile_only(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "foo.c"
    src.write_text("int add(int a, int b){return a+b;}\n", encoding="utf-8")
    obj = tmp_path / "foo.o"
    exe = ClangExecutable()
    args = ClangArgs(
        input=[src],
        output=obj,
        standard=ClangCStandard.C11,
        compile_only=True,
        warnings_all=False,
        warnings_extra=False,
    )
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
    assert obj.exists()


@pytest.mark.skipif(not _CLANGXX_AVAILABLE, reason="clang++ not available")
def test_clangxx_real_compiles_cpp_file(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions
    from lograder.process.registry.clang import (
        ClangCXXStandard,
        ClangXXArgs,
        ClangXXExecutable,
    )

    src = tmp_path / "main.cpp"
    src.write_text(_HELLO_CPP, encoding="utf-8")
    out = tmp_path / "main"
    exe = ClangXXExecutable()
    args = ClangXXArgs(
        input=[src],
        output=out,
        standard=ClangCXXStandard.CXX17,
        warnings_all=False,
        warnings_extra=False,
    )
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
    assert out.exists()
