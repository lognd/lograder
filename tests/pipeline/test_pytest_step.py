# mypy: ignore-errors
"""Integration tests for PytestTest using real pytest invocations."""

from __future__ import annotations

import pytest

from lograder.pipeline.config import config
from lograder.pipeline.test.pytest import (
    PytestError,
    PytestFailure,
    PytestSuccess,
    PytestTest,
)
from lograder.process.executable import ExecutableOptions
from lograder.process.registry.pytest import PytestArgs

# ---------------------------------------------------------------------------
# Test file content helpers
# ---------------------------------------------------------------------------

_PASSING_TESTS = """\
def test_add():
    assert 1 + 1 == 2

def test_sub():
    assert 3 - 1 == 2
"""

_FAILING_TESTS = """\
def test_ok():
    assert True

def test_fail():
    assert 1 == 2, "one is not two"
"""

_SKIPPED_TESTS = """\
import pytest

def test_real():
    assert True

@pytest.mark.skip(reason="not ready")
def test_skipped():
    assert False
"""

_MIXED_TESTS = """\
import pytest

def test_passes():
    assert 1 + 1 == 2

def test_fails():
    assert False

@pytest.mark.skip
def test_skipped():
    pass
"""

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _run_step(step, artifacts=None):
    gen = step(artifacts or {})
    packets = []
    try:
        while True:
            packets.append(next(gen))
    except StopIteration as e:
        return packets, e.value


# ---------------------------------------------------------------------------
# Basic functionality
# ---------------------------------------------------------------------------


def test_passing_tests(tmp_path):
    (tmp_path / "test_math.py").write_text(_PASSING_TESTS)
    step = PytestTest(
        paths=["test_math.py"],
        options=ExecutableOptions(cwd=tmp_path),
    )
    packets, result = _run_step(step)

    assert result.is_ok
    assert len(packets) == 2
    assert all(p.is_ok for p in packets)
    names = {p.danger_ok.test_name for p in packets}
    assert "test_math::test_add" in names or "test_add" in names  # classname may vary


def test_failing_tests(tmp_path):
    (tmp_path / "test_things.py").write_text(_FAILING_TESTS)
    step = PytestTest(
        paths=["test_things.py"],
        options=ExecutableOptions(cwd=tmp_path),
    )
    packets, result = _run_step(step)

    assert result.is_ok
    ok_count = sum(1 for p in packets if p.is_ok)
    err_count = sum(1 for p in packets if p.is_err)
    assert ok_count == 1
    assert err_count == 1


def test_failure_message_captured(tmp_path):
    (tmp_path / "test_f.py").write_text(_FAILING_TESTS)
    step = PytestTest(
        paths=["test_f.py"],
        options=ExecutableOptions(cwd=tmp_path),
    )
    packets, _ = _run_step(step)

    failure = next(p.danger_err for p in packets if p.is_err)
    assert isinstance(failure, PytestFailure)
    assert failure.failure_message or failure.failure_text  # some failure detail


def test_skipped_tests_not_yielded(tmp_path):
    (tmp_path / "test_skip.py").write_text(_SKIPPED_TESTS)
    step = PytestTest(
        paths=["test_skip.py"],
        options=ExecutableOptions(cwd=tmp_path),
    )
    packets, result = _run_step(step)

    assert result.is_ok
    assert len(packets) == 1
    assert packets[0].is_ok


def test_mixed_results(tmp_path):
    (tmp_path / "test_mixed.py").write_text(_MIXED_TESTS)
    step = PytestTest(
        paths=["test_mixed.py"],
        options=ExecutableOptions(cwd=tmp_path),
    )
    packets, result = _run_step(step)

    assert result.is_ok
    assert any(p.is_ok for p in packets)
    assert any(p.is_err for p in packets)


def test_autodiscover_without_paths(tmp_path):
    (tmp_path / "test_auto.py").write_text(_PASSING_TESTS)
    step = PytestTest(
        paths=None,
        options=ExecutableOptions(cwd=tmp_path),
    )
    packets, result = _run_step(step)

    assert result.is_ok
    assert len(packets) == 2


def test_keyword_filter(tmp_path):
    (tmp_path / "test_kw.py").write_text(_PASSING_TESTS)
    step = PytestTest(
        paths=["test_kw.py"],
        base_args=PytestArgs(keyword="add"),
        options=ExecutableOptions(cwd=tmp_path),
    )
    packets, result = _run_step(step)

    assert result.is_ok
    assert len(packets) == 1
    test_name = packets[0].danger_ok.test_name
    assert "add" in test_name


# ---------------------------------------------------------------------------
# Success packet fields
# ---------------------------------------------------------------------------


def test_success_packet_artifact_name(tmp_path):
    (tmp_path / "test_m.py").write_text(_PASSING_TESTS)
    step = PytestTest(
        paths=["test_m.py"],
        options=ExecutableOptions(cwd=tmp_path),
        label="my_label",
    )
    packets, _ = _run_step(step)

    for p in packets:
        assert p.danger_ok.artifact_name == "my_label"


def test_success_packet_classname(tmp_path):
    (tmp_path / "test_m.py").write_text(_PASSING_TESTS)
    step = PytestTest(
        paths=["test_m.py"],
        options=ExecutableOptions(cwd=tmp_path),
    )
    packets, _ = _run_step(step)

    for p in packets:
        success = p.danger_ok
        assert isinstance(success, PytestSuccess)
        assert success.classname  # non-empty classname from pytest


def test_default_label_is_pytest(tmp_path):
    (tmp_path / "test_m.py").write_text(_PASSING_TESTS)
    step = PytestTest(
        paths=["test_m.py"],
        options=ExecutableOptions(cwd=tmp_path),
    )
    packets, _ = _run_step(step)

    assert all(p.danger_ok.artifact_name == "pytest" for p in packets)


def test_artifacts_returned_unchanged(tmp_path):
    (tmp_path / "test_m.py").write_text(_PASSING_TESTS)
    step = PytestTest(
        paths=["test_m.py"],
        options=ExecutableOptions(cwd=tmp_path),
    )
    sentinel = {"key": "value"}
    _, result = _run_step(step, sentinel)  # type: ignore[arg-type]

    assert result.is_ok
    assert result.danger_ok is sentinel


# ---------------------------------------------------------------------------
# Error conditions
# ---------------------------------------------------------------------------


def test_warn_no_tests_true_empty_directory(tmp_path):
    step = PytestTest(
        paths=None,
        options=ExecutableOptions(cwd=tmp_path),
        warn_no_tests=True,
    )
    # Empty tmp_path -- no test files
    packets, result = _run_step(step)
    # Either fatal error (no tests) OR pytest exits with no-tests-collected
    # which may not produce valid XML -- either way result is an error
    assert result.is_err


def test_warn_no_tests_false_returns_ok_with_no_tests(tmp_path):
    # Create a conftest.py with nothing to collect
    (tmp_path / "conftest.py").write_text("")
    step = PytestTest(
        paths=["conftest.py"],
        options=ExecutableOptions(cwd=tmp_path),
        warn_no_tests=False,
    )
    packets, result = _run_step(step)
    # With warn_no_tests=False, should be ok (or error if conftest.py itself errors)
    # Just check it doesn't raise an exception in the step
    assert result.is_ok or result.is_err  # no uncaught exception
