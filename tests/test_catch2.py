import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from testing_utils import create_dummy_submission, get_results

from lograder.grader.submission_handler import SubmissionHandler
from lograder.grader.tests.unit_tests.directory import make_unit_test_from_directory


@pytest.mark.skipif(sys.platform != "win32", reason="WSL makes this really slow.")
def test_cpp_catch2_1(tmp_path: Path):
    create_dummy_submission(tmp_path, Path("tests/test-projects/cpp-catch2-project-1"))

    SubmissionHandler.clear()

    make_unit_test_from_directory(name="Catch2 Simple Project")

    SubmissionHandler.make_submission(
        assignment_name="Hello World from `lograder`!",
        assignment_authors=["Logan Dapp"],
        assignment_description="Test the most basic catch2 process.",
        assignment_due_date=datetime.now() + timedelta(hours=9.53),
    )

    results = get_results()
    for test in results["tests"]:
        assert test["score"] == test["max_score"]


@pytest.mark.skipif(sys.platform != "win32", reason="WSL makes this really slow.")
def test_cpp_catch2_2(tmp_path: Path):
    create_dummy_submission(tmp_path, Path("tests/test-projects/cpp-catch2-project-2"))

    SubmissionHandler.clear()

    make_unit_test_from_directory(name="Catch2 Simple Project")

    SubmissionHandler.make_submission(
        assignment_name="Hello World from `lograder`!",
        assignment_authors=["Logan Dapp"],
        assignment_description="Test the most basic catch2 process.",
        assignment_due_date=datetime.now() + timedelta(hours=9.53),
    )

    results = get_results()
    for test in results["tests"]:
        assert test["score"] == test["max_score"]


@pytest.mark.skipif(sys.platform != "win32", reason="WSL makes this really slow.")
def test_cpp_catch2_partial(tmp_path: Path):
    create_dummy_submission(
        tmp_path, Path("tests/test-projects/cpp-catch2-partial-project-1")
    )

    SubmissionHandler.clear()

    make_unit_test_from_directory(name="Catch2 Simple Project")

    SubmissionHandler.make_submission(
        assignment_name="Hello World from `lograder`!",
        assignment_authors=["Logan Dapp"],
        assignment_description="Test the most basic catch2 process.",
        assignment_due_date=datetime.now() + timedelta(hours=9.53),
    )

    results = get_results()
    for test in results["tests"]:
        assert test["score"] == test["max_score"] * 0.5


@pytest.mark.skipif(sys.platform != "win32", reason="WSL makes this really slow.")
def test_cmake_catch2_1(tmp_path: Path):
    create_dummy_submission(
        tmp_path, Path("tests/test-projects/cmake-catch2-project-1")
    )

    SubmissionHandler.clear()

    make_unit_test_from_directory(name="Catch2 Simple Project")

    SubmissionHandler.make_submission(
        assignment_name="Hello World from `lograder`!",
        assignment_authors=["Logan Dapp"],
        assignment_description="Test the most basic catch2 process.",
        assignment_due_date=datetime.now() + timedelta(hours=9.53),
    )

    results = get_results()
    for test in results["tests"]:
        assert test["score"] == test["max_score"]


@pytest.mark.skipif(sys.platform != "win32", reason="WSL makes this really slow.")
def test_cmake_catch2_2(tmp_path: Path):
    create_dummy_submission(
        tmp_path, Path("tests/test-projects/cmake-catch2-project-2")
    )

    SubmissionHandler.clear()

    make_unit_test_from_directory(name="Catch2 Simple Project")

    SubmissionHandler.make_submission(
        assignment_name="Hello World from `lograder`!",
        assignment_authors=["Logan Dapp"],
        assignment_description="Test the most basic catch2 process.",
        assignment_due_date=datetime.now() + timedelta(hours=9.53),
    )

    results = get_results()
    for test in results["tests"]:
        assert test["score"] == test["max_score"]
