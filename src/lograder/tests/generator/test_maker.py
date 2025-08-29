from typing import Callable, Generator, List

from ..registry import TestRegistry
from ..test import ComparisonTest
from .types import TestCase, TestCaseProtocol, WeightedTestCaseProtocol


def make_tests_from_generator(
    generator: Callable[[], Generator[TestCase, None, None]],
) -> None:
    generated_tests: List[ComparisonTest] = []
    for test_case in generator():
        if isinstance(test_case, WeightedTestCaseProtocol):
            generated_tests.append(
                ComparisonTest(
                    name=test_case.get_name(),
                    input=test_case.get_input(),
                    expected_output=test_case.get_expected_output(),
                    weight=test_case.get_weight(),
                )
            )
        elif isinstance(test_case, TestCaseProtocol):
            generated_tests.append(
                ComparisonTest(
                    name=test_case.get_name(),
                    input=test_case.get_input(),
                    expected_output=test_case.get_expected_output(),
                    weight=1.0,
                )
            )
        elif isinstance(test_case, dict):
            if "weight" in test_case:
                generated_tests.append(
                    ComparisonTest(
                        name=test_case["name"],
                        input=test_case["input"],
                        expected_output=test_case["expected_output"],
                        weight=test_case["weight"],
                    )
                )
                continue
            generated_tests.append(
                ComparisonTest(
                    name=test_case["name"],
                    input=test_case["input"],
                    expected_output=test_case["expected_output"],
                    weight=1.0,
                )
            )
        else:
            raise ValueError(
                f"`generator` passed to `make_tests_from_generator` produced a type, `{type(test_case)}`, which is not supported."
            )

    TestRegistry.extend(generated_tests)
