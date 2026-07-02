from pathlib import Path

import pytest

from lograder.pipeline.check.project import simple_project
from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.mixin.mixin import InjectStudentIntoStaff
from lograder.pipeline.pipeline import Pipeline
from lograder.pipeline.score import AllOrNothingScorer, TestCaseScorer
from lograder.pipeline.test.output_compare import (
    OutputCompareCase,
    OutputCompareTest,
)

from .conftest import PROJECTS, FixedDirCMakeBuild, copy_staff, copy_submission

CMakeManifestCheck = simple_project.CMakeManifestCheck

_ECHO_CASES = [
    OutputCompareCase(
        name="hello", args=["hello"], stdin=b"", expected_stdout="hello\n"
    ),
    OutputCompareCase(
        name="multi_word",
        args=["foo", "bar", "baz"],
        stdin=b"",
        expected_stdout="foo bar baz\n",
    ),
    OutputCompareCase(name="single", args=["one"], stdin=b"", expected_stdout="one\n"),
]

_ADDER_CASES = [
    OutputCompareCase(
        name="add_pos", args=["3", "4"], stdin=b"", expected_stdout="7\n"
    ),
    OutputCompareCase(
        name="add_neg", args=["-2", "5"], stdin=b"", expected_stdout="3\n"
    ),
    OutputCompareCase(
        name="add_zero", args=["0", "0"], stdin=b"", expected_stdout="0\n"
    ),
]


def _make_echo_pipeline_with_inject(
    submission_dir: Path, staff_dir: Path, build_dir: Path
):
    check_step = CMakeManifestCheck()
    check_step.scorer = AllOrNothingScorer(0.0, label="Manifest")

    build_step = FixedDirCMakeBuild(build_dir)
    build_step.scorer = AllOrNothingScorer(10.0, label="Build")

    test_step = OutputCompareTest("echo", _ECHO_CASES)
    test_step.scorer = TestCaseScorer(
        {"hello": 5.0, "multi_word": 5.0, "single": 5.0},
        label="Tests",
    )

    pipeline = Pipeline()
    pipeline.steps = [
        LocalDirectory(submission_dir),
        InjectStudentIntoStaff(staff_dir),
        check_step,
        build_step,
        test_step,
    ]
    return pipeline


def _make_full_echo_pipeline(submission_dir: Path, build_dir: Path):
    check_step = CMakeManifestCheck()
    check_step.scorer = AllOrNothingScorer(0.0, label="Manifest")

    build_step = FixedDirCMakeBuild(build_dir)
    build_step.scorer = AllOrNothingScorer(10.0, label="Build")

    test_step = OutputCompareTest("echo", _ECHO_CASES)
    test_step.scorer = TestCaseScorer(
        {"hello": 5.0, "multi_word": 5.0, "single": 5.0},
        label="Tests",
    )

    pipeline = Pipeline()
    pipeline.steps = [
        LocalDirectory(submission_dir),
        check_step,
        build_step,
        test_step,
    ]
    return pipeline


def _make_adder_pipeline(submission_dir: Path, staff_dir: Path, build_dir: Path):
    check_step = CMakeManifestCheck()
    check_step.scorer = AllOrNothingScorer(0.0, label="Manifest")

    build_step = FixedDirCMakeBuild(build_dir)
    build_step.scorer = AllOrNothingScorer(10.0, label="Build")

    test_step = OutputCompareTest("add", _ADDER_CASES)
    test_step.scorer = TestCaseScorer(
        {"add_pos": 5.0, "add_neg": 5.0, "add_zero": 5.0},
        label="Tests",
    )

    pipeline = Pipeline()
    pipeline.steps = [
        LocalDirectory(submission_dir),
        InjectStudentIntoStaff(staff_dir),
        check_step,
        build_step,
        test_step,
    ]
    return pipeline


