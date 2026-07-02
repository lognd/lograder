from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from lograder.common import Result
from lograder.output.capture import CapturedOutput
from lograder.pipeline.test.test import TestFailure, TestSuccess

if TYPE_CHECKING:
    from lograder.pipeline.metadata import GraderMetadata
    from lograder.pipeline.step import Step


# ---------------------------------------------------------------------------
# Gradescope type aliases
# ---------------------------------------------------------------------------

Visibility = Literal["hidden", "after_due_date", "after_published", "visible"]
OutputFormat = Literal["text", "html", "simple_format", "md", "ansi"]

GRADESCOPE_RESULTS_PATH = Path("/autograder/results/results.json")


# ---------------------------------------------------------------------------
# Gradescope configuration dataclasses
# ---------------------------------------------------------------------------


@dataclass
class GradescopeTestConfig:
    """Per-test Gradescope metadata. Attach to a scorer: ``scorer.gradescope = GradescopeTestConfig(...)``.

    All fields are optional. ``status=None`` lets Gradescope infer pass/fail
    from score vs max_score. ``output`` is shown to students directly in the
    Gradescope UI  -  put a human-readable summary here.
    """

    output: str = ""
    visibility: Visibility | None = None
    status: Literal["passed", "failed"] | None = None
    number: str = ""
    tags: list[str] = field(default_factory=list)
    output_format: OutputFormat | None = None
    name_format: Literal["text", "html", "md", "ansi"] | None = None
    extra_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class GradescopeConfig:
    """Top-level Gradescope results configuration.

    Pass this to ``PipelineScore.to_gradescope_dict(config=...)``.

    ``output`` appears above the test list on the Gradescope submission page.
    ``visibility`` sets the default visibility for all tests; individual test
    configs can override it. ``stdout_visibility`` controls whether
    run_autograder's stdout is shown to students.
    """

    output: str = ""
    output_format: OutputFormat = "ansi"
    test_output_format: OutputFormat = "ansi"
    test_name_format: Literal["text", "html", "md", "ansi"] = "text"
    visibility: Visibility = "visible"
    stdout_visibility: Visibility = "hidden"
    execution_time: int | None = None
    extra_data: dict[str, Any] = field(default_factory=dict)
    leaderboard: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Scoring primitives
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# PipelineScore
# ---------------------------------------------------------------------------


