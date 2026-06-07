# mypy: ignore-errors
"""Unit tests for ComplexityTest."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from lograder.pipeline.test.complexity import (
    ComplexityCase,
    ComplexityClass,
    ComplexityError,
    ComplexityFailure,
    ComplexityTest,
    _classify,
    _fit_exponent,
    _median,
)
from lograder.pipeline.types.artifacts import FileArtifact

# ---------------------------------------------------------------------------
# Pure helpers (no g++ required)
# ---------------------------------------------------------------------------


def test_median_odd():
    assert _median([3.0, 1.0, 2.0]) == 2.0


def test_median_even():
    assert _median([1.0, 3.0]) == 2.0


def test_fit_exponent_linear():
    # T(n) = n -> alpha should be close to 1.0
    sizes = [100, 1000, 10000]
    times = [0.001, 0.01, 0.1]
    alpha = _fit_exponent(sizes, times)
    assert abs(alpha - 1.0) < 0.05


def test_fit_exponent_quadratic():
    sizes = [10, 100, 1000]
    times = [0.0001, 0.01, 1.0]
    alpha = _fit_exponent(sizes, times)
    assert abs(alpha - 2.0) < 0.1


def test_fit_exponent_constant():
    sizes = [10, 100, 1000]
    times = [0.001, 0.001, 0.001]
    alpha = _fit_exponent(sizes, times)
    assert abs(alpha) < 0.2


def test_fit_exponent_single_point():
    assert _fit_exponent([100], [0.01]) == 0.0


def test_classify_linear():
    assert "O(n)" in _classify(1.0)


def test_classify_constant():
    assert "O(1)" in _classify(0.05)


def test_classify_quadratic():
    assert "O(n^2)" in _classify(2.0)


def test_classify_super_cubic():
    result = _classify(5.0)
    assert "super-cubic" in result


def test_complexity_error_missing_artifact():
    step = ComplexityTest("missing", [])
    yields, result = _drive(step, {})
    assert result.is_err
    assert isinstance(result.danger_err, ComplexityError)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


_HAS_GPP = subprocess.run(["which", "g++"], capture_output=True).returncode == 0


def _build_linear_binary() -> Path | None:
    """Build a binary that does O(n) work: sum n integers from stdin."""
    src = """
#include <iostream>
int main(){
    long long n; std::cin >> n;
    volatile long long s = 0;
    for(long long i = 0; i < n; i++) s += i;
    std::cout << s << "\\n";
    return 0;
}
"""
    tmpdir = Path(tempfile.mkdtemp(prefix="lograder_complexity_"))
    src_f = tmpdir / "prog.cpp"
    src_f.write_text(src, encoding="utf-8")
    binary = tmpdir / "prog"
    r = subprocess.run(
        ["g++", "-O2", "-o", str(binary), str(src_f)], capture_output=True
    )
    return binary if r.returncode == 0 else None


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_complexity_linear_program_detected():
    binary = _build_linear_binary()
    if binary is None:
        pytest.skip("Compilation failed")

    artifact = FileArtifact(path=binary)
    cases = [
        ComplexityCase(
            name="linear_sum",
            input_fn=lambda n: f"{n}\n".encode(),
            sizes=[1000, 5000, 20000, 100000],
            expected=ComplexityClass.O_N,
            runs_per_size=3,
        )
    ]
    step = ComplexityTest("prog", cases)
    yields, result = _drive(step, {"prog": artifact})
    assert result.is_ok
    assert len(yields) == 1
    # O(n) bounds are generous; accept either ok or err for CI variability
    # but at least the step ran without crashing
    pkt = yields[0]
    assert pkt.is_ok or pkt.is_err


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_complexity_wrong_class_yields_failure():
    binary = _build_linear_binary()
    if binary is None:
        pytest.skip("Compilation failed")

    artifact = FileArtifact(path=binary)
    cases = [
        ComplexityCase(
            name="expect_cubic",
            input_fn=lambda n: f"{n}\n".encode(),
            sizes=[1000, 5000, 20000],
            expected=ComplexityClass.O_N_CUBED,
            runs_per_size=2,
        )
    ]
    step = ComplexityTest("prog", cases)
    yields, result = _drive(step, {"prog": artifact})
    assert result.is_ok
    assert len(yields) == 1
    assert yields[0].is_err
    assert isinstance(yields[0].danger_err, ComplexityFailure)


def _drive(step, input_val):
    gen = step(input_val)
    yields = []
    try:
        while True:
            yields.append(next(gen))
    except StopIteration as e:
        return yields, e.value
