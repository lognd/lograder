from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from lograder.common import Result
from lograder.pipeline.test.test import TestFailure, TestSuccess

if TYPE_CHECKING:
    from lograder.pipeline.step import Step


@dataclass
class GimmeConfig:
    """Awards a point floor to students who pass at least `min_pass_fraction` of attempted cases."""

    min_pass_fraction: float
    points: float


@dataclass
class ScoreContribution:
    earned: float
    possible: float
    extra_credit: float = 0.0

    @property
    def total(self) -> float:
        return self.earned + self.extra_credit


@dataclass
class PipelineScore:
    """Aggregated scoring result from a pipeline run.

    `contributions` includes ALL scored steps — both completed and skipped due to early
    exit. Skipped steps contribute 0/possible so the total `possible` is always accurate.
    """

    contributions: list[tuple[Step, ScoreContribution]] = field(default_factory=list)

    def add(self, step: Step, contribution: ScoreContribution) -> None:
        self.contributions.append((step, contribution))

    def total(self) -> ScoreContribution:
        return ScoreContribution(
            earned=sum(c.earned for _, c in self.contributions),
            possible=sum(c.possible for _, c in self.contributions),
            extra_credit=sum(c.extra_credit for _, c in self.contributions),
        )

    def to_gradescope_dict(self, *, output: str = "") -> dict[str, Any]:
        """Return a Gradescope-compatible results dict.

        Score per test = earned + extra_credit (Gradescope allows score > max_score for
        extra credit). Enrich the returned dict — add per-test `output`, `visibility`,
        or `status` — before writing to results.json.
        """
        tests = []
        for step, c in self.contributions:
            label = step.scorer.label if step.scorer is not None else None
            tests.append(
                {
                    "name": label or step.__class__.__name__,
                    "score": c.total,
                    "max_score": c.possible,
                }
            )
        total = self.total()
        result: dict[str, Any] = {"score": total.total, "tests": tests}
        if output:
            result["output"] = output
        return result


class Scorer(ABC):
    """Base for step scorers. Attach to `step.scorer` before running the pipeline."""

    label: str | None = None

    @abstractmethod
    def on_packet(self, result: Result) -> None:
        """Called for each display packet yielded by the step."""

    @abstractmethod
    def on_complete(self, result: Result) -> None:
        """Called once with the step's final return Result."""

    @abstractmethod
    def contribution(self) -> ScoreContribution:
        """Must return 0/possible when never called (step skipped by early exit)."""


class TestCaseScorer(Scorer):
    """Awards points per passing test case with optional extra credit and gimme floor.

    Args:
        points_per_case: Flat float (requires `num_cases`) or dict case→points.
        num_cases: Required when `points_per_case` is a float.
        extra_credit_cases: Case names → extra credit earned on pass; NOT in `possible`.
        gimme: If student passes >= `min_pass_fraction` of attempted cases, `earned`
            is floored to `gimme.points`.
        label: Name used in Gradescope output.
    """

    __test__: bool = False

    def __init__(
        self,
        points_per_case: dict[str, float] | float,
        *,
        num_cases: int | None = None,
        extra_credit_cases: dict[str, float] | None = None,
        gimme: GimmeConfig | None = None,
        label: str | None = None,
    ) -> None:
        if isinstance(points_per_case, (int, float)) and num_cases is None:
            raise ValueError(
                "`num_cases` is required when `points_per_case` is a flat value."
            )
        self.label = label
        self._points = points_per_case
        self._possible: float = (
            sum(points_per_case.values())
            if isinstance(points_per_case, dict)
            else float(points_per_case) * num_cases  # type: ignore[operator]
        )
        self._extra_credit_cases: dict[str, float] = extra_credit_cases or {}
        self._gimme = gimme
        self._passes: dict[str, float] = {}
        self._fail_count: int = 0
        self._extra_earned: float = 0.0

    def on_packet(self, result: Result) -> None:
        val = result.danger_ok if result.is_ok else result.danger_err
        if isinstance(val, TestSuccess):
            pts = (
                self._points.get(val.test_name, 0.0)
                if isinstance(self._points, dict)
                else float(self._points)
            )
            self._passes[val.test_name] = pts
            self._extra_earned += self._extra_credit_cases.get(val.test_name, 0.0)
        elif isinstance(val, TestFailure):
            self._fail_count += 1

    def on_complete(self, result: Result) -> None:
        pass

    def contribution(self) -> ScoreContribution:
        raw_earned = sum(self._passes.values())
        if self._gimme is not None:
            denominator = len(self._passes) + self._fail_count
            fraction = len(self._passes) / denominator if denominator > 0 else 0.0
            if fraction >= self._gimme.min_pass_fraction:
                raw_earned = max(raw_earned, self._gimme.points)
        return ScoreContribution(
            earned=min(raw_earned, self._possible),
            possible=self._possible,
            extra_credit=self._extra_earned,
        )


class AllOrNothingScorer(Scorer):
    """Awards full points if the step's return Result is Ok, 0 otherwise.

    Responds only to the fatal return — use `CleanRunScorer` to score non-fatal Err yields.

    Args:
        points: Regular points on success.
        extra_credit: Bonus points on success; NOT counted in `possible`.
        label: Name used in Gradescope output.
    """

    def __init__(
        self, points: float, *, extra_credit: float = 0.0, label: str | None = None
    ) -> None:
        self.label = label
        self._points = points
        self._extra_credit = extra_credit
        self._ok = False

    def on_packet(self, result: Result) -> None:
        pass

    def on_complete(self, result: Result) -> None:
        self._ok = result.is_ok

    def contribution(self) -> ScoreContribution:
        return ScoreContribution(
            earned=self._points if self._ok else 0.0,
            possible=self._points,
            extra_credit=self._extra_credit if self._ok else 0.0,
        )


class CleanRunScorer(Scorer):
    """Awards points based on the absence of non-fatal Err packets yielded by a step.

    Designed for check steps where a clean run (zero or few violations) earns credit.
    Responds to yielded Err packets — not the fatal return value. Use `AllOrNothingScorer`
    if you only care about whether the step as a whole passes.

    Args:
        points: Regular points awarded when Err yield count <= `max_errors`.
        max_errors: Maximum tolerated non-fatal Err yields (default 0 = must be clean).
        require_ok_return: If True (default), award 0 when the step fatally returns Err
            regardless of yield count.
        extra_credit: Bonus points awarded under the same conditions; NOT in `possible`.
        label: Name used in Gradescope output.
    """

    def __init__(
        self,
        points: float,
        *,
        max_errors: int = 0,
        require_ok_return: bool = True,
        extra_credit: float = 0.0,
        label: str | None = None,
    ) -> None:
        self.label = label
        self._points = points
        self._max_errors = max_errors
        self._require_ok_return = require_ok_return
        self._extra_credit = extra_credit
        self._err_count: int = 0
        self._return_ok: bool = False

    def on_packet(self, result: Result) -> None:
        if result.is_err:
            self._err_count += 1

    def on_complete(self, result: Result) -> None:
        self._return_ok = result.is_ok

    def contribution(self) -> ScoreContribution:
        if self._require_ok_return and not self._return_ok:
            return ScoreContribution(earned=0.0, possible=self._points)
        qualifies = self._err_count <= self._max_errors
        return ScoreContribution(
            earned=self._points if qualifies else 0.0,
            possible=self._points,
            extra_credit=self._extra_credit if qualifies else 0.0,
        )
