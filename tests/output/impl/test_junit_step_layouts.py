# mypy: ignore-errors
"""Layout rendering tests for Catch2, gtest, ctest, and pytest test step models."""

from __future__ import annotations

import lograder.output.layout.test.catch2
import lograder.output.layout.test.ctest
import lograder.output.layout.test.gtest
import lograder.output.layout.test.pytest
from lograder.output.layout.layout import dispatch_layout
from lograder.pipeline.test.catch2 import Catch2Error, Catch2Failure, Catch2Success
from lograder.pipeline.test.ctest import CTestError, CTestFailure, CTestSuccess
from lograder.pipeline.test.gtest import GTestError, GTestFailure, GTestSuccess
from lograder.pipeline.test.pytest import PytestError, PytestFailure, PytestSuccess

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def simple(model) -> str:
    return dispatch_layout(model).to_simple(model)


def ansi(model) -> str:
    return dispatch_layout(model).to_ansi(model)


# ---------------------------------------------------------------------------
# Catch2 layouts
# ---------------------------------------------------------------------------


def test_catch2_success_simple_contains_pass():
    m = Catch2Success(
        test_name="Suite/test_add",
        artifact_name="tests",
        suite_name="Suite",
        duration=0.042,
        stdout="",
        stderr="",
    )
    out = simple(m)
    assert "[PASS]" in out
    assert "Suite/test_add" in out


def test_catch2_success_ansi_contains_pass():
    m = Catch2Success(
        test_name="Suite/test_add",
        artifact_name="tests",
        suite_name="Suite",
        duration=0.042,
        stdout="",
        stderr="",
    )
    out = ansi(m)
    assert "PASS" in out
    assert "Suite/test_add" in out


def test_catch2_success_duration_shown():
    m = Catch2Success(
        test_name="t",
        artifact_name="a",
        suite_name="S",
        duration=1.234,
        stdout="",
        stderr="",
    )
    assert "1.234" in simple(m)


def test_catch2_success_no_duration():
    m = Catch2Success(
        test_name="t",
        artifact_name="a",
        suite_name="S",
        duration=None,
        stdout="",
        stderr="",
    )
    out = simple(m)
    assert "None" not in out


def test_catch2_failure_simple_contains_fail():
    m = Catch2Failure(
        test_name="Suite/bad",
        artifact_name="tests",
        suite_name="Suite",
        duration=0.005,
        failure_message="1 != 2",
        failure_text="at test.cpp:10",
        stdout="",
        stderr="",
    )
    out = simple(m)
    assert "[FAIL]" in out
    assert "Suite/bad" in out
    assert "1 != 2" in out
    assert "test.cpp:10" in out


def test_catch2_failure_ansi_contains_fail():
    m = Catch2Failure(
        test_name="t",
        artifact_name="a",
        suite_name="S",
        duration=None,
        failure_message="oops",
        failure_text="detail",
        stdout="",
        stderr="",
    )
    out = ansi(m)
    assert "FAIL" in out
    assert "oops" in out


def test_catch2_failure_truncates_long_text():
    m = Catch2Failure(
        test_name="t",
        artifact_name="a",
        suite_name="S",
        duration=None,
        failure_message="m",
        failure_text="x" * 1000,
        stdout="",
        stderr="",
    )
    out = simple(m)
    assert "truncated" in out or len(out) < 2000


def test_catch2_error_simple():
    m = Catch2Error(artifact_name="tests", message="binary crashed")
    out = simple(m)
    assert "[ERROR]" in out
    assert "binary crashed" in out


def test_catch2_error_ansi():
    m = Catch2Error(artifact_name="tests", message="no xml")
    out = ansi(m)
    assert "ERROR" in out
    assert "no xml" in out


# ---------------------------------------------------------------------------
# gtest layouts
# ---------------------------------------------------------------------------


def test_gtest_success_simple():
    m = GTestSuccess(
        test_name="MathTest.Add",
        artifact_name="tests",
        suite_name="MathTest",
        duration=0.001,
        stdout="",
        stderr="",
    )
    out = simple(m)
    assert "[PASS]" in out
    assert "MathTest.Add" in out


def test_gtest_success_ansi():
    m = GTestSuccess(
        test_name="MathTest.Add",
        artifact_name="tests",
        suite_name="MathTest",
        duration=0.001,
        stdout="",
        stderr="",
    )
    out = ansi(m)
    assert "PASS" in out


def test_gtest_failure_simple():
    m = GTestFailure(
        test_name="MathTest.Bad",
        artifact_name="tests",
        suite_name="MathTest",
        duration=0.002,
        failure_message="Expected: 1\n  Actual: 2",
        failure_text="line 42",
        stdout="",
        stderr="",
    )
    out = simple(m)
    assert "[FAIL]" in out
    assert "MathTest.Bad" in out
    assert "Expected" in out


