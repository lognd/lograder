from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Generator, List

from .output_tests import CLIOutputTest
from .types import (
    FlaggedTestCaseProtocol,
    FlaggedWeightedTestCaseProtocol,
    TestCase,
    TestCaseProtocol,
    WeightedTestCaseProtocol,
)

if TYPE_CHECKING:
    from ...builders.interfaces.builder import BuilderInterface


def make_tests_from_generator(builder: BuilderInterface):
    def decorator(
        generator: Callable[[], Generator[TestCase, None, None]],
    ) -> None:
        generated_tests: List[CLIOutputTest] = []
        for test_case in generator():
            if isinstance(test_case, WeightedTestCaseProtocol):
                test = CLIOutputTest.make(
                    name=test_case.get_name(),
                    builder=builder,
                    stdin=test_case.get_input(),
                    expected_stdout=test_case.get_expected_output(),
                    weight=test_case.get_weight(),
                    args=[],
                    working_dir=builder.get_build_directory(),
                    wrap_args=builder.wrap_args(),
                )
                generated_tests.append(test)
            elif isinstance(test_case, TestCaseProtocol):
                test = CLIOutputTest.make(
                    name=test_case.get_name(),
                    builder=builder,
                    stdin=test_case.get_input(),
                    expected_stdout=test_case.get_expected_output(),
                    weight=1.0,
                    args=[],
                    working_dir=builder.get_build_directory(),
                    wrap_args=builder.wrap_args(),
                )
                generated_tests.append(test)
            elif isinstance(test_case, FlaggedWeightedTestCaseProtocol):
                test = CLIOutputTest.make(
                    name=test_case.get_name(),
                    builder=builder,
                    stdin=test_case.get_input(),
                    expected_stdout=test_case.get_expected_output(),
                    weight=test_case.get_weight(),
                    args=test_case.get_flags(),
                    working_dir=builder.get_build_directory(),
                    wrap_args=builder.wrap_args(),
                )
                generated_tests.append(test)
            elif isinstance(test_case, FlaggedTestCaseProtocol):
                test = CLIOutputTest.make(
                    name=test_case.get_name(),
                    builder=builder,
                    stdin=test_case.get_input(),
                    expected_stdout=test_case.get_expected_output(),
                    weight=1.0,
                    args=test_case.get_flags(),
                    working_dir=builder.get_build_directory(),
                    wrap_args=builder.wrap_args(),
                )
                generated_tests.append(test)
            elif isinstance(test_case, dict):
                if "weight" in test_case:
                    weight = test_case["weight"]
                else:
                    weight = 1.0
                if "flags" in test_case:
                    flags = test_case["flags"]
                else:
                    flags = []

                test = CLIOutputTest.make(
                    name=test_case["name"],
                    builder=builder,
                    stdin=test_case["input"],
                    expected_stdout=test_case["expected_output"],
                    weight=weight,
                    args=flags,
                    working_dir=builder.get_build_directory(),
                    wrap_args=builder.wrap_args(),
                )
                generated_tests.append(test)
            else:
                raise ValueError(
                    f"`generator` passed to `make_tests_from_generator` produced a type, `{type(test_case)}`, which is not supported."
                )

    return decorator
