import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from testing_utils import create_dummy_submission, get_results

from lograder.data.penalties import PenaltyConfig
from lograder.grader.addons.valgrind import ValgrindAddon
from lograder.grader.builders.dispatcher import ProjectDispatcher
from lograder.grader.submission_handler import SubmissionHandler
from lograder.grader.tests.output_comparison import make_tests_from_strs


@pytest.mark.skipif(sys.platform == "win32", reason="Does not run on Windows")
def test_valgrind_no_leak(tmp_path: Path):
    create_dummy_submission(
        tmp_path, Path("tests/test-projects/cpp-valgrind-project-1")
    )

    SubmissionHandler.clear()

    builder = ProjectDispatcher()
    builder.set_allowed_project_types(["cxx-source"])

    tests = make_tests_from_strs(
        builder=builder,
        names=["Test `Hello World`."],
        inputs=[""],
        expected_outputs=[""],
    )
    tests[0].add_exec_addon(ValgrindAddon())
    SubmissionHandler.make_submission(
        assignment_name="Hello World from `lograder`!",
        assignment_authors=["Logan Dapp"],
        assignment_description="Test the most basic compilation process.",
        assignment_due_date=datetime.now() + timedelta(hours=9.53),
    )

    results = get_results()
    for test in results["tests"]:
        assert test["score"] == test["max_score"]


@pytest.mark.skipif(sys.platform == "win32", reason="Does not run on Windows")
def test_valgrind_with_leak(tmp_path: Path):
    create_dummy_submission(
        tmp_path, Path("tests/test-projects/cpp-valgrind-project-2")
    )

    SubmissionHandler.clear()

    builder = ProjectDispatcher()
    builder.set_allowed_project_types(["cxx-source"])

    tests = make_tests_from_strs(
        builder=builder,
        names=["Test `Hello World`."],
        inputs=[""],
        expected_outputs=[""],
    )
    tests[0].add_exec_addon(ValgrindAddon())
    SubmissionHandler.make_submission(
        assignment_name="Hello World from `lograder`!",
        assignment_authors=["Logan Dapp"],
        assignment_description="Test the most basic compilation process.",
        assignment_due_date=datetime.now() + timedelta(hours=9.53),
    )

    results = get_results()
    for test in results["tests"]:
        assert (
            test["score"]
            == test["max_score"] * PenaltyConfig.DEFAULT_VALGRIND_LEAK_PENALTY
        )