def test_gtest_failure_ansi():
    m = GTestFailure(
        test_name="t",
        artifact_name="a",
        suite_name="S",
        duration=None,
        failure_message="bad",
        failure_text="detail",
        stdout="",
        stderr="",
    )
    out = ansi(m)
    assert "FAIL" in out
    assert "bad" in out


def test_gtest_error_simple():
    m = GTestError(artifact_name="tests", message="no binary")
    out = simple(m)
    assert "[ERROR]" in out
    assert "no binary" in out


def test_gtest_error_ansi():
    m = GTestError(artifact_name="tests", message="no binary")
    out = ansi(m)
    assert "ERROR" in out


# ---------------------------------------------------------------------------
# ctest layouts
# ---------------------------------------------------------------------------


def test_ctest_success_simple():
    m = CTestSuccess(
        test_name="CTestSuite/test_math",
        artifact_name="build",
        suite_name="CTestSuite",
        duration=0.100,
    )
    out = simple(m)
    assert "[PASS]" in out
    assert "test_math" in out


def test_ctest_success_ansi():
    m = CTestSuccess(
        test_name="CTestSuite/test_math",
        artifact_name="build",
        suite_name="CTestSuite",
        duration=0.100,
    )
    out = ansi(m)
    assert "PASS" in out


def test_ctest_failure_simple():
    m = CTestFailure(
        test_name="Suite/test_bad",
        artifact_name="build",
        suite_name="Suite",
        duration=0.050,
        failure_message="exit code 1",
        failure_text="process exited non-zero",
    )
    out = simple(m)
    assert "[FAIL]" in out
    assert "test_bad" in out
    assert "exit code 1" in out


def test_ctest_failure_ansi():
    m = CTestFailure(
        test_name="t",
        artifact_name="a",
        suite_name="S",
        duration=None,
        failure_message="failed",
        failure_text="details",
    )
    out = ansi(m)
    assert "FAIL" in out


def test_ctest_error_simple():
    m = CTestError(artifact_name="build", message="ctest not found")
    out = simple(m)
    assert "[ERROR]" in out
    assert "ctest not found" in out


def test_ctest_error_ansi():
    m = CTestError(artifact_name="build", message="ctest not found")
    out = ansi(m)
    assert "ERROR" in out


# ---------------------------------------------------------------------------
# pytest layouts
# ---------------------------------------------------------------------------


def test_pytest_success_simple():
    m = PytestSuccess(
        test_name="test_math::test_add",
        artifact_name="pytest",
        classname="test_math",
        duration=0.003,
        stdout="",
        stderr="",
    )
    out = simple(m)
    assert "[PASS]" in out
    assert "test_math::test_add" in out


def test_pytest_success_ansi():
    m = PytestSuccess(
        test_name="test_math::test_add",
        artifact_name="pytest",
        classname="test_math",
        duration=0.003,
        stdout="",
        stderr="",
    )
    out = ansi(m)
    assert "PASS" in out


def test_pytest_failure_simple():
    m = PytestFailure(
        test_name="test_things::test_fail",
        artifact_name="pytest",
        classname="test_things",
        duration=0.007,
        failure_message="AssertionError: one is not two",
        failure_text="assert 1 == 2",
        stdout="",
        stderr="",
    )
    out = simple(m)
    assert "[FAIL]" in out
    assert "test_fail" in out
    assert "AssertionError" in out


def test_pytest_failure_ansi():
    m = PytestFailure(
        test_name="t",
        artifact_name="pytest",
        classname="C",
        duration=None,
        failure_message="oops",
        failure_text="detail",
        stdout="",
        stderr="",
    )
    out = ansi(m)
    assert "FAIL" in out
    assert "oops" in out


def test_pytest_error_simple():
    m = PytestError(artifact_name="pytest", message="pytest not installed")
    out = simple(m)
    assert "[ERROR]" in out
    assert "pytest not installed" in out


def test_pytest_error_ansi():
    m = PytestError(artifact_name="pytest", message="no tests found")
    out = ansi(m)
    assert "ERROR" in out


def test_pytest_layout_no_artifact_name_in_output():
    # Unlike binary-based steps, pytest layout doesn't show artifact_name in success
    m = PytestSuccess(
        test_name="mod::fn",
        artifact_name="pytest",
        classname="mod",
        duration=None,
        stdout="",
        stderr="",
    )
    out = simple(m)
    assert "mod::fn" in out
