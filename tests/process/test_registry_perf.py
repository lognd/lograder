# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.perf import (
    PerfExecutable,
    PerfRecordArgs,
    PerfReportArgs,
    PerfScriptArgs,
    PerfStatArgs,
)


def test_record_basic() -> None:
    args = PerfRecordArgs(command=["./a.out"])
    emitted = args.emit()
    assert emitted[0] == "record"
    assert "./a.out" in emitted


def test_record_with_flags() -> None:
    args = PerfRecordArgs(
        output=Path("perf.data"),
        frequency=99,
        system_wide=True,
        command=["./prog"],
    )

    emitted = args.emit()
    assert "-o" in emitted
    assert "perf.data" in emitted
    assert "-F" in emitted
    assert "99" in emitted
    assert "-a" in emitted


def test_record_does_not_require_command() -> None:
    PerfRecordArgs()


def test_stat_basic() -> None:
    args = PerfStatArgs(command=["./a.out"])
    emitted = args.emit()
    assert emitted[0] == "stat"
    assert "./a.out" in emitted


def test_stat_with_events() -> None:
    args = PerfStatArgs(
        event=["cycles", "instructions"],
        command=["./a.out"],
    )

    emitted = args.emit()
    assert "-ecycles" in emitted
    assert "-einstructions" in emitted


def test_stat_does_not_require_command() -> None:
    PerfStatArgs()


def test_report_basic() -> None:
    args = PerfReportArgs(input_file=Path("perf.data"))
    emitted = args.emit()
    assert emitted[0] == "report"
    assert "-i" in emitted
    assert "perf.data" in emitted


def test_report_flags() -> None:
    args = PerfReportArgs(
        stdio=True,
        call_graph="fp",
    )

    emitted = args.emit()
    assert "--stdio" in emitted
    assert "-g" in emitted
    assert "fp" in emitted


def test_script_basic() -> None:
    args = PerfScriptArgs(input_file=Path("perf.data"))
    emitted = args.emit()
    assert emitted[0] == "script"
    assert "-i" in emitted


def test_add_opts_passthrough() -> None:
    args = PerfReportArgs(add_opts=["--no-children"])
    assert "--no-children" in args.emit()


def test_registered() -> None:
    assert PerfExecutable.executable is not None
    assert PerfExecutable.executable.command == ["perf"]