@pytest.mark.slow
def test_cmake_echo_correct_full_pipeline(tmp_path):
    submission_dir = tmp_path / "submission"
    staff_dir = tmp_path / "staff"
    build_dir = tmp_path / "build"
    copy_submission(PROJECTS / "cmake_echo" / "submissions" / "correct", submission_dir)
    copy_staff(PROJECTS / "cmake_echo" / "staff", staff_dir)

    pipeline = _make_echo_pipeline_with_inject(submission_dir, staff_dir, build_dir)
    with config(root_directory=tmp_path):
        score = pipeline()

    build_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Build"
    )
    test_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Tests"
    )
    assert build_contrib.earned == 10.0
    assert test_contrib.earned == 15.0


@pytest.mark.slow
def test_cmake_echo_reversed_fails_tests(tmp_path):
    submission_dir = tmp_path / "submission"
    staff_dir = tmp_path / "staff"
    build_dir = tmp_path / "build"
    copy_submission(
        PROJECTS / "cmake_echo" / "submissions" / "reversed", submission_dir
    )
    copy_staff(PROJECTS / "cmake_echo" / "staff", staff_dir)

    pipeline = _make_echo_pipeline_with_inject(submission_dir, staff_dir, build_dir)
    with config(root_directory=tmp_path):
        score = pipeline()

    build_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Build"
    )
    test_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Tests"
    )
    assert build_contrib.earned == 10.0
    assert test_contrib.earned < 15.0


@pytest.mark.slow
def test_cmake_echo_compile_error_stops_pipeline(tmp_path):
    submission_dir = tmp_path / "submission"
    staff_dir = tmp_path / "staff"
    build_dir = tmp_path / "build"
    copy_submission(
        PROJECTS / "cmake_echo" / "submissions" / "compile_error", submission_dir
    )
    copy_staff(PROJECTS / "cmake_echo" / "staff", staff_dir)

    pipeline = _make_echo_pipeline_with_inject(submission_dir, staff_dir, build_dir)
    with config(root_directory=tmp_path):
        score = pipeline()

    build_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Build"
    )
    test_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Tests"
    )
    assert build_contrib.earned == 0.0
    assert test_contrib.earned == 0.0
    assert test_contrib.possible == 15.0


@pytest.mark.slow
def test_cmake_echo_missing_source_fails_manifest_check(tmp_path):
    submission_dir = tmp_path / "submission"
    staff_dir = tmp_path / "staff"
    build_dir = tmp_path / "build"
    copy_submission(
        PROJECTS / "cmake_echo" / "submissions" / "missing_source", submission_dir
    )
    copy_staff(PROJECTS / "cmake_echo" / "staff", staff_dir)

    pipeline = _make_echo_pipeline_with_inject(submission_dir, staff_dir, build_dir)
    with config(root_directory=tmp_path):
        score = pipeline()

    build_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Build"
    )
    assert build_contrib.earned == 0.0


@pytest.mark.slow
def test_full_cmake_echo_correct(tmp_path):
    submission_dir = tmp_path / "submission"
    build_dir = tmp_path / "build"
    copy_submission(
        PROJECTS / "full_cmake_echo" / "submissions" / "correct", submission_dir
    )

    pipeline = _make_full_echo_pipeline(submission_dir, build_dir)
    with config(root_directory=tmp_path):
        score = pipeline()

    build_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Build"
    )
    test_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Tests"
    )
    assert build_contrib.earned == 10.0
    assert test_contrib.earned == 15.0


@pytest.mark.slow
def test_full_cmake_echo_missing_cmake_fails_check(tmp_path):
    submission_dir = tmp_path / "submission"
    build_dir = tmp_path / "build"
    copy_submission(
        PROJECTS / "full_cmake_echo" / "submissions" / "missing_cmake", submission_dir
    )

    pipeline = _make_full_echo_pipeline(submission_dir, build_dir)
    with config(root_directory=tmp_path):
        score = pipeline()

    build_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Build"
    )
    assert build_contrib.earned == 0.0
    assert build_contrib.possible == 10.0


