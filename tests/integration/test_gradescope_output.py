# mypy: ignore-errors
import json
from pathlib import Path
from typing import Generator

import pytest
from pydantic import BaseModel

from lograder.common import Err, Ok, Result
from lograder.output.gradescope import GradescopeVisibility, write_gradescope_results
from lograder.pipeline.pipeline import Pipeline
from lograder.pipeline.score import (
    AllOrNothingScorer,
    CleanRunScorer,
    PipelineScore,
    ScoreContribution,
    TestCaseScorer,
)
from lograder.pipeline.step import Step
from lograder.pipeline.test.test import TestSuccess
from lograder.pipeline.types.sentinel import PIPELINE_START


class _D(BaseModel):
    pass


class _E(BaseModel):
    pass


class _OkStep(Step[PIPELINE_START, int, _E, _D, _E]):
    def __call__(
        self, input: PIPELINE_START
    ) -> Generator[Result[_D, _E], None, Result[int, _E]]:
        if False:
            yield Ok(_D())
        return Ok(1)


class _ErrStep(Step[PIPELINE_START, int, _E, _D, _E]):
    def __call__(
        self, input: PIPELINE_START
    ) -> Generator[Result[_D, _E], None, Result[int, _E]]:
        if False:
            yield Ok(_D())
        return Err(_E())


def _build_score(*items):
    score = PipelineScore()
    for step, scorer in items:
        step.scorer = scorer
        score.add(step, scorer.contribution())
    return score


def test_write_gradescope_results_creates_file(tmp_path):
    out_path = tmp_path / "results.json"
    score = PipelineScore()
    write_gradescope_results(score, path=out_path)
    assert out_path.exists()


def test_write_gradescope_results_returns_dict(tmp_path):
    out_path = tmp_path / "results.json"
    score = PipelineScore()
    result = write_gradescope_results(score, path=out_path)
    on_disk = json.loads(out_path.read_text(encoding="utf-8"))
    assert result == on_disk


def test_write_gradescope_results_structure(tmp_path):
    out_path = tmp_path / "results.json"
    score = PipelineScore()
    result = write_gradescope_results(score, path=out_path)
    assert "score" in result
    assert "tests" in result
    assert "visibility" in result
    assert "stdout_visibility" in result


def test_write_gradescope_results_visibility_default(tmp_path):
    out_path = tmp_path / "results.json"
    score = PipelineScore()
    result = write_gradescope_results(score, path=out_path)
    assert result["visibility"] == "visible"


def test_write_gradescope_results_stdout_visibility_default(tmp_path):
    out_path = tmp_path / "results.json"
    score = PipelineScore()
    result = write_gradescope_results(score, path=out_path)
    assert result["stdout_visibility"] == "hidden"


def test_write_gradescope_results_hidden_visibility(tmp_path):
    out_path = tmp_path / "results.json"
    score = PipelineScore()
    result = write_gradescope_results(
        score, path=out_path, visibility=GradescopeVisibility.HIDDEN
    )
    assert result["visibility"] == "hidden"


def test_write_gradescope_results_creates_parent_dirs(tmp_path):
    out_path = tmp_path / "deep" / "nested" / "results.json"
    score = PipelineScore()
    write_gradescope_results(score, path=out_path)
    assert out_path.exists()


def test_gradescope_score_from_empty_pipeline(tmp_path):
    out_path = tmp_path / "results.json"
    score = PipelineScore()
    result = write_gradescope_results(score, path=out_path)
    assert result["score"] == 0.0
    assert result["tests"] == []


def test_gradescope_with_all_or_nothing_scorer_pass(tmp_path):
    out_path = tmp_path / "results.json"
    step = _OkStep()
    scorer = AllOrNothingScorer(10.0, label="Build")
    scorer.on_complete(Ok(1))
    step.scorer = scorer
    score = PipelineScore()
    score.add(step, scorer.contribution())
    result = write_gradescope_results(score, path=out_path)
    assert result["score"] == 10.0
    assert result["tests"][0]["score"] == 10.0


def test_gradescope_with_multiple_scorers(tmp_path):
    out_path = tmp_path / "results.json"
    step1 = _OkStep()
    scorer1 = AllOrNothingScorer(10.0, label="Build")
    scorer1.on_complete(Ok(1))
    step1.scorer = scorer1

    step2 = _OkStep()
    scorer2 = AllOrNothingScorer(5.0, label="Check")
    scorer2.on_complete(Ok(1))
    step2.scorer = scorer2

    score = PipelineScore()
    score.add(step1, scorer1.contribution())
    score.add(step2, scorer2.contribution())
    result = write_gradescope_results(score, path=out_path)
    assert len(result["tests"]) == 2
    assert result["score"] == 15.0


def test_gradescope_extra_credit_in_output(tmp_path):
    out_path = tmp_path / "results.json"
    step = _OkStep()
    scorer = AllOrNothingScorer(10.0, extra_credit=5.0, label="Build")
    scorer.on_complete(Ok(1))
    step.scorer = scorer
    score = PipelineScore()
    score.add(step, scorer.contribution())
    result = write_gradescope_results(score, path=out_path)
    assert result["tests"][0]["score"] == 15.0


def test_gradescope_skipped_step_shows_zero(tmp_path):
    out_path = tmp_path / "results.json"
    step = _OkStep()
    scorer = AllOrNothingScorer(10.0, label="Build")
    step.scorer = scorer
    score = PipelineScore()
    score.add(step, scorer.contribution())
    result = write_gradescope_results(score, path=out_path)
    assert result["tests"][0]["score"] == 0.0
    assert result["tests"][0]["max_score"] == 10.0


def test_gradescope_output_field(tmp_path):
    out_path = tmp_path / "results.json"
    score = PipelineScore()
    result = write_gradescope_results(
        score, output="See log for details", path=out_path
    )
    assert result.get("output") == "See log for details"


def test_to_gradescope_dict_without_writing():
    step = _OkStep()
    scorer = AllOrNothingScorer(10.0, label="Build")
    scorer.on_complete(Ok(1))
    step.scorer = scorer
    score = PipelineScore()
    score.add(step, scorer.contribution())
    d = score.to_gradescope_dict()
    assert "score" in d
    assert d["score"] == 10.0
