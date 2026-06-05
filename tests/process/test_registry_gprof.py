# mypy: ignore-errors
# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.gprof import GprofArgs, GprofExecutable


def test_basic_executable_only() -> None:
    args = GprofArgs(executable=Path("a.out"))
    assert args.emit() == ["a.out"]


def test_with_gmon_file() -> None:
    args = GprofArgs(
        executable=Path("a.out"),
        gmon_file=Path("gmon.out"),
    )
    assert args.emit() == ["a.out", "gmon.out"]


def test_flags() -> None:
    args = GprofArgs(
        executable=Path("a.out"),
        flat_profile=True,
        call_graph=True,
        no_static=True,
    )

    emitted = set(args.emit())
    assert "-p" in emitted
    assert "-q" in emitted
    assert "-a" in emitted


def test_annotate_source() -> None:
    args = GprofArgs(
        executable=Path("a.out"),
        annotate_source=["file.c"],
    )

    emitted = args.emit()
    assert "-Afile.c" in emitted


def test_file_format() -> None:
    args = GprofArgs(
        executable=Path("a.out"),
        file_format="prof",
    )

    assert "-Oprof" in args.emit()


def test_add_opts_passthrough() -> None:
    args = GprofArgs(
        executable=Path("a.out"),
        add_opts=["--no-demangle", "--some-flag"],
    )

    emitted = args.emit()
    assert "--no-demangle" in emitted
    assert "--some-flag" in emitted


def test_combined_usage() -> None:
    args = GprofArgs(
        executable=Path("a.out"),
        gmon_file=Path("gmon.out"),
        flat_profile=True,
        annotate_source=["main.c"],
    )

    emitted = args.emit()
    assert "a.out" in emitted
    assert "gmon.out" in emitted
    assert "-p" in emitted
    assert "-Amain.c" in emitted


def test_reject_blank_executable() -> None:
    with pytest.raises(ValidationError):
        GprofArgs(executable="   ")


def test_reject_blank_gmon_file() -> None:
    with pytest.raises(ValidationError):
        GprofArgs(
            executable=Path("a.out"),
            gmon_file="   ",
        )


def test_reject_blank_sequence_entry() -> None:
    with pytest.raises(ValidationError):
        GprofArgs(
            executable=Path("a.out"),
            annotate_source=[""],
        )


def test_registered() -> None:
    assert GprofExecutable.executable is not None
    assert GprofExecutable.executable.command == ["gprof"]


# --- Real executable tests ---

import shutil as _shutil
import subprocess as _subprocess

_GPROF_AVAILABLE = bool(_shutil.which("gprof"))
_GCC_AVAILABLE = bool(_shutil.which("gcc"))

_PROF_C = """\
#include <stdio.h>
void work(void) { for(int i=0;i<1000;i++) {} }
int main(void) { work(); return 0; }
"""


@pytest.mark.skipif(
    not (_GPROF_AVAILABLE and _GCC_AVAILABLE), reason="gprof and gcc both required"
)
def test_gprof_real_profiles_program(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "main.c"
    src.write_text(_PROF_C, encoding="utf-8")
    binary = tmp_path / "main"
    _subprocess.run(
        ["gcc", "-pg", str(src), "-o", str(binary)], check=True, capture_output=True
    )
    _subprocess.run([str(binary)], cwd=str(tmp_path), check=True, capture_output=True)
    gmon = tmp_path / "gmon.out"
    assert gmon.exists()

    exe = GprofExecutable()
    args = GprofArgs(executable=binary, gmon_file=gmon)
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
    assert (
        b"Call graph" in result.danger_ok.stdout_bytes
        or b"Flat profile" in result.danger_ok.stdout_bytes
    )
