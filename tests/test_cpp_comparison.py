from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator

from testing_utils import create_dummy_submission, get_results

from lograder.grader.builders.cpp.cxx_source import CxxSourceBuilder
from lograder.grader.builders.dispatcher import ProjectDispatcher
from lograder.grader.submission_handler import SubmissionHandler
from lograder.grader.tests.output_comparison import (
    TestCaseDict,
    TestCaseProtocol,
    make_tests_from_files,
    make_tests_from_generator,
    make_tests_from_strs,
)


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


def test_cpp_echo_file(tmp_path: Path):
    ifile = tmp_path / "input.txt"
    ofile = tmp_path / "output.txt"
    with open(ifile, "w") as f:
        f.write("Hello World")
    with open(ofile, "w") as f:
        f.write("Hello World")

    create_dummy_submission(tmp_path, Path("tests/test-projects/cpp-cmp-project-2"))

    SubmissionHandler.clear()

    builder = CxxSourceBuilder()
    make_tests_from_files(
        builder=builder,
        names=['Echoing "Hello World" (both files).'],
        input_files=[ifile],
        expected_output_files=[ofile],
    )
    make_tests_from_files(
        builder=builder,
        names=['Echoing "Hello World" (input file, output string).'],
        input_files=[ifile],
        expected_output_strs=["Hello World"],
    )
    make_tests_from_files(
        builder=builder,
        names=['Echoing "Hello World" (input string, output file).'],
        input_strs=["Hello World"],
        expected_output_files=[ofile],
    )
    make_tests_from_files(
        builder=builder,
        names=['Echoing "Hello World" (both strings).'],
        input_strs=["Hello World"],
        expected_output_strs=["Hello World"],
    )
    SubmissionHandler.make_submission(
        assignment_name="Test `Echo` from `lograder` with files!",
        assignment_authors=["Logan Dapp"],
        assignment_description="Test the most basic compilation process.",
        assignment_due_date=datetime.now() + timedelta(hours=9.53),
    )

    results = get_results()
    for test in results["tests"]:
        print(test["output"])
        assert test["score"] == test["max_score"]


def test_cpp_echo_gen(tmp_path: Path):
    N_TESTS: int = 1

    SubmissionHandler.clear()

    builder = CxxSourceBuilder()

    class Case(TestCaseProtocol):
        def __init__(self, num: int):
            self._name: str = str(num)

        def get_name(self):
            return self._name

        def get_input(self):
            return self._name

        def get_expected_output(self):
            return self._name

    @make_tests_from_generator(builder)
    def test_generator_dict() -> Generator[TestCaseDict, None, None]:
        for i in range(N_TESTS):
            yield TestCaseDict(name=f"{i}", input=f"{i}", expected_output=f"{i}")

    @make_tests_from_generator(builder)
    def test_generator_protocol() -> Generator[TestCaseProtocol, None, None]:
        for i in range(N_TESTS):
            yield Case(i)

    create_dummy_submission(tmp_path, Path("tests/test-projects/cpp-cmp-project-2"))

    SubmissionHandler.make_submission(
        assignment_name="Test `Echo` from `lograder` with files!",
        assignment_authors=["Logan Dapp"],
        assignment_description="Test the most basic compilation process.",
        assignment_due_date=datetime.now() + timedelta(hours=9.53),
    )

    results = get_results()

    assert len(results["tests"]) == 2 * N_TESTS

    for test in results["tests"]:

        print(test["output"])
        assert test["score"] == test["max_score"]
