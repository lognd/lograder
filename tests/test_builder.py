from pathlib import Path
import shutil
import pytest

from lograder.tests import make_tests_from_files
from lograder.builder import ProjectBuilder

@pytest.mark.description('Testing C++ Source Build of correct "Hello World!" project.')
def test_project_1(tmp_path):
    here = Path(__file__).parent
    src_project_dir = here / "project-1"
    shutil.copytree(src_project_dir, tmp_path)

    assert (tmp_path / "hello_world.cpp").is_file()
    assert (tmp_path / "expected_output.txt").is_file()

    make_tests_from_files(
        names = ['Testing C++ Source Build of correct "Hello World!" project.'],
        expected_output_files=[tmp_path / "expected_output.txt"]
    )

    assignment = ProjectBuilder(tmp_path)
    preprocessor_results = assignment.preprocess()
    build_results = assignment.build()
    runtime_results = assignment.run_tests()

    assert runtime_results.get_test_cases()[0].get_successful()

@pytest.mark.description('Testing CMake Build of correct "Hello World!" project.')
def test_project_2(tmp_path):
    here = Path(__file__).parent
    src_project_dir = here / "project-2"
    shutil.copytree(src_project_dir, tmp_path)

    assert (tmp_path / "main.cpp").is_file()
    assert (tmp_path / "CMakeLists.txt").is_file()
    assert (tmp_path / "expected_output.txt").is_file()

    make_tests_from_files(
        names=['Testing CMake Build of correct "Hello World!" project.'],
        expected_output_files=[tmp_path / "expected_output.txt"]
    )

    assignment = ProjectBuilder(tmp_path)
    preprocessor_results = assignment.preprocess()
    build_results = assignment.build()
    runtime_results = assignment.run_tests()

    assert runtime_results.get_test_cases()[0].get_successful()

@pytest.mark.description('Testing Makefile Build of correct "Hello World!" project.')
def test_project_3(tmp_path):
    here = Path(__file__).parent
    src_project_dir = here / "project-3"
    shutil.copytree(src_project_dir, tmp_path)

    assert (tmp_path / "main.cpp").is_file()
    assert (tmp_path / "Makefile").is_file()
    assert (tmp_path / "expected_output.txt").is_file()

    make_tests_from_files(
        names=['Testing Makefile Build of correct "Hello World!" project.'],
        expected_output_files=[tmp_path / "expected_output.txt"]
    )

    assignment = ProjectBuilder(tmp_path)
    preprocessor_results = assignment.preprocess()
    build_results = assignment.build()
    runtime_results = assignment.run_tests()

    assert runtime_results.get_test_cases()[0].get_successful()

@pytest.mark.description('Testing C++ Source Build of bad "Hello World!" project.')
def test_project_4(tmp_path):
    here = Path(__file__).parent
    src_project_dir = here / "project-4"
    shutil.copytree(src_project_dir, tmp_path)

    assert (tmp_path / "hello_world.cpp").is_file()
    assert (tmp_path / "expected_output.txt").is_file()

    make_tests_from_files(
        names=['Testing C++ Source Build of bad "Hello World!" project.'],
        expected_output_files=[tmp_path / "expected_output.txt"]
    )

    assignment = ProjectBuilder(tmp_path)
    preprocessor_results = assignment.preprocess()
    build_results = assignment.build()
    runtime_results = assignment.run_tests()

    assert runtime_results.get_test_cases()[0].get_successful() is False

@pytest.mark.description('Testing CMake Build of bad "Hello World!" project.')
def test_project_5(tmp_path):
    here = Path(__file__).parent
    src_project_dir = here / "project-5"
    shutil.copytree(src_project_dir, tmp_path)

    assert (tmp_path / "main.cpp").is_file()
    assert (tmp_path / "CMakeLists.txt").is_file()
    assert (tmp_path / "expected_output.txt").is_file()

    make_tests_from_files(
        names=['Testing CMake Build of bad "Hello World!" project.'],
        expected_output_files=[tmp_path / "expected_output.txt"]
    )

    assignment = ProjectBuilder(tmp_path)
    preprocessor_results = assignment.preprocess()
    build_results = assignment.build()
    runtime_results = assignment.run_tests()

    assert runtime_results.get_test_cases()[0].get_successful() is False

@pytest.mark.description('Testing Makefile Build of bad "Hello World!" project.')
def test_project_6(tmp_path):
    here = Path(__file__).parent
    src_project_dir = here / "project-6"
    shutil.copytree(src_project_dir, tmp_path)

    assert (tmp_path / "main.cpp").is_file()
    assert (tmp_path / "Makefile").is_file()
    assert (tmp_path / "expected_output.txt").is_file()

    make_tests_from_files(
        names=['Testing Makefile Build of bad "Hello World!" project.'],
        expected_output_files=[tmp_path / "expected_output.txt"]
    )

    assignment = ProjectBuilder(tmp_path)
    preprocessor_results = assignment.preprocess()
    build_results = assignment.build()
    runtime_results = assignment.run_tests()

    assert runtime_results.get_test_cases()[0].get_successful() is False


