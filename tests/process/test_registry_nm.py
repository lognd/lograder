# mypy: ignore-errors
from __future__ import annotations

from pathlib import Path

import pytest

from lograder.process.cli_args import CLI_ARG_MISSING
from lograder.process.registry.nm import NmArgs, NmExecutable


def test_basic_emit_single_file(tmp_path):
    f = tmp_path / "lib.a"
    args = NmArgs(files=[f])
    tokens = args.emit()
    assert str(f) in tokens


def test_dynamic_flag():
    f = Path("/tmp/lib.so")
    args = NmArgs(files=[f], dynamic=True)
    tokens = args.emit()
    assert "-D" in tokens or "--dynamic" in tokens


def test_defined_only_flag():
    f = Path("/tmp/lib.a")
    args = NmArgs(files=[f], defined_only=True)
    tokens = args.emit()
    assert "--defined-only" in tokens


def test_extern_only_flag():
    f = Path("/tmp/lib.a")
    args = NmArgs(files=[f], extern_only=True)
    tokens = args.emit()
    assert "--extern-only" in tokens or "-g" in tokens


def test_undefined_only_flag():
    f = Path("/tmp/lib.a")
    args = NmArgs(files=[f], undefined_only=True)
    tokens = args.emit()
    assert "--undefined-only" in tokens or "-u" in tokens


def test_demangle_flag():
    f = Path("/tmp/lib.a")
    args = NmArgs(files=[f], demangle=True)
    tokens = args.emit()
    assert "--demangle" in tokens or "-C" in tokens


def test_portability_flag():
    f = Path("/tmp/lib.a")
    args = NmArgs(files=[f], portability=True)
    tokens = args.emit()
    assert "-P" in tokens or "--portability" in tokens


def test_multiple_files():
    files = [Path("/tmp/a.o"), Path("/tmp/b.o")]
    args = NmArgs(files=files)
    tokens = args.emit()
    assert "/tmp/a.o" in tokens
    assert "/tmp/b.o" in tokens


def test_no_flags_by_default():
    f = Path("/tmp/lib.a")
    args = NmArgs(files=[f])
    tokens = args.emit()
    assert "-D" not in tokens
    assert "--defined-only" not in tokens
    assert "--extern-only" not in tokens


def test_nm_executable_is_instantiable():
    exe = NmExecutable()
    assert exe is not None


def test_nm_check_runnable_returns_result():
    exe = NmExecutable()
    result = exe.check_runnable()
    # Either ok (nm installed) or err (not installed) — both valid outcomes
    assert result.is_ok or result.is_err


# --- Real executable tests ---

import shutil as _shutil
import subprocess as _subprocess

_NM_AVAILABLE = bool(_shutil.which("nm"))
_GCC_AVAILABLE = bool(_shutil.which("gcc"))


@pytest.mark.skipif(
    not (_NM_AVAILABLE and _GCC_AVAILABLE), reason="nm and gcc both required"
)
def test_nm_real_lists_symbols_from_object(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "foo.c"
    src.write_text("int my_special_symbol(void){return 1;}\n", encoding="utf-8")
    obj = tmp_path / "foo.o"
    _subprocess.run(
        ["gcc", "-c", str(src), "-o", str(obj)], check=True, capture_output=True
    )

    exe = NmExecutable()
    args = NmArgs(files=[obj], extern_only=True, defined_only=True)
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
    assert b"my_special_symbol" in result.danger_ok.stdout_bytes


@pytest.mark.skipif(
    not (_NM_AVAILABLE and _GCC_AVAILABLE), reason="nm and gcc both required"
)
def test_nm_real_dynamic_flag_on_shared_lib(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "bar.c"
    src.write_text("int bar(void){return 2;}\n", encoding="utf-8")
    lib = tmp_path / "libbar.so"
    _subprocess.run(
        ["gcc", "-shared", "-fPIC", str(src), "-o", str(lib)],
        check=True,
        capture_output=True,
    )

    exe = NmExecutable()
    args = NmArgs(files=[lib], dynamic=True)
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
    assert b"bar" in result.danger_ok.stdout_bytes
