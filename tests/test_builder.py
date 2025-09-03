import shutil
import sys
from datetime import datetime
from pathlib import Path

import pytest

from lograder.dispatch import AssignmentSummary, ProjectDispatcher
from lograder.output.formatters.default import (
    AssignmentMetadata,
    DefaultExecutableTestCaseFormatter,
)
from lograder.tests import make_tests_from_files


@pytest.mark.description('Testing C++ Source Build of correct "Hello World!" project.')
def test_project_1(tmp_path):
    here = Path(__file__).parent
    src_project_dir = here / "test-projects" / "project-1"
    shutil.copytree(src_project_dir, tmp_path, dirs_exist_ok=True)

    assert (tmp_path / "hello_world.cpp").is_file()
    assert (tmp_path / "expected_output.txt").is_file()

    make_tests_from_files(
        names=['Testing C++ Source Build of correct "Hello World!" project.'],
        expected_output_files=[tmp_path / "expected_output.txt"],
        input_strs=[""],
    )

    assignment = ProjectDispatcher(tmp_path)
    metadata = AssignmentMetadata(
        assignment_name="Lograder Unit Testing",
        assignment_authors=["Logan Dapp"],
        assignment_description="for `pytest`-ing of the Gradescope Autograder library.",
        assignment_due_date=datetime(year=2030, month=12, day=12),
    )
    preprocessor_results = assignment.preprocess()
    builder_results = assignment.build()
    runtime_results = assignment.run_tests()
    summary = AssignmentSummary(
        metadata=metadata,
        preprocessor_output=preprocessor_results.get_output(),
        build_output=builder_results.get_output(),
        test_cases=runtime_results.get_test_cases(),
    )
    print(summary.get_assignment_text())
    for test in runtime_results.get_test_cases():
        print(DefaultExecutableTestCaseFormatter().format(test))
        assert test.get_successful()


@pytest.mark.description('Testing CMake Build of correct "Hello World!" project.')
def test_project_2(tmp_path):
    here = Path(__file__).parent
    src_project_dir = here / "test-projects" / "project-2"
    shutil.copytree(src_project_dir, tmp_path, dirs_exist_ok=True)

    assert (tmp_path / "main.cpp").is_file()
    assert (tmp_path / "CMakeLists.txt").is_file()
    assert (tmp_path / "expected_output.txt").is_file()

    make_tests_from_files(
        names=['Testing CMake Build of correct "Hello World!" project.'],
        expected_output_files=[tmp_path / "expected_output.txt"],
        input_strs=[""],
    )

    assignment = ProjectDispatcher(tmp_path)

    metadata = AssignmentMetadata(
        assignment_name="Lograder Unit Testing",
        assignment_authors=["Logan Dapp"],
        assignment_description="for `pytest`-ing of the Gradescope Autograder library.",
        assignment_due_date=datetime(year=2030, month=12, day=12),
    )
    preprocessor_results = assignment.preprocess()
    builder_results = assignment.build()
    runtime_results = assignment.run_tests()
    summary = AssignmentSummary(
        metadata=metadata,
        preprocessor_output=preprocessor_results.get_output(),
        build_output=builder_results.get_output(),
        test_cases=runtime_results.get_test_cases(),
    )
    print(summary.get_assignment_text())
    for test in runtime_results.get_test_cases():
        print(DefaultExecutableTestCaseFormatter().format(test))
        assert test.get_successful()


if not sys.platform.startswith("win"):

    @pytest.mark.description(
        'Testing Makefile Build of correct "Hello World!" project.'
    )
    def test_project_3(tmp_path):
        here = Path(__file__).parent
        src_project_dir = here / "test-projects" / "project-3"
        shutil.copytree(src_project_dir, tmp_path, dirs_exist_ok=True)

        assert (tmp_path / "main.cpp").is_file()
        assert (tmp_path / "Makefile").is_file()
        assert (tmp_path / "expected_output.txt").is_file()

        make_tests_from_files(
            names=['Testing Makefile Build of correct "Hello World!" project.'],
            expected_output_files=[tmp_path / "expected_output.txt"],
            input_strs=[""],
        )

        assignment = ProjectDispatcher(tmp_path)
        metadata = AssignmentMetadata(
            assignment_name="Lograder Unit Testing",
            assignment_authors=["Logan Dapp"],
            assignment_description="for `pytest`-ing of the Gradescope Autograder library.",
            assignment_due_date=datetime(year=2030, month=12, day=12),
        )
        preprocessor_results = assignment.preprocess()
        builder_results = assignment.build()
        runtime_results = assignment.run_tests()
        summary = AssignmentSummary(
            metadata=metadata,
            preprocessor_output=preprocessor_results.get_output(),
            build_output=builder_results.get_output(),
            test_cases=runtime_results.get_test_cases(),
        )
        print(summary.get_assignment_text())
        for test in runtime_results.get_test_cases():
            print(DefaultExecutableTestCaseFormatter().format(test))
            assert test.get_successful()