@pytest.mark.slow
def test_full_cmake_echo_compile_error_stops(tmp_path):
    submission_dir = tmp_path / "submission"
    build_dir = tmp_path / "build"
    copy_submission(
        PROJECTS / "full_cmake_echo" / "submissions" / "compile_error", submission_dir
    )

    pipeline = _make_full_echo_pipeline(submission_dir, build_dir)
    with config(root_directory=tmp_path):
        score = pipeline()

    build_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Build"
    )
    assert build_contrib.earned == 0.0


@pytest.mark.slow
def test_full_cmake_echo_partial_pass_scores_partial(tmp_path):
    submission_dir = tmp_path / "submission"
    build_dir = tmp_path / "build"
    copy_submission(
        PROJECTS / "full_cmake_echo" / "submissions" / "partial_pass", submission_dir
    )

    pipeline = _make_full_echo_pipeline(submission_dir, build_dir)
    with config(root_directory=tmp_path):
        score = pipeline()

    build_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Build"
    )
    test_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Tests"
    )
    assert build_contrib.earned == 10.0
    assert 0.0 < test_contrib.earned < 15.0


@pytest.mark.slow
def test_cmake_adder_correct(tmp_path):
    submission_dir = tmp_path / "submission"
    staff_dir = tmp_path / "staff"
    build_dir = tmp_path / "build"
    copy_submission(
        PROJECTS / "cmake_adder" / "submissions" / "correct", submission_dir
    )
    copy_staff(PROJECTS / "cmake_adder" / "staff", staff_dir)

    pipeline = _make_adder_pipeline(submission_dir, staff_dir, build_dir)
    with config(root_directory=tmp_path):
        score = pipeline()

    test_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Tests"
    )
    assert test_contrib.earned == 15.0


@pytest.mark.slow
def test_cmake_adder_off_by_one_fails(tmp_path):
    submission_dir = tmp_path / "submission"
    staff_dir = tmp_path / "staff"
    build_dir = tmp_path / "build"
    copy_submission(
        PROJECTS / "cmake_adder" / "submissions" / "off_by_one", submission_dir
    )
    copy_staff(PROJECTS / "cmake_adder" / "staff", staff_dir)

    pipeline = _make_adder_pipeline(submission_dir, staff_dir, build_dir)
    with config(root_directory=tmp_path):
        score = pipeline()

    test_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Tests"
    )
    assert test_contrib.earned < 15.0


@pytest.mark.slow
def test_cmake_adder_wrong_formula_fails(tmp_path):
    submission_dir = tmp_path / "submission"
    staff_dir = tmp_path / "staff"
    build_dir = tmp_path / "build"
    copy_submission(
        PROJECTS / "cmake_adder" / "submissions" / "wrong_formula", submission_dir
    )
    copy_staff(PROJECTS / "cmake_adder" / "staff", staff_dir)

    pipeline = _make_adder_pipeline(submission_dir, staff_dir, build_dir)
    with config(root_directory=tmp_path):
        score = pipeline()

    test_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Tests"
    )
    assert test_contrib.earned < 15.0


@pytest.mark.slow
def test_cmake_adder_compile_error_stops(tmp_path):
    submission_dir = tmp_path / "submission"
    staff_dir = tmp_path / "staff"
    build_dir = tmp_path / "build"
    copy_submission(
        PROJECTS / "cmake_adder" / "submissions" / "compile_error", submission_dir
    )
    copy_staff(PROJECTS / "cmake_adder" / "staff", staff_dir)

    pipeline = _make_adder_pipeline(submission_dir, staff_dir, build_dir)
    with config(root_directory=tmp_path):
        score = pipeline()

    build_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Build"
    )
    test_contrib = next(
        c for _, c in score.contributions if _.scorer and _.scorer.label == "Tests"
    )
    assert build_contrib.earned == 0.0
    assert test_contrib.earned == 0.0
