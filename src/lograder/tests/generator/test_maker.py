from typing import Callable, Generator, List

from ..registry import TestRegistry
from ..test import ExecutableOutputComparisonTest
from .types import (
    FlaggedTestCaseProtocol,
    FlaggedWeightedTestCaseProtocol,
    TestCase,
    TestCaseProtocol,
    WeightedTestCaseProtocol,
)


def make_tests_from_generator(
    generator: Callable[[], Generator[TestCase, None, None]],
) -> None:
    generated_tests: List[ExecutableOutputComparisonTest] = []
    for test_case in generator():
        if isinstance(test_case, WeightedTestCaseProtocol):
            test = ExecutableOutputComparisonTest(
                name=test_case.get_name(),
                input=test_case.get_input(),
                expected_output=test_case.get_expected_output(),
                weight=test_case.get_weight(),
                flags=[],
            )
            generated_tests.append(test)
        elif isinstance(test_case, TestCaseProtocol):
            test = ExecutableOutputComparisonTest(
                name=test_case.get_name(),
                input=test_case.get_input(),
                expected_output=test_case.get_expected_output(),
                weight=1.0,
                flags=[],
            )
            generated_tests.append(test)
        elif isinstance(test_case, FlaggedWeightedTestCaseProtocol):
            test = ExecutableOutputComparisonTest(
                name=test_case.get_name(),
                input=test_case.get_input(),
                expected_output=test_case.get_expected_output(),
                weight=test_case.get_weight(),
                flags=test_case.get_flags(),
            )
            generated_tests.append(test)
        elif isinstance(test_case, FlaggedTestCaseProtocol):
            test = ExecutableOutputComparisonTest(
                name=test_case.get_name(),
                input=test_case.get_input(),
                expected_output=test_case.get_expected_output(),
                weight=1.0,
                flags=test_case.get_flags(),
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

            test = ExecutableOutputComparisonTest(
                name=test_case["name"],
                input=test_case["input"],
                expected_output=test_case["expected_output"],
                weight=weight,
                flags=flags,
            )
            generated_tests.append(test)
        else:
            raise ValueError(
                f"`generator` passed to `make_tests_from_generator` produced a type, `{type(test_case)}`, which is not supported."
            )

    TestRegistry.extend(generated_tests)
