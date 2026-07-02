"""ComplexityTest  -  verify algorithmic complexity via empirical timing."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generator, final

from lograder.common import Err, Ok, Result
from lograder.pipeline.config import get_config
from lograder.pipeline.test.test import Test, TestError, TestFailure, TestSuccess
from lograder.pipeline.types.artifacts import Artifact
from lograder.process.executable import ExecutableOptions
from lograder.process.os_helpers import StreamMode

if TYPE_CHECKING:
    from _strenum_compat import StrEnum
else:
    try:
        from enum import StrEnum
    except ImportError:
        from strenum import StrEnum

__test__: bool = False

_MIN_MEASURABLE_S = 1e-4


# ---------------------------------------------------------------------------
# Complexity class definitions
# ---------------------------------------------------------------------------


class ComplexityClass(StrEnum):
    """Expected algorithmic complexity class.

    The exponent bounds used for classification:

    +--------------+----------------+
    | Class        | log-log slope  |
    +==============+================+
    | O(1)         | alpha < 0.15   |
    | O(log n)     | 0.05 < alpha < 0.35 |
    | O(n)         | 0.75 < alpha < 1.35 |
    | O(n log n)   | 0.90 < alpha < 1.55 |
    | O(n^2)       | 1.75 < alpha < 2.35 |
    | O(n^3)       | 2.70 < alpha < 3.30 |
    +--------------+----------------+

    O(n) and O(n log n) overlap intentionally: at the input sizes typical
    for autograders, O(n log n) is nearly indistinguishable from O(n).
    Use at least sizes spanning 3 orders of magnitude to improve resolution.
    """

    O_1 = "O(1)"
    O_LOG_N = "O(log n)"
    O_N = "O(n)"
    O_N_LOG_N = "O(n log n)"
    O_N_SQUARED = "O(n^2)"
    O_N_CUBED = "O(n^3)"


_COMPLEXITY_BOUNDS: dict[ComplexityClass, tuple[float, float]] = {
    ComplexityClass.O_1: (0.0, 0.15),
    ComplexityClass.O_LOG_N: (0.05, 0.35),
    ComplexityClass.O_N: (0.75, 1.35),
    ComplexityClass.O_N_LOG_N: (0.90, 1.55),
    ComplexityClass.O_N_SQUARED: (1.75, 2.35),
    ComplexityClass.O_N_CUBED: (2.70, 3.30),
}


def _alpha_for(cls: ComplexityClass) -> tuple[float, float]:
    return _COMPLEXITY_BOUNDS[cls]


def _classify(alpha: float) -> str:
    for cls, (lo, hi) in _COMPLEXITY_BOUNDS.items():
        if lo <= alpha <= hi:
            return cls.value
    if alpha < 0:
        return "O(1) or less"
    return f"super-cubic (alpha={alpha:.2f})"


def _fit_exponent(sizes: list[int], times: list[float]) -> float:
    """Least-squares fit of log(T) = alpha*log(n) + C; return alpha."""
    n = len(sizes)
    if n < 2:
        return 0.0
    log_n = [math.log(s) for s in sizes]
    log_t = [math.log(max(t, _MIN_MEASURABLE_S)) for t in times]
    mean_n = sum(log_n) / n
    mean_t = sum(log_t) / n
    num = sum((log_n[i] - mean_n) * (log_t[i] - mean_t) for i in range(n))
    den = sum((log_n[i] - mean_n) ** 2 for i in range(n))
    if den == 0.0:
        return 0.0
    return num / den


# ---------------------------------------------------------------------------
# Case model
# ---------------------------------------------------------------------------


@dataclass
class ComplexityCase:
    """A single complexity test case.

    Args:
        name:           Unique case name.
        input_fn:       Callable that takes an integer ``n`` and returns
                        ``bytes`` to feed as stdin.  The returned bytes should
                        represent an input of "size n" for the algorithm under
                        test.
        sizes:          Increasing input sizes to measure at.  Use at least 4
                        values spanning >= 2 orders of magnitude for reliable
                        classification.
        expected:       Expected complexity class.
        args:           Command-line arguments passed to the binary.
        runs_per_size:  Number of timed runs per size; the median is used.
        timeout:        Per-run timeout in seconds.  Defaults to the pipeline
                        executable timeout.
    """

    name: str
    input_fn: Callable[[int], bytes]
    sizes: list[int]
    expected: ComplexityClass
    args: list[str] = field(default_factory=list)
    runs_per_size: int = 3
    timeout: float | None = None


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


class ComplexitySuccess(TestSuccess):
    __test__: bool = False
    expected: str
    measured_exponent: float
    measured_class: str
    sizes: list[int]
    times_s: list[float]


class ComplexityFailure(TestFailure):
    __test__: bool = False
    expected: str
    measured_exponent: float
    measured_class: str
    sizes: list[int]
    times_s: list[float]


class ComplexityError(TestError):
    __test__: bool = False


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------


def _median(values: list[float]) -> float:
    s = sorted(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 == 1 else (s[mid - 1] + s[mid]) / 2.0


@final
class ComplexityTest(
    Test[
        dict[str, Artifact],
        dict[str, Artifact],
        ComplexityError,
        ComplexitySuccess,
        ComplexityFailure,
    ]
):
    """Measure empirical complexity by timing at increasing input sizes.

    For each ``ComplexityCase`` the binary is run ``runs_per_size`` times at
    each size in ``sizes``; the median time per size is used.  A log-log
    linear regression gives an estimated exponent ``alpha``.  The case
    passes if ``alpha`` falls within the expected complexity class's bounds.

    Useful for checking sorting, searching, and other algorithmic assignments:

    Example::

        pipeline.add(comp := ComplexityTest("sorter", [
            ComplexityCase(
                name="sort_is_nlogn",
                input_fn=lambda n: "\\n".join(
                    str(i) for i in range(n, 0, -1)
                ).encode() + b"\\n",
                sizes=[100, 500, 2000, 10000, 50000],
                expected=ComplexityClass.O_N_LOG_N,
            ),
        ]))
        comp.scorer = TestCaseScorer({"sort_is_nlogn": 20.0}, label="Complexity")

    Note: timing-based tests are inherently noisy on shared CI machines.
    Use generous ``sizes`` ranges and set ``runs_per_size >= 3`` to reduce
    variance.

    Args:
        artifact_name:  Key in the artifacts dict for the binary.
        cases:          Complexity test cases.
        options:        ``ExecutableOptions`` forwarded to each run.
    """

    def __init__(
        self,
        artifact_name: str,
        cases: Iterable[ComplexityCase],
        options: ExecutableOptions | None = None,
    ) -> None:
        self._artifact_name = artifact_name
        self._cases = list(cases)
        self._options = options

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[ComplexitySuccess, ComplexityFailure],
        None,
        Result[dict[str, Artifact], ComplexityError],
    ]:
        artifact_result = self._resolve_artifact(artifacts, self._artifact_name)
        if artifact_result.is_err:
            return Err(
                ComplexityError(
                    artifact_name=self._artifact_name,
                    message=artifact_result.danger_err,
                )
            )
        artifact = artifact_result.danger_ok

        cfg = get_config()

        for case in self._cases:
            timeout = case.timeout or cfg.executable_timeout
            base_options = (self._options or ExecutableOptions()).model_copy(
                update={
                    "stdout_mode": StreamMode.PIPE,
                    "stderr_mode": StreamMode.PIPE,
                    "timeout": timeout,
                }
            )

            median_times: list[float] = []
            for size in case.sizes:
                stdin_bytes = case.input_fn(size)
                run_times: list[float] = []
                for _ in range(case.runs_per_size):
                    t0 = time.perf_counter()
                    self._invoke(artifact, case.args, stdin_bytes, base_options)
                    run_times.append(time.perf_counter() - t0)
                median_times.append(_median(run_times))

            alpha = _fit_exponent(case.sizes, median_times)
            lo, hi = _alpha_for(case.expected)
            measured_class = _classify(alpha)

            if lo <= alpha <= hi:
                yield Ok(
                    ComplexitySuccess(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        expected=case.expected.value,
                        measured_exponent=round(alpha, 3),
                        measured_class=measured_class,
                        sizes=case.sizes,
                        times_s=[round(t, 6) for t in median_times],
                    )
                )
            else:
                yield Err(
                    ComplexityFailure(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        expected=case.expected.value,
                        measured_exponent=round(alpha, 3),
                        measured_class=measured_class,
                        sizes=case.sizes,
                        times_s=[round(t, 6) for t in median_times],
                    )
                )

        return Ok(artifacts)


import lograder.output.layout.test.complexity  # noqa: E402, F401
