from .common import FilePath
from .file import make_tests_from_files
from .generator import (
    FlaggedTestCaseProtocol,
    FlaggedWeightedTestCaseProtocol,
    TestCaseDict,
    TestCaseProtocol,
    WeightedTestCaseProtocol,
    make_tests_from_generator,
)
from .registry import TestRegistry
from .simple import make_tests_from_strs
from .template import (
    TemplateSubstitution,
    TestCaseTemplate,
    TSub,
    make_tests_from_template,
)
from .test import ComparisonTest

__all__ = [
    "make_tests_from_strs",
    "FilePath",
    "make_tests_from_files",
    "TestCaseProtocol",
    "WeightedTestCaseProtocol",
    "FlaggedTestCaseProtocol",
    "FlaggedWeightedTestCaseProtocol",
    "TestCaseDict",
    "make_tests_from_generator",
    "TemplateSubstitution",
    "TSub",
    "TestCaseTemplate",
    "make_tests_from_template",
    "ComparisonTest",
    "TestRegistry",
]
