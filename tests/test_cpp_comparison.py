from datetime import datetime, timedelta
from pathlib import Path

from testing_utils import create_dummy_submission, get_results

from lograder.grader.builders.dispatcher import ProjectDispatcher
from lograder.grader.submission_handler import SubmissionHandler
from lograder.grader.tests.output_comparison import make_tests_from_strs


def test_cpp_hello_world(tmp_path: Path):
    create_dummy_submission(tmp_path, Path("tests/test-projects/cpp-cmp-project-1"))

    SubmissionHandler.clear()

    builder = ProjectDispatcher()
    builder.set_allowed_project_types(["cxx-source"])
    builder.load_builder()
    make_tests_from_strs(
        builder=builder,
        names=["Test `Hello World`."],
        inputs=[""],
        expected_outputs=["Hello World from `lograder`!"],
    )
    SubmissionHandler.make_submission(
        assignment_name="Hello World from `lograder`!",
        assignment_authors=["Logan Dapp"],
        assignment_description="Test the most basic compilation process.",
        assignment_due_date=datetime.now() + timedelta(hours=9.53),
    )


def test_cpp_echo(tmp_path: Path):
    create_dummy_submission(tmp_path, Path("tests/test-projects/cpp-cmp-project-2"))

    SubmissionHandler.clear()

    builder = ProjectDispatcher()
    builder.set_allowed_project_types(["cxx-source"])
    builder.load_builder()
    make_tests_from_strs(
        builder=builder,
        names=['Echoing "Hello World".'],
        inputs=["Hello World"],
        expected_outputs=["Hello World"],
    )
    SubmissionHandler.make_submission(
        assignment_name="Test `Echo` from `lograder`!",
        assignment_authors=["Logan Dapp"],
        assignment_description="Test the most basic compilation process.",
        assignment_due_date=datetime.now() + timedelta(hours=9.53),
    )

    results = get_results()
    for test in results["tests"]:
        assert test["score"] == test["max_score"]
