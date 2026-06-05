# mypy: ignore-errors
# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.ar import ArArgs, ArExecutable, ArOperation


def test_ar_basic_replace() -> None:
    args = ArArgs(
        operation=ArOperation.REPLACE,
        create=True,
        index=True,
        archive=Path("lib.a"),
        files=[Path("a.o"), Path("b.o")],
    )

    assert args.emit() == ["rcs", "lib.a", "a.o", "b.o"]


def test_ar_extract_verbose() -> None:
    args = ArArgs(
        operation=ArOperation.EXTRACT,
        verbose=True,
        archive=Path("lib.a"),
        files=[Path("a.o")],
    )

    assert args.emit() == ["xv", "lib.a", "a.o"]


def test_ar_table_no_files() -> None:
    args = ArArgs(
        operation=ArOperation.TABLE,
        archive=Path("lib.a"),
    )

    assert args.emit() == ["t", "lib.a"]


def test_ar_insert_after_requires_position_member() -> None:
    with pytest.raises(ValidationError):
        ArArgs(
            operation=ArOperation.REPLACE,
            insert_after=True,
            archive=Path("lib.a"),
            files=[Path("a.o")],
        )


def test_ar_insert_after_valid() -> None:
    args = ArArgs(
        operation=ArOperation.REPLACE,
        insert_after=True,
        position_member=Path("ref.o"),
        archive=Path("lib.a"),
        files=[Path("a.o")],
    )

    assert args.emit() == ["ra", "lib.a", "ref.o", "a.o"]


def test_ar_mutually_exclusive_insert_flags() -> None:
    with pytest.raises(ValidationError):
        ArArgs(
            operation=ArOperation.REPLACE,
            insert_after=True,
            insert_before=True,
            position_member=Path("ref.o"),
            archive=Path("lib.a"),
        )


def test_ar_raw_modifiers_passthrough() -> None:
    args = ArArgs(
        operation=ArOperation.REPLACE,
        raw_modifiers="D",
        archive=Path("lib.a"),
        files=[Path("a.o")],
    )

    assert args.emit() == ["rD", "lib.a", "a.o"]


def test_ar_emit_string_contains_expected() -> None:
    args = ArArgs(
        operation=ArOperation.REPLACE,
        create=True,
        index=True,
        archive=Path("lib.a"),
        files=[Path("a.o")],
    )

    assert "rcs lib.a a.o" in " ".join(args.emit())


def test_ar_rejects_blank_archive() -> None:
    with pytest.raises(ValidationError):
        ArArgs(
            operation=ArOperation.REPLACE,
            archive="   ",
        )


def test_ar_executable_registered() -> None:
    assert ArExecutable.executable is not None
    assert ArExecutable.executable.command == ["ar"]


# --- Real executable tests ---

import shutil as _shutil
import subprocess as _subprocess

_AR_AVAILABLE = bool(_shutil.which("ar"))
_GCC_AVAILABLE = bool(_shutil.which("gcc"))


@pytest.mark.skipif(
    not (_AR_AVAILABLE and _GCC_AVAILABLE), reason="ar and gcc both required"
)
def test_ar_real_creates_static_library(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "foo.c"
    src.write_text("int foo(void){return 42;}\n", encoding="utf-8")
    obj = tmp_path / "foo.o"
    _subprocess.run(
        ["gcc", "-c", str(src), "-o", str(obj)], check=True, capture_output=True
    )
    assert obj.exists()

    lib = tmp_path / "libfoo.a"
    exe = ArExecutable()
    args = ArArgs(
        operation=ArOperation.REPLACE,
        create=True,
        index=True,
        archive=lib,
        files=[obj],
    )
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
    assert lib.exists()


@pytest.mark.skipif(
    not (_AR_AVAILABLE and _GCC_AVAILABLE), reason="ar and gcc both required"
)
def test_ar_real_lists_library_table(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "bar.c"
    src.write_text("int bar(void){return 0;}\n", encoding="utf-8")
    obj = tmp_path / "bar.o"
    _subprocess.run(
        ["gcc", "-c", str(src), "-o", str(obj)], check=True, capture_output=True
    )
    lib = tmp_path / "libbar.a"
    _subprocess.run(["ar", "rcs", str(lib), str(obj)], check=True, capture_output=True)

    exe = ArExecutable()
    args = ArArgs(operation=ArOperation.TABLE, archive=lib)
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
    assert b"bar" in result.danger_ok.stdout_bytes
