# mypy: ignore-errors
# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.lld import (
    LldElfArgs,
    LldExecutable,
    LldLinkArgs,
)


def test_elf_basic() -> None:
    args = LldElfArgs(input=[Path("a.o")])
    assert "a.o" in args.emit()


def test_elf_output_and_flags() -> None:
    args = LldElfArgs(
        input=[Path("a.o")],
        output=Path("a.out"),
        shared=True,
        gc_sections=True,
    )
    emitted = args.emit()
    assert "-o" in emitted
    assert "a.out" in emitted
    assert "-shared" in emitted
    assert "--gc-sections" in emitted


def test_elf_libraries() -> None:
    args = LldElfArgs(
        input=[Path("a.o")],
        library_dirs=[Path("/usr/lib")],
        libraries=["m"],
    )
    emitted = args.emit()
    assert "-L/usr/lib" in emitted
    assert "-lm" in emitted


def test_elf_modes_conflict() -> None:
    with pytest.raises(ValidationError):
        LldElfArgs(
            input=[Path("a.o")],
            shared=True,
            static=True,
        )


def test_link_basic() -> None:
    args = LldLinkArgs(input=[Path("a.obj")])
    emitted = args.emit()
    assert "link" in emitted
    assert "a.obj" in emitted


def test_link_output_and_flags() -> None:
    args = LldLinkArgs(
        input=[Path("a.obj")],
        output=Path("a.exe"),
        debug=True,
    )
    emitted = args.emit()
    assert "/OUT:a.exe" in emitted
    assert "/DEBUG" in emitted


def test_link_requires_input() -> None:
    with pytest.raises(ValidationError):
        LldLinkArgs(input=[])


def test_registered() -> None:
    assert LldExecutable.executable is not None
    assert LldExecutable.executable.command == ["ld.lld"]


# --- Real executable tests ---

import shutil as _shutil
import subprocess as _subprocess

_LLD_AVAILABLE = bool(_shutil.which("ld.lld"))
_GCC_AVAILABLE = bool(_shutil.which("gcc"))


@pytest.mark.skipif(
    not (_LLD_AVAILABLE and _GCC_AVAILABLE), reason="ld.lld and gcc both required"
)
def test_lld_real_creates_shared_library(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "foo.c"
    src.write_text("int foo(void){return 99;}\n", encoding="utf-8")
    obj = tmp_path / "foo.o"
    _subprocess.run(
        ["gcc", "-c", "-fPIC", str(src), "-o", str(obj)],
        check=True,
        capture_output=True,
    )
    assert obj.exists()

    out_lib = tmp_path / "libfoo.so"
    exe = LldExecutable()
    args = LldElfArgs(input=[obj], output=out_lib, shared=True)
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
    assert out_lib.exists()
