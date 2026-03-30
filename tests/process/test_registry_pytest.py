# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.pytest import PytestArgs, PytestExecutable


def test_basic_paths() -> None:
    args = PytestArgs(paths=[Path("tests")])
    assert args.emit() == ["tests"]


def test_keyword_marker() -> None:
    args = PytestArgs(keyword="fast", marker="unit")
    emitted = args.emit()
    assert "-k" in emitted and "fast" in emitted
    assert "-m" in emitted and "unit" in emitted


def test_flags() -> None:
    args = PytestArgs(verbose=True, exit_first=True)
    emitted = set(args.emit())
    assert "-v" in emitted
    assert "-x" in emitted


def test_durations_and_junit() -> None:
    args = PytestArgs(durations=5, junit_xml=Path("r.xml"))
    emitted = args.emit()
    assert "--durations=5" in emitted
    assert "--junitxml=r.xml" in emitted


def test_ignore_and_deselect() -> None:
    args = PytestArgs(
        ignore=[Path("build")],
        deselect=["tests/test_bad.py::test_fail"],
    )
    emitted = args.emit()
    assert "--ignore=build" in emitted
    assert "--deselect=tests/test_bad.py::test_fail" in emitted


def test_python_warnings() -> None:
    args = PytestArgs(python_warnings=["ignore::DeprecationWarning"])
    assert "-Wignore::DeprecationWarning" in args.emit()


def test_add_opts_passthrough() -> None:
    args = PytestArgs(add_opts=["--tb=short", "--strict-markers"])
    emitted = args.emit()
    assert "--tb=short" in emitted
    assert "--strict-markers" in emitted


def test_reject_blank_keyword() -> None:
    with pytest.raises(ValidationError):
        PytestArgs(keyword="   ")


def test_reject_bad_path() -> None:
    with pytest.raises(ValidationError):
        PytestArgs(paths=[Path("BAD")])


def test_verbose_quiet_conflict() -> None:
    with pytest.raises(ValidationError):
        PytestArgs(verbose=True, quiet=True)


def test_stepwise_dependency() -> None:
    with pytest.raises(ValidationError):
        PytestArgs(stepwise_skip=True)


def test_registered() -> None:
    assert PytestExecutable.executable is not None
    assert PytestExecutable.executable.command == ["pytest"]
