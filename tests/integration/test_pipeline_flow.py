# mypy: ignore-errors
from typing import Generator

import pytest
from pydantic import BaseModel

from lograder.common import Err, Ok, Result
from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.pipeline import Pipeline
from lograder.pipeline.score import (
    AllOrNothingScorer,
    CleanRunScorer,
    GimmeConfig,
    PipelineScore,
    TestCaseScorer,
)
from lograder.pipeline.step import Step
from lograder.pipeline.test.output_compare import (
    OutputCompareFailure,
    OutputCompareSuccess,
)
from lograder.pipeline.types.sentinel import PIPELINE_START


class _D(BaseModel):
    pass


class _E(BaseModel):
    pass


@register_layout("test-flow-err")
class _ELayout(Layout[_E]):
    @classmethod
    def to_simple(cls, data: _E) -> str:
        return "test-error"

    @classmethod
    def to_ansi(cls, data: _E) -> str:
        return "test-error"


class _OkStep(Step[PIPELINE_START, int, _E, _D, _E]):
    def __call__(
        self, input: PIPELINE_START
    ) -> Generator[Result[_D, _E], None, Result[int, _E]]:
        if False:
            yield Ok(_D())
        return Ok(42)


class _ErrStep(Step[PIPELINE_START, int, _E, _D, _E]):
    def __call__(
        self, input: PIPELINE_START
    ) -> Generator[Result[_D, _E], None, Result[int, _E]]:
        if False:
            yield Ok(_D())
        return Err(_E())


class _IntOkStep(Step[int, str, _E, _D, _E]):
    def __call__(self, input: int) -> Generator[Result[_D, _E], None, Result[str, _E]]:
        if False:
            yield Ok(_D())
        return Ok(str(input))


class _StrSentinelStep(Step[PIPELINE_START, str, _E, _D, _E]):
    def __call__(
        self, input: PIPELINE_START
    ) -> Generator[Result[_D, _E], None, Result[str, _E]]:
        if False:
            yield Ok(_D())
        return Ok("hello")


class _StrCheckStep(Step[str, str, _E, _D, _E]):
    def __init__(self):
        self.received_input = None

    def __call__(self, input: str) -> Generator[Result[_D, _E], None, Result[str, _E]]:
        self.received_input = input
        if False:
            yield Ok(_D())
        return Ok(input)


# Uses registered OutputCompare* types so the pipeline logger doesn't fail.
class _YieldOkStep(
    Step[PIPELINE_START, int, _E, OutputCompareSuccess, OutputCompareFailure]
):
    def __call__(
        self, input: PIPELINE_START
    ) -> Generator[
        Result[OutputCompareSuccess, OutputCompareFailure], None, Result[int, _E]
    ]:
        yield Ok(OutputCompareSuccess(test_name="case_a", artifact_name="art", args=[]))
        yield Ok(OutputCompareSuccess(test_name="case_b", artifact_name="art", args=[]))
        yield Err(
            OutputCompareFailure(
                test_name="case_c",
                artifact_name="art",
                args=[],
                stdin_text="",
                expected_stdout="x",
                actual_stdout="y",
                diff="",
                expected_exit_code=None,
                actual_exit_code=0,
            )
        )
        return Ok(1)


class _YieldErrStep(
    Step[PIPELINE_START, int, _E, OutputCompareSuccess, OutputCompareFailure]
):
    def __call__(
        self, input: PIPELINE_START
    ) -> Generator[
        Result[OutputCompareSuccess, OutputCompareFailure], None, Result[int, _E]
    ]:
        yield Err(
            OutputCompareFailure(
                test_name="t1",
                artifact_name="art",
                args=[],
                stdin_text="",
                expected_stdout="x",
                actual_stdout="y",
                diff="",
                expected_exit_code=None,
                actual_exit_code=0,
            )
        )
        yield Err(
            OutputCompareFailure(
                test_name="t2",
                artifact_name="art",
                args=[],
                stdin_text="",
                expected_stdout="x",
                actual_stdout="y",
                diff="",
                expected_exit_code=None,
                actual_exit_code=0,
            )
        )
        return Ok(1)


def test_empty_pipeline_returns_empty_score():
    pipeline = Pipeline()
    score = pipeline()
    assert isinstance(score, PipelineScore)
    assert score.contributions == []


def test_single_step_ok_no_scorer():
    pipeline = Pipeline()
    step = _OkStep()
    pipeline.steps = [step]
    score = pipeline()
    assert isinstance(score, PipelineScore)
    assert score.contributions == []


def test_pipeline_stops_on_err_return():
    called = []

    class _SecondStep(Step[int, str, _E, _D, _E]):
        def __call__(
            self, input: int
        ) -> Generator[Result[_D, _E], None, Result[str, _E]]:
            called.append(True)
            if False:
                yield Ok(_D())
            return Ok("done")

    pipeline = Pipeline()
    pipeline.steps = [_ErrStep(), _SecondStep()]
    pipeline()
    assert called == []