@pytest.mark.description('Testing C++ Source Build of bad "Hello World!" project.')
def test_project_4(tmp_path):
    here = Path(__file__).parent
    src_project_dir = here / "test-projects" / "project-4"
    shutil.copytree(src_project_dir, tmp_path, dirs_exist_ok=True)

    assert (tmp_path / "bad_hello_world.cpp").is_file()
    assert (tmp_path / "expected_output.txt").is_file()

    make_tests_from_files(
        names=['Testing C++ Source Build of bad "Hello World!" project.'],
        expected_output_files=[tmp_path / "expected_output.txt"],
        input_strs=[""],
    )

    assignment = ProjectDispatcher(tmp_path)
    metadata = AssignmentMetadata(
        assignment_name="Lograder Unit Testing",
        assignment_authors=["Logan Dapp"],
        assignment_description="for `pytest`-ing of the Gradescope Autograder library.",
        assignment_due_date=datetime(year=2030, month=12, day=12),
    )
    preprocessor_results = assignment.preprocess()
    builder_results = assignment.build()
    runtime_results = assignment.run_tests()
    summary = AssignmentSummary(
        metadata=metadata,
        preprocessor_output=preprocessor_results.get_output(),
        build_output=builder_results.get_output(),
        test_cases=runtime_results.get_test_cases(),
    )
    print(summary.get_assignment_text())
    for test in runtime_results.get_test_cases():
        print(DefaultExecutableTestCaseFormatter().format(test))
        assert test.get_successful() is False


@pytest.mark.description('Testing CMake Build of bad "Hello World!" project.')
def test_project_5(tmp_path):
    here = Path(__file__).parent
    src_project_dir = here / "test-projects" / "project-5"
    shutil.copytree(src_project_dir, tmp_path, dirs_exist_ok=True)

    assert (tmp_path / "bad_main.cpp").is_file()
    assert (tmp_path / "CMakeLists.txt").is_file()
    assert (tmp_path / "expected_output.txt").is_file()

    make_tests_from_files(
        names=['Testing CMake Build of bad "Hello World!" project.'],
        expected_output_files=[tmp_path / "expected_output.txt"],
        input_strs=[""],
    )

    assignment = ProjectDispatcher(tmp_path)
    metadata = AssignmentMetadata(
        assignment_name="Lograder Unit Testing",
        assignment_authors=["Logan Dapp"],
        assignment_description="for `pytest`-ing of the Gradescope Autograder library.",
        assignment_due_date=datetime(year=2030, month=12, day=12),
    )
    preprocessor_results = assignment.preprocess()
    builder_results = assignment.build()
    runtime_results = assignment.run_tests()
    summary = AssignmentSummary(
        metadata=metadata,
        preprocessor_output=preprocessor_results.get_output(),
        build_output=builder_results.get_output(),
        test_cases=runtime_results.get_test_cases(),
    )
    print(summary.get_assignment_text())
    for test in runtime_results.get_test_cases():
        print(DefaultExecutableTestCaseFormatter().format(test))
        assert test.get_successful() is False


if not sys.platform.startswith("win"):

    @pytest.mark.description('Testing Makefile Build of bad "Hello World!" project.')
    def test_project_6(tmp_path):
        here = Path(__file__).parent
        src_project_dir = here / "test-projects" / "project-6"
        shutil.copytree(src_project_dir, tmp_path, dirs_exist_ok=True)

        assert (tmp_path / "bad_main.cpp").is_file()
        assert (tmp_path / "Makefile").is_file()
        assert (tmp_path / "expected_output.txt").is_file()

        make_tests_from_files(
            names=['Testing Makefile Build of bad "Hello World!" project.'],
            expected_output_files=[tmp_path / "expected_output.txt"],
            input_strs=[""],
        )

        assignment = ProjectDispatcher(tmp_path)
        metadata = AssignmentMetadata(
            assignment_name="Lograder Unit Testing",
            assignment_authors=["Logan Dapp"],
            assignment_description="for `pytest`-ing of the Gradescope Autograder library.",
            assignment_due_date=datetime(year=2030, month=12, day=12),
        )
        preprocessor_results = assignment.preprocess()
        builder_results = assignment.build()
        runtime_results = assignment.run_tests()
        summary = AssignmentSummary(
            metadata=metadata,
            preprocessor_output=preprocessor_results.get_output(),
            build_output=builder_results.get_output(),
            test_cases=runtime_results.get_test_cases(),
        )
        print(summary.get_assignment_text())
        for test in runtime_results.get_test_cases():
            print(DefaultExecutableTestCaseFormatter().format(test))
            assert test.get_successful() is False
