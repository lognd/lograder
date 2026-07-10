from typing import Generator

import pytest
from pydantic import BaseModel

from lograder.common import Err, Ok, Result
from lograder.pipeline.score import (
    AllOrNothingScorer,
    CleanRunScorer,
    GimmeConfig,
    PipelineScore,
    ScoreContribution,
    TestCaseScorer,
)
from lograder.pipeline.step import Step
from lograder.pipeline.test.test import TestFailure, TestSuccess
from lograder.pipeline.types.sentinel import PIPELINE_START


class _D(BaseModel):
    pass


class _E(BaseModel):
    pass


class _DummyStep(Step[PIPELINE_START, int, _E, _D, _E]):
    def __call__(
        self, input: PIPELINE_START
    ) -> Generator[Result[_D, _E], None, Result[int, _E]]:
        if False:
            yield Ok(_D())
        return Ok(0)


def _make_success(name: str) -> Result:
    return Ok(TestSuccess(test_name=name, artifact_name="art"))


def _make_failure(name: str) -> Result:
    return Err(TestFailure(test_name=name, artifact_name="art"))


# --- TestCaseScorer ---


def test_test_case_scorer_dict_all_pass():
    scorer = TestCaseScorer({"a": 5.0, "b": 10.0})
    scorer.on_packet(_make_success("a"))
    scorer.on_packet(_make_success("b"))
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.earned == 15.0
    assert c.possible == 15.0


def test_test_case_scorer_dict_partial_pass():
    scorer = TestCaseScorer({"a": 5.0, "b": 10.0})
    scorer.on_packet(_make_success("a"))
    scorer.on_packet(_make_failure("b"))
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.earned == 5.0
    assert c.possible == 15.0


def test_test_case_scorer_dict_no_pass():
    scorer = TestCaseScorer({"a": 5.0, "b": 10.0})
    scorer.on_packet(_make_failure("a"))
    scorer.on_packet(_make_failure("b"))
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.earned == 0.0
    assert c.possible == 15.0


def test_test_case_scorer_flat_requires_num_cases():
    with pytest.raises(ValueError):
        TestCaseScorer(5.0)


def test_test_case_scorer_flat_with_num_cases():
    scorer = TestCaseScorer(5.0, num_cases=3)
    scorer.on_packet(_make_success("a"))
    scorer.on_packet(_make_success("b"))
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.possible == 15.0
    assert c.earned == 10.0


def test_test_case_scorer_extra_credit_not_in_possible():
    scorer = TestCaseScorer({"a": 5.0}, extra_credit_cases={"bonus": 3.0})
    c = scorer.contribution()
    assert c.possible == 5.0


def test_test_case_scorer_extra_credit_earned_on_pass():
    scorer = TestCaseScorer({"a": 5.0}, extra_credit_cases={"bonus": 3.0})
    scorer.on_packet(_make_success("a"))
    scorer.on_packet(_make_success("bonus"))
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.extra_credit == 3.0


def test_test_case_scorer_gimme_floor_applied():
    scorer = TestCaseScorer(
        {"a": 5.0, "b": 5.0, "c": 5.0},
        gimme=GimmeConfig(min_pass_fraction=0.5, points=3.0),
    )
    scorer.on_packet(_make_success("a"))
    scorer.on_packet(_make_failure("b"))
    scorer.on_packet(_make_failure("c"))
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.earned >= 3.0


def test_test_case_scorer_gimme_not_applied_below_threshold():
    scorer = TestCaseScorer(
        {"a": 5.0, "b": 5.0, "c": 5.0},
        gimme=GimmeConfig(min_pass_fraction=0.9, points=10.0),
    )
    scorer.on_packet(_make_success("a"))
    scorer.on_packet(_make_failure("b"))
    scorer.on_packet(_make_failure("c"))
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.earned == 5.0


def test_test_case_scorer_earned_capped_at_possible():
    scorer = TestCaseScorer({"a": 5.0, "b": 5.0})
    scorer.on_packet(_make_success("a"))
    scorer.on_packet(_make_success("b"))
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.earned <= c.possible


def test_test_case_scorer_unknown_case_scores_zero():
    scorer = TestCaseScorer({"known": 10.0})
    scorer.on_packet(_make_success("unknown"))
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.earned == 0.0


# --- AllOrNothingScorer ---


def test_all_or_nothing_ok_awards_full_points():
    scorer = AllOrNothingScorer(10.0)
    scorer.on_packet(Ok(_D()))
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.earned == 10.0
    assert c.possible == 10.0