def test_pipeline_threads_datum_through_ok_steps():
    check_step = _StrCheckStep()
    pipeline = Pipeline()
    pipeline.steps = [_StrSentinelStep(), check_step]
    pipeline()
    assert check_step.received_input == "hello"


def test_pipeline_skipped_steps_contribute_zero_possible():
    pipeline = Pipeline()
    first = _ErrStep()
    second = _IntOkStep()
    second.scorer = AllOrNothingScorer(10.0, label="Second")
    pipeline.steps = [first, second]
    score = pipeline()
    assert len(score.contributions) == 1
    _, contrib = score.contributions[0]
    assert contrib.earned == 0.0
    assert contrib.possible == 10.0


def test_all_or_nothing_scorer_ok():
    pipeline = Pipeline()
    step = _OkStep()
    step.scorer = AllOrNothingScorer(10.0, label="Build")
    pipeline.steps = [step]
    score = pipeline()
    _, contrib = score.contributions[0]
    assert contrib.earned == 10.0


def test_all_or_nothing_scorer_err():
    pipeline = Pipeline()
    step = _ErrStep()
    step.scorer = AllOrNothingScorer(10.0, label="Build")
    pipeline.steps = [step]
    score = pipeline()
    _, contrib = score.contributions[0]
    assert contrib.earned == 0.0
    assert contrib.possible == 10.0


def test_test_case_scorer_tracks_passes_and_fails():
    pipeline = Pipeline()
    step = _YieldOkStep()
    step.scorer = TestCaseScorer(
        {"case_a": 5.0, "case_b": 5.0, "case_c": 5.0}, label="Tests"
    )
    pipeline.steps = [step]
    score = pipeline()
    _, contrib = score.contributions[0]
    assert contrib.earned == 10.0
    assert contrib.possible == 15.0


def test_test_case_scorer_with_gimme():
    pipeline = Pipeline()
    step = _YieldOkStep()
    step.scorer = TestCaseScorer(
        {"case_a": 5.0, "case_b": 5.0, "case_c": 5.0},
        gimme=GimmeConfig(min_pass_fraction=0.5, points=5.0),
        label="Tests",
    )
    pipeline.steps = [step]
    score = pipeline()
    _, contrib = score.contributions[0]
    assert contrib.earned >= 5.0


def test_test_case_scorer_extra_credit():
    class _ExtraStep(
        Step[PIPELINE_START, int, _E, OutputCompareSuccess, OutputCompareFailure]
    ):
        def __call__(
            self, input: PIPELINE_START
        ) -> Generator[
            Result[OutputCompareSuccess, OutputCompareFailure], None, Result[int, _E]
        ]:
            yield Ok(
                OutputCompareSuccess(test_name="regular", artifact_name="art", args=[])
            )
            yield Ok(
                OutputCompareSuccess(test_name="bonus", artifact_name="art", args=[])
            )
            return Ok(1)

    pipeline = Pipeline()
    step = _ExtraStep()
    step.scorer = TestCaseScorer(
        {"regular": 10.0},
        extra_credit_cases={"bonus": 5.0},
        label="Tests",
    )
    pipeline.steps = [step]
    score = pipeline()
    _, contrib = score.contributions[0]
    assert contrib.possible == 10.0
    assert contrib.extra_credit == 5.0


def test_clean_run_scorer_clean_step():
    pipeline = Pipeline()
    step = _OkStep()
    step.scorer = CleanRunScorer(5.0, label="Check")
    pipeline.steps = [step]
    score = pipeline()
    _, contrib = score.contributions[0]
    assert contrib.earned == 5.0


def test_clean_run_scorer_with_errors():
    pipeline = Pipeline()
    step = _YieldErrStep()
    step.scorer = CleanRunScorer(5.0, max_errors=0, label="Check")
    pipeline.steps = [step]
    score = pipeline()
    _, contrib = score.contributions[0]
    assert contrib.earned == 0.0


def test_pipeline_score_total():
    pipeline = Pipeline()
    s1 = _OkStep()
    s1.scorer = AllOrNothingScorer(10.0, label="Build")

    class _SecondOkStep(Step[int, str, _E, _D, _E]):
        def __call__(
            self, input: int
        ) -> Generator[Result[_D, _E], None, Result[str, _E]]:
            if False:
                yield Ok(_D())
            return Ok("done")

    s2 = _SecondOkStep()
    s2.scorer = AllOrNothingScorer(5.0, label="Test")
    pipeline.steps = [s1, s2]
    score = pipeline()
    total = score.total()
    assert total.earned == 15.0
    assert total.possible == 15.0


def test_to_gradescope_dict_format():
    pipeline = Pipeline()
    step = _OkStep()
    step.scorer = AllOrNothingScorer(10.0, label="Build")
    pipeline.steps = [step]
    score = pipeline()
    d = score.to_gradescope_dict()
    assert "score" in d
    assert "tests" in d
    assert isinstance(d["score"], (int, float))
    assert isinstance(d["tests"], list)
    assert d["tests"][0]["name"] == "Build"
