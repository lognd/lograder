from typing import List, TYPE_CHECKING
from datetime import datetime, timedelta

from lograder.grader.submission_handler import SubmissionHandler
from lograder.grader.tests.unit_tests.directory import make_unit_test_from_directory
from lograder.grader.builders.dispatcher import ProjectDispatcher
from lograder.grader.builders.cpp.cxx_source import CxxSourceBuilder
from lograder.grader.builders.cpp.cmake import CMakeBuilder
from lograder.grader.tests.output_comparison import (
    TestCaseDict,
    TestCaseProtocol,
    make_tests_from_files,
    make_tests_from_generator,
    make_tests_from_strs,
    make_tests_from_template,
    TemplateSubstitution,
    TSub,
)
from lograder.grader.addons.valgrind import ValgrindAddon
from lograder.grader.tests.interfaces.test import TestInterface

if TYPE_CHECKING:
    from lograder.grader.tests.output_comparison.output_tests import OutputTestInterface
    from lograder.grader.tests.unit_tests.catch2 import Catch2UnitTest

__all__ = [
    "make_unit_test_from_directory",
    "make_tests_from_files",
    "make_tests_from_generator",
    "make_tests_from_strs",
    "make_tests_from_template",
    "ProjectDispatcher",
    "CMakeBuilder",
    "CxxSourceBuilder",
    "TestCaseDict",
    "TestCaseProtocol"
]

def initialize_assignment():
    SubmissionHandler.clear()

def add_valgrind(test: OutputTestInterface | Catch2UnitTest):
    test.add_exec_addon(ValgrindAddon())

def get_all_tests() -> List[TestInterface]:
    return TestInterface.get_tests()

def finalize_assignment(
    assignment_name: str,
    assignment_authors: List[str],
    assignment_description: str,
    assignment_due_date: datetime
):
    SubmissionHandler.make_submission(
        assignment_name=assignment_name,
        assignment_authors=assignment_authors,
        assignment_description=assignment_description,
        assignment_due_date=assignment_due_date,
    )

def hello_world():
    return "Hello World from `lograder`!"