@dataclass
class PipelineScore:
    """Aggregated scoring result from a pipeline run.

    ``contributions`` includes ALL scored steps  -  both completed and skipped due to early
    exit. Skipped steps contribute 0/possible so the total ``possible`` is always accurate.

    ``metadata`` is carried from ``Pipeline.__call__(metadata=...)`` and is automatically
    included in the ``output`` block of ``to_gradescope_dict()`` / ``write_results_json()``.
    """

    contributions: list[tuple[Step, ScoreContribution]] = field(default_factory=list)
    metadata: GraderMetadata | None = None

    def add(self, step: Step, contribution: ScoreContribution) -> None:
        self.contributions.append((step, contribution))

    def total(self) -> ScoreContribution:
        return ScoreContribution(
            earned=sum(c.earned for _, c in self.contributions),
            possible=sum(c.possible for _, c in self.contributions),
            extra_credit=sum(c.extra_credit for _, c in self.contributions),
        )

    def to_gradescope_dict(
        self,
        *,
        config: GradescopeConfig | None = None,
        output: str = "",
        metadata: GraderMetadata | None = None,
    ) -> dict[str, Any]:
        """Return a Gradescope-compatible results dict.

        ``config`` controls top-level visibility, output format, and other
        settings. Scorers may carry a ``GradescopeTestConfig`` for per-test
        metadata (output text, visibility override, status, tags, etc.).

        ``output`` is a shorthand for ``config.output`` when you only need
        to set the top-level message and nothing else.

        ``metadata`` overrides ``self.metadata`` if supplied. The metadata
        block is prepended to ``output`` automatically.
        """
        effective_metadata = metadata if metadata is not None else self.metadata
        cfg = config or GradescopeConfig(output=output)
        if output and not cfg.output:
            cfg = GradescopeConfig(
                output=output,
                output_format=cfg.output_format,
                test_output_format=cfg.test_output_format,
                test_name_format=cfg.test_name_format,
                visibility=cfg.visibility,
                stdout_visibility=cfg.stdout_visibility,
                execution_time=cfg.execution_time,
                extra_data=cfg.extra_data,
                leaderboard=cfg.leaderboard,
            )

        # Prepend metadata block to output; metadata uses ANSI codes so force the format.
        if effective_metadata is not None:
            meta_block = effective_metadata.to_display_string()
            combined = meta_block + ("\n\n" + cfg.output if cfg.output else "")
            from dataclasses import replace as _replace

            cfg = _replace(cfg, output=combined, output_format="ansi")

        tests = []
        for step, c in self.contributions:
            scorer = step.scorer
            label = scorer.label if scorer is not None else None
            tc = scorer.gradescope if scorer is not None else None

            test: dict[str, Any] = {
                "name": label or step.__class__.__name__,
                "score": c.total,
                "max_score": c.possible,
            }

            effective_vis = (
                tc.visibility
                if tc is not None and tc.visibility is not None
                else cfg.visibility
            )

            if tc is not None:
                if tc.visibility is not None:
                    test["visibility"] = tc.visibility
                if tc.status is not None:
                    test["status"] = tc.status
                if tc.number:
                    test["number"] = tc.number
                if tc.tags:
                    test["tags"] = tc.tags
                if tc.name_format is not None:
                    test["name_format"] = tc.name_format
                if tc.extra_data:
                    test["extra_data"] = tc.extra_data

            # Output: grader-set tc.output always wins; fall back to pipeline-
            # captured output only for tests whose effective visibility is "visible".
            if tc is not None and tc.output:
                test["output"] = tc.output
                if tc.output_format is not None:
                    test["output_format"] = tc.output_format
            elif (
                scorer is not None
                and scorer.captured_output is not None
                and effective_vis == "visible"
            ):
                fmt = (
                    tc.output_format
                    if tc is not None and tc.output_format is not None
                    else cfg.test_output_format
                )
                test["output"] = scorer.captured_output.for_format(fmt)
                test["output_format"] = fmt

            tests.append(test)

        total = self.total()
        result: dict[str, Any] = {
            "score": total.total,
            "visibility": cfg.visibility,
            "stdout_visibility": cfg.stdout_visibility,
            "output_format": cfg.output_format,
            "test_output_format": cfg.test_output_format,
            "test_name_format": cfg.test_name_format,
            "tests": tests,
        }
        if cfg.output:
            result["output"] = cfg.output
        if cfg.execution_time is not None:
            result["execution_time"] = cfg.execution_time
        if cfg.extra_data:
            result["extra_data"] = cfg.extra_data
        if cfg.leaderboard:
            result["leaderboard"] = cfg.leaderboard
        return result

    def write_results_json(
        self,
        *,
        config: GradescopeConfig | None = None,
        output: str = "",
        path: Path | None = None,
        metadata: GraderMetadata | None = None,
    ) -> None:
        """Serialize results to a JSON file (default: ``/autograder/results/results.json``).

        Creates parent directories if they do not exist.

        ``metadata`` overrides ``self.metadata`` if supplied.
        """
        dest = path or GRADESCOPE_RESULTS_PATH
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = self.to_gradescope_dict(config=config, output=output, metadata=metadata)
        dest.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Scorer base
# ---------------------------------------------------------------------------


class Scorer(ABC):
    """Base for step scorers. Attach to ``step.scorer`` before running the pipeline."""

    label: str | None = None
    gradescope: GradescopeTestConfig | None = None
    captured_output: CapturedOutput | None = (
        None  # populated by Pipeline; consumed by serializers
    )

    @abstractmethod
    def on_packet(self, result: Result) -> None:
        """Called for each display packet yielded by the step."""

    @abstractmethod
    def on_complete(self, result: Result) -> None:
        """Called once with the step's final return Result."""

    @abstractmethod
    def contribution(self) -> ScoreContribution:
        """Must return 0/possible when never called (step skipped by early exit)."""


# ---------------------------------------------------------------------------
# Concrete scorers
# ---------------------------------------------------------------------------


class TestCaseScorer(Scorer):
    """Awards points per passing test case with optional extra credit and gimme floor.

    Args:
        points_per_case: Flat float (requires ``num_cases``) or dict case->points.
        num_cases: Required when ``points_per_case`` is a float.
        extra_credit_cases: Case names -> extra credit earned on pass; NOT in ``possible``.
        gimme: If student passes >= ``min_pass_fraction`` of attempted cases, ``earned``
            is floored to ``gimme.points``.
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
        if isinstance(points_per_case, dict):
            self._possible: float = sum(points_per_case.values())
        else:
            assert num_cases is not None  # enforced above
            self._possible = float(points_per_case) * num_cases
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

    Responds only to the fatal return  -  use ``CleanRunScorer`` to score non-fatal Err yields.

    Args:
        points: Regular points on success.
        extra_credit: Bonus points on success; NOT counted in ``possible``.
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
    Responds to yielded Err packets  -  not the fatal return value. Use ``AllOrNothingScorer``
    if you only care about whether the step as a whole passes.

    Args:
        points: Regular points awarded when Err yield count <= ``max_errors``.
        max_errors: Maximum tolerated non-fatal Err yields (default 0 = must be clean).
        require_ok_return: If True (default), award 0 when the step fatally returns Err
            regardless of yield count.
        extra_credit: Bonus points awarded under the same conditions; NOT in ``possible``.
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
