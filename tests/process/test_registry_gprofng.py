from __future__ import annotations

from pathlib import Path

import pytest

from lograder.process.registry.gprofng import (
    GprofngCollectArgs,
    GprofngDisplayArgs,
    GprofngExecutable,
)


def test_collect_basic() -> None:
    args = GprofngCollectArgs(
        command=["./a.out"],
    )

    emitted = args.emit()
    assert emitted[0] == "collect"
    assert "./a.out" in emitted


def test_collect_with_output_and_flags() -> None:
    args = GprofngCollectArgs(
        output=Path("exp"),
        follow_children=True,
        command=["./prog"],
    )

    emitted = args.emit()
    assert "collect" in emitted
    assert "-o" in emitted
    assert "exp" in emitted
    assert "-F" in emitted
    assert "./prog" in emitted


def test_collect_does_not_require_command() -> None:
    GprofngCollectArgs()


def test_display_basic() -> None:
    args = GprofngDisplayArgs(
        experiment=Path("exp"),
    )

    emitted = args.emit()
    assert emitted == ["display", "exp"]


def test_display_with_flags() -> None:
    args = GprofngDisplayArgs(
        experiment=Path("exp"),
        functions=True,
        call_tree=True,
    )

    emitted = set(args.emit())
    assert "display" in emitted
    assert "exp" in emitted
    assert "-functions" in emitted
    assert "-calltree" in emitted


def test_display_with_metrics() -> None:
    args = GprofngDisplayArgs(
        experiment=Path("exp"),
        metrics="time",
    )

    emitted = args.emit()
    assert "-metrics" in emitted
    assert "time" in emitted


def test_add_opts_passthrough() -> None:
    args = GprofngDisplayArgs(
        experiment=Path("exp"),
        add_opts=["--some-flag"],
    )

    assert "--some-flag" in args.emit()


def test_registered() -> None:
    assert GprofngExecutable.executable is not None
    assert GprofngExecutable.executable.command == ["gprofng"]


# --- Real executable tests ---

import platform as _platform  # noqa: E402
import shutil as _shutil  # noqa: E402
import subprocess as _subprocess  # noqa: E402

_GPROFNG_AVAILABLE = bool(_shutil.which("gprofng"))
_GCC_AVAILABLE = bool(_shutil.which("gcc"))
_X86_64 = _platform.machine() == "x86_64"

_WORK_C = """\
#include <stdio.h>
void work(void) { for(int i=0;i<10000;i++) {} }
int main(void) { work(); return 0; }
"""


@pytest.mark.skipif(
    not (_GPROFNG_AVAILABLE and _GCC_AVAILABLE and _X86_64),
    reason="gprofng collect requires x86-64, gprofng, and gcc",
)
def test_gprofng_real_collect(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "main.c"
    src.write_text(_WORK_C, encoding="utf-8")
    binary = tmp_path / "main"
    _subprocess.run(
        ["gcc", str(src), "-o", str(binary)], check=True, capture_output=True
    )

    exe = GprofngExecutable()
    args = GprofngCollectArgs(command=[str(binary)])
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
