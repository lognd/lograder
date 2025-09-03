import sys
from pathlib import Path
from typing import Generator

import pytest

from lograder.tests import (
    TestCaseDict,
    TestCaseTemplate,
    TestRegistry,
    TSub,
    make_tests_from_files,
    make_tests_from_generator,
    make_tests_from_strs,
    make_tests_from_template,
)


@pytest.mark.description(
    "Testing the successful tests constructed from basic strings (using `make_tests_from_strs`)."
)
def test_basic_strs_success():
    TestRegistry.clear()

    num_tests: int = 10

    tests = make_tests_from_strs(
        names=[f"Test Case #{i}" for i in range(num_tests)],
        inputs=[f"{i}" for i in range(num_tests)],
        expected_outputs=[f"{i}" for i in range(num_tests)],
    )
    for i, test in enumerate(tests):
        assert test.get_expected_output() == f"{i}"


@pytest.mark.description(
    "Testing the unsuccessful tests constructed from basic strings (using `make_tests_from_strs`)."
)
def test_basic_strs_failure():
    TestRegistry.clear()

    num_tests: int = 10
    tests = make_tests_from_strs(
        names=[f"Test Case #{i}" for i in range(num_tests)],
        inputs=[f"{i}" for i in range(num_tests)],
        expected_outputs=[f"{i}" for i in range(num_tests)],
    )
    for i, test in enumerate(tests):
        assert test.get_expected_output() != "-1"


@pytest.mark.description("Testing to see if flags are passed correctly from tests.")
def test_flag_strs():
    TestRegistry.clear()

    num_tests: int = 10
    tests = make_tests_from_strs(
        names=[f"Test Case #{i}" for i in range(num_tests)],
        inputs=["" for _ in range(num_tests)],
        expected_outputs=[f"{i}" for i in range(num_tests)],
        flag_sets=[[f"{i}"] for i in range(num_tests)],
    )
    for i, test in enumerate(tests):
        if sys.platform.startswith("win"):
            test.set_target(["cmd", "/c", "echo"])
        else:
            test.set_target(["echo"])
        test.run()
        assert test.get_successful()


@pytest.mark.description("Testing to see if stdin is passed correctly from tests.")
def test_input_strs():
    TestRegistry.clear()

    num_tests: int = 10
    tests = make_tests_from_strs(
        names=[f"Test Case #{i}" for i in range(num_tests)],
        inputs=[f"{i}" for i in range(num_tests)],
        expected_outputs=[f"{i}" for i in range(num_tests)],
    )
    for i, test in enumerate(tests):
        if sys.platform.startswith("win"):
            test.set_target(["cmd", "/c", "more"])
        else:
            test.set_target(["cat"])
        test.run()
        assert test.get_successful()


@pytest.mark.description(
    "Testing the successful tests constructed from files (using `make_tests_from_files`)."
)
def test_basic_files_success():
    TestRegistry.clear()

    here = Path(__file__).parent
    tests = make_tests_from_files(
        names=["Test Case #0", "Test Case #1"],
        input_files=[
            here / "file_input" / "input-0.txt",
            here / "file_input" / "input-1.txt",
        ],
        expected_output_files=[
            here / "file_output" / "output-0.txt",
            here / "file_output" / "output-1.txt",
        ],
    )
    for i, test in enumerate(tests):
        assert test.get_expected_output() == f"{i}"


@pytest.mark.description(
    "Testing the unsuccessful tests constructed from files (using `make_tests_from_files`)."
)
def test_basic_files_failure():
    TestRegistry.clear()
    here = Path(__file__).parent
    tests = make_tests_from_files(
        names=["Test Case #0", "Test Case #1"],
        input_files=[
            here / "file_input" / "input-0.txt",
            here / "file_input" / "input-1.txt",
        ],
        expected_output_files=[
            here / "file_output" / "output-0.txt",
            here / "file_output" / "output-1.txt",
        ],
    )
    for i, test in enumerate(tests):
        assert test.get_expected_output() != "-1"


@pytest.mark.description(
    "Testing the successful tests constructed from template (using `make_tests_from_template`)."
)
def test_basic_templates_success():
    TestRegistry.clear()

    num_tests: int = 10
    here = Path(__file__).parent
    tests = make_tests_from_template(
        names=[f"Test Case #{i}" for i in range(num_tests)],
        template=TestCaseTemplate(
            input_template_str="{}",
            input_substitutions=[TSub(i) for i in range(num_tests)],
            expected_output_template_file=here / "file_template" / "template-0.txt",
            expected_output_substitutions=[TSub(i) for i in range(num_tests)],
        ),
    )
    for i, test in enumerate(tests):
        assert test.get_expected_output().strip() == f"{i}"


@pytest.mark.description(
    "Testing the unsuccessful tests constructed from template (using `make_tests_from_template`)."
)
def test_basic_templates_failure():
    TestRegistry.clear()

    num_tests: int = 10
    here = Path(__file__).parent
    tests = make_tests_from_template(
        names=[f"Test Case #{i}" for i in range(num_tests)],
        template=TestCaseTemplate(
            input_template_str="{}",
            input_substitutions=[TSub(i) for i in range(num_tests)],
            expected_output_template_file=here / "file_template" / "template-0.txt",
            expected_output_substitutions=[TSub(i) for i in range(num_tests)],
        ),
    )
    for i, test in enumerate(tests):
        assert test.get_expected_output() != "-1"


@pytest.mark.description(
    "Testing the successful tests constructed from function generator (using `make_tests_from_generator`)."
)
def test_basic_generator_success():
    TestRegistry.clear()

    num_tests: int = 10

    @make_tests_from_generator
    def make_tests() -> Generator[TestCaseDict, None, None]:
        for i in range(num_tests):
            case: TestCaseDict = {
                "name": f"Test Case #{i}",
                "input": f"{i}",
                "expected_output": f"{i}",
            }
            yield case

    for i, test in enumerate(TestRegistry.iterate()):
        assert test.get_expected_output() == f"{i}"


@pytest.mark.description(
    "Testing the unsuccessful tests constructed from function generator (using `make_tests_from_generator`)."
)
def test_basic_generator_failure():
    TestRegistry.clear()

    num_tests: int = 10

    @make_tests_from_generator
    def make_tests() -> Generator[TestCaseDict, None, None]:
        for i in range(num_tests):
            case: TestCaseDict = {
                "name": f"Test Case #{i}",
                "input": f"{i}",
                "expected_output": f"{i}",
            }
            yield case

    for i, test in enumerate(TestRegistry.iterate()):
        assert test.get_expected_output() != "-1"
