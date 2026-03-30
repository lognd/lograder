# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

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
