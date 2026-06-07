# mypy: ignore-errors
"""Unit tests for CompileCheckTest."""

import subprocess

import pytest

from lograder.pipeline.test.compile_check import (
    _NO_MAIN_SENTINEL,
    CompileCase,
    CompileCheckFailure,
    CompileCheckSuccess,
    CompileCheckTest,
    _build_source,
)

# ---------------------------------------------------------------------------
# _build_source helper
# ---------------------------------------------------------------------------


def test_build_source_wraps_code_in_main():
    case = CompileCase(name="t", code="int x = 1;", should_compile=True)
    src = _build_source(case)
    assert "int main()" in src
    assert "int x = 1;" in src


def test_build_source_no_main_sentinel_skips_wrapper():
    preamble = f"#include <iostream>\n{_NO_MAIN_SENTINEL}"
    case = CompileCase(
        name="t",
        code="int main(){return 0;}",
        should_compile=True,
        preamble=preamble,
    )
    src = _build_source(case)
    # Should NOT wrap in another main()
    assert src.count("int main") == 1


def test_build_source_preamble_appears_before_code():
    case = CompileCase(
        name="t",
        code="x = 1;",
        should_compile=True,
        preamble="#include <stdio.h>",
    )
    src = _build_source(case)
    assert src.index("#include") < src.index("x = 1;")


# ---------------------------------------------------------------------------
# CompileCheckTest step
# ---------------------------------------------------------------------------


_HAS_GPP = subprocess.run(["which", "g++"], capture_output=True).returncode == 0


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_compile_check_valid_code_passes():
    cases = [
        CompileCase(
            name="valid_int_decl",
            code="int x = 42;",
            should_compile=True,
        )
    ]
    step = CompileCheckTest(cases)
    yields, result = _drive(step, {})
    assert result.is_ok
    assert len(yields) == 1
    assert yields[0].is_ok
    assert isinstance(yields[0].danger_ok, CompileCheckSuccess)


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_compile_check_invalid_code_fails_as_expected():
    cases = [
        CompileCase(
            name="invalid_type_assign",
            code='int x = "not an int";',
            should_compile=False,
        )
    ]
    step = CompileCheckTest(cases)
    yields, result = _drive(step, {})
    assert result.is_ok
    assert len(yields) == 1
    assert yields[0].is_ok  # Expected to NOT compile -- that's a success
    success = yields[0].danger_ok
    assert isinstance(success, CompileCheckSuccess)
    assert not success.should_compile


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_compile_check_unexpected_compile_error_yields_failure():
    cases = [
        CompileCase(
            name="expected_to_pass_but_wont",
            code="this is garbage @@@@",
            should_compile=True,
        )
    ]
    step = CompileCheckTest(cases)
    yields, result = _drive(step, {})
    assert result.is_ok
    assert len(yields) == 1
    assert yields[0].is_err
    failure = yields[0].danger_err
    assert isinstance(failure, CompileCheckFailure)
    assert failure.should_compile is True


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_compile_check_multiple_cases():
    cases = [
        CompileCase(name="good", code="int y = 0;", should_compile=True),
        CompileCase(name="bad", code='int z = "oops";', should_compile=False),
    ]
    step = CompileCheckTest(cases)
    yields, result = _drive(step, {})
    assert result.is_ok
    assert len(yields) == 2
    assert all(y.is_ok for y in yields)


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_compile_check_artifacts_passed_through(tmp_path):
    from lograder.pipeline.types.artifacts import FileArtifact

    fake_path = tmp_path / "fake"
    fake_path.write_bytes(b"")
    artifacts = {"my_binary": FileArtifact(path=fake_path)}
    step = CompileCheckTest([])
    yields, result = _drive(step, artifacts)
    assert result.is_ok
    assert result.danger_ok is artifacts


def _drive(step, input_val):
    gen = step(input_val)
    yields = []
    try:
        while True:
            yields.append(next(gen))
    except StopIteration as e:
        return yields, e.value
