import shutil
import sys
from pathlib import Path

import pytest

from lograder.builder import ProjectBuilder
from lograder.output.formatters.default import (
    DefaultBuildOutputFormatter,
    DefaultPreprocessorOutputFormatter,
    DefaultTestCaseFormatter,
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

    assignment = ProjectBuilder(tmp_path)
    preprocessor_results = assignment.preprocess()
    builder_results = assignment.build()
    print(
        DefaultPreprocessorOutputFormatter().format(preprocessor_results.get_output())
    )
    print(DefaultBuildOutputFormatter().format(builder_results.get_output()))

    print("Files:\n  *" + "\n  *".join(str(file) for file in tmp_path.rglob("*")))

    runtime_results = assignment.run_tests()

    for test in runtime_results.get_test_cases():
        print(DefaultTestCaseFormatter().format(test))
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

    assignment = ProjectBuilder(tmp_path)
    preprocessor_results = assignment.preprocess()
    builder_results = assignment.build()
    print(
        DefaultPreprocessorOutputFormatter().format(preprocessor_results.get_output())
    )
    print(DefaultBuildOutputFormatter().format(builder_results.get_output()))

    print("Files:\n  *" + "\n  *".join(str(file) for file in tmp_path.rglob("*")))

    runtime_results = assignment.run_tests()

    for test in runtime_results.get_test_cases():
        print(DefaultTestCaseFormatter().format(test))
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

        assignment = ProjectBuilder(tmp_path)
        preprocessor_results = assignment.preprocess()
        builder_results = assignment.build()
        print(
            DefaultPreprocessorOutputFormatter().format(
                preprocessor_results.get_output()
            )
        )
        print(DefaultBuildOutputFormatter().format(builder_results.get_output()))

        print("Files:\n  *" + "\n  *".join(str(file) for file in tmp_path.rglob("*")))

        runtime_results = assignment.run_tests()
        for test in runtime_results.get_test_cases():
            print(DefaultTestCaseFormatter().format(test))
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

    assignment = ProjectBuilder(tmp_path)
    preprocessor_results = assignment.preprocess()
    builder_results = assignment.build()
    print(
        DefaultPreprocessorOutputFormatter().format(preprocessor_results.get_output())
    )
    print(DefaultBuildOutputFormatter().format(builder_results.get_output()))

    print("Files:\n  *" + "\n  *".join(str(file) for file in tmp_path.rglob("*")))

    runtime_results = assignment.run_tests()

    for test in runtime_results.get_test_cases():
        print(DefaultTestCaseFormatter().format(test))
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

    assignment = ProjectBuilder(tmp_path)
    preprocessor_results = assignment.preprocess()
    builder_results = assignment.build()
    print(
        DefaultPreprocessorOutputFormatter().format(preprocessor_results.get_output())
    )
    print(DefaultBuildOutputFormatter().format(builder_results.get_output()))

    print("Files:\n  *" + "\n  *".join(str(file) for file in tmp_path.rglob("*")))

    runtime_results = assignment.run_tests()

    for test in runtime_results.get_test_cases():
        print(DefaultTestCaseFormatter().format(test))
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

        assignment = ProjectBuilder(tmp_path)

        preprocessor_results = assignment.preprocess()
        builder_results = assignment.build()
        print(
            DefaultPreprocessorOutputFormatter().format(
                preprocessor_results.get_output()
            )
        )
        print(DefaultBuildOutputFormatter().format(builder_results.get_output()))

        print("Files:\n  *" + "\n  *".join(str(file) for file in tmp_path.rglob("*")))

        runtime_results = assignment.run_tests()

        for test in runtime_results.get_test_cases():
            print(DefaultTestCaseFormatter().format(test))
            assert test.get_successful() is False