def test_all_or_nothing_err_awards_zero():
    scorer = AllOrNothingScorer(10.0)
    scorer.on_complete(Err(_E()))
    c = scorer.contribution()
    assert c.earned == 0.0
    assert c.possible == 10.0


def test_all_or_nothing_extra_credit_on_ok():
    scorer = AllOrNothingScorer(10.0, extra_credit=5.0)
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.extra_credit == 5.0


def test_all_or_nothing_extra_credit_zero_on_err():
    scorer = AllOrNothingScorer(10.0, extra_credit=5.0)
    scorer.on_complete(Err(_E()))
    c = scorer.contribution()
    assert c.extra_credit == 0.0


def test_all_or_nothing_no_on_complete_call_gives_zero():
    scorer = AllOrNothingScorer(10.0)
    c = scorer.contribution()
    assert c.earned == 0.0
    assert c.possible == 10.0


def test_all_or_nothing_ignores_err_packets_awards_full_on_ok_return():
    """FLAW-1 regression (documented, not changed): a source-style check that
    yields per-violation Err packets but fatally returns Ok (SourceCheck,
    RawSourceCheck, MypyCheck, TyCheck) awards FULL credit under
    AllOrNothingScorer, because on_packet is intentionally a no-op. This is
    the documented, tested contract of AllOrNothingScorer -- see its
    docstring and docs/pipeline/scoring.md -- not a bug to fix here.
    CleanRunScorer is the correct scorer for that case; see
    test_clean_run_with_errors_above_max_awards_zero above for the
    contrasting, correct behavior on the identical packet stream.
    """
    scorer = AllOrNothingScorer(10.0)
    # Simulate a check step that yields several violation packets ...
    scorer.on_packet(Err(_E()))
    scorer.on_packet(Err(_E()))
    scorer.on_packet(Err(_E()))
    # ... but still fatally returns Ok (its own "job" -- reporting -- succeeded).
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.earned == 10.0  # full credit despite 3 violations -- by design


# --- CleanRunScorer ---


def test_clean_run_no_errors_awards_points():
    scorer = CleanRunScorer(5.0)
    scorer.on_packet(Ok(_D()))
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.earned == 5.0


def test_clean_run_with_errors_above_max_awards_zero():
    scorer = CleanRunScorer(5.0, max_errors=0)
    scorer.on_packet(Err(_E()))
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.earned == 0.0


def test_clean_run_with_errors_at_max_awards_points():
    scorer = CleanRunScorer(5.0, max_errors=2)
    scorer.on_packet(Err(_E()))
    scorer.on_packet(Err(_E()))
    scorer.on_complete(Ok(1))
    c = scorer.contribution()
    assert c.earned == 5.0


def test_clean_run_require_ok_return_zeroes_on_err_return():
    scorer = CleanRunScorer(5.0, require_ok_return=True)
    scorer.on_complete(Err(_E()))
    c = scorer.contribution()
    assert c.earned == 0.0


def test_clean_run_not_require_ok_return_ignores_return():
    scorer = CleanRunScorer(5.0, require_ok_return=False)
    scorer.on_complete(Err(_E()))
    c = scorer.contribution()
    assert c.earned == 5.0


# --- ScoreContribution ---


def test_score_contribution_total_is_earned_plus_extra():
    c = ScoreContribution(earned=7.0, possible=10.0, extra_credit=3.0)
    assert c.total == 10.0


# --- PipelineScore ---


def test_pipeline_score_add_and_total():
    score = PipelineScore()
    step = _DummyStep()
    scorer = AllOrNothingScorer(10.0, label="Build")
    scorer.on_complete(Ok(1))
    step.scorer = scorer
    score.add(step, scorer.contribution())

    total = score.total()
    assert total.earned == 10.0
    assert total.possible == 10.0


def test_pipeline_score_to_gradescope_dict_correct_format():
    score = PipelineScore()
    step = _DummyStep()
    scorer = AllOrNothingScorer(10.0, label="Build")
    scorer.on_complete(Ok(1))
    step.scorer = scorer
    score.add(step, scorer.contribution())

    d = score.to_gradescope_dict()
    assert "score" in d
    assert "tests" in d
    assert d["score"] == 10.0
    assert len(d["tests"]) == 1
    assert d["tests"][0]["name"] == "Build"
    assert d["tests"][0]["score"] == 10.0
    assert d["tests"][0]["max_score"] == 10.0


def test_pipeline_score_to_gradescope_dict_with_output():
    score = PipelineScore()
    d = score.to_gradescope_dict(output="See log for details")
    assert d.get("output") == "See log for details"
