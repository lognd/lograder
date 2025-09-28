from .file import make_tests_from_files
from .generator import make_tests_from_generator
from .output_tests import CLIOutputTest
from .simple import make_tests_from_strs
from .template import make_tests_from_template
from .types import TemplateSubstitution, TestCaseDict, TSub

__all__ = [
    "make_tests_from_files",
    "make_tests_from_generator",
    "make_tests_from_strs",
    "make_tests_from_template",
    "CLIOutputTest",
    "TestCaseDict",
    "TemplateSubstitution",
    "TSub",
]
